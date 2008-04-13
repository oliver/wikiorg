#!/usr/bin/python

import os
import re
import gtk
import gtk.glade
from gtk import gdk
import gobject
import pango

from htmlviewer import HtmlViewer


class LinkHistory:
    """
    Stores information about visited pages (for back/forward buttons).
    Note that many functions only work after at least one page has been added (with pushPageName).
    """
    def __init__ (self, gui):
        """
        "gui" is the WikiOrgGui object that displays the history buttons.
        """
        self.gui = gui
        self.visited = [] # list of pages (contains back, forward, and current pages)
        self.currentPageIndex = None # index of current page (in self.visited)

    def pushPageName (self, page):
        """ Add given page to top of history """
        if self.currentPageIndex != None and page == self.getCurrentPage():
            print "(history: page '%s' is current page - not adding)" % page
            return

        # remove all "forward" pages:
        if self.currentPageIndex != None:
            self.visited = self.visited[:self.currentPageIndex + 1]

        self.visited.append(page)
        self.currentPageIndex = len(self.visited) - 1

        print "(added page '%s')" % page
        self.notifyGui()

    def notifyGui (self):
        """ Inform GUI object that it has to update its history display. """
        self.gui.setHistoryButtonState(self.canGoBack(), self.canGoForward())

    def canGoBack (self, count = 1):
        """ Returns true if history can go back 'count' pages. """
        assert(count > 0)
        return self.currentPageIndex > (count - 1)

    def canGoForward (self, count = 1):
        """ Returns true if history can go forward 'count' pages. """
        return self.currentPageIndex < (len(self.visited) - count)

    def getCurrentPage (self):
        """ Returns name of current page. """
        assert(self.currentPageIndex != None)
        return self.visited[self.currentPageIndex]

    def getBackPages (self):
        """ Returns a list of 'past' pages (order: newest first). """
        if self.currentPageIndex == None:
            return []
        else:
            pages = self.visited[:self.currentPageIndex]
            pages.reverse()
            return pages

    def getForwardPages (self):
        """ Returns a list of 'future' pages (order: oldest first). """
        if self.currentPageIndex == None:
            return []
        else:
            return self.visited[self.currentPageIndex + 1:]

    def goBack (self, count = 1):
        """ Go back 'count' pages. """
        if self.canGoBack(count):
            self.currentPageIndex = self.currentPageIndex - count
            self.notifyGui()
            self.gui.displayMarkdown( self.getCurrentPage() )
        else:
            print "warning: tried to go back in history but there are not enough older pages"

    def goForward (self, count = 1):
        """ Go forward 'count' pages. """
        if self.canGoForward(count):
            self.currentPageIndex = self.currentPageIndex + count
            self.notifyGui()
            self.gui.displayMarkdown( self.getCurrentPage() )
        else:
            print "warning: tried to go forward in history but there are not enough newer pages"


class FileStorageBackend:
    """ Handles the actual storage of wiki pages to files. """
    def __init__ (self):
        self.directory = "." # the directory where files are saved

    def pageExists (self, pagename):
        filename = self.pageToFile(pagename)
        # TODO: check for directory, and regular file, and whatnot...
        return os.path.exists(filename)

    def createNewPage (self, pagename):
        filename = self.pageToFile(pagename)
        f = open(filename, "w")
        f.write("enter text for %s here..." % pagename)
        f.close()

    def getPageContent (self, pagename):
        filename = self.pageToFile(pagename)
        f = open(filename, "r")
        text = f.read()
        f.close()
        return text

    def savePageContent (self, pagename, text):
        filename = self.pageToFile(pagename)
        f = open(filename, "w")
        f.write(text)
        f.close()

    def pageToFile (self, wikiword):
        """ Translates a page name (wiki word) into a file name. """
        return "%s/%s.markdown" % (self.directory, wikiword)


class WikiOrgGui:
    """ Main class for this application (holds the GUI etc.) """
    def __init__ (self):
        self.currentPage = None
        self.editMode = False
        self.textChanged = False

        self.gladeFile = "wikiorg.glade"
        self.tree = gtk.glade.XML(self.gladeFile)
        self.tree.signal_autoconnect(self)

        # set up storage backend:
        self.storage = FileStorageBackend()

        # set up link history:
        self.linkHistory = LinkHistory(self)

        # set up menus for back/forward buttons:
        btnGoBack = self.tree.get_widget("btnGoBack")
        self.backMenu = gtk.Menu()
        btnGoBack.set_menu(self.backMenu)

        btnGoForward = self.tree.get_widget("btnGoForward")
        self.forwardMenu = gtk.Menu()
        btnGoForward.set_menu(self.forwardMenu)

        # set up HTML viewer widget:
        self.viewer = HtmlViewer()
        self.viewer.setLinkHandler(self.linkHandler)
        self.viewer.getWidget().show()

        # remove the TextView from ScrolledWindow but keep it for later:
        viewerParent = self.tree.get_widget('mainScrollWin')
        self.textView = viewerParent.get_children()[0]
        viewerParent.remove(self.textView)
        # instead, add the HTML viewer widget:
        viewerParent.add(self.viewer.getWidget())

        # set up text view:
        fontName = "Monospace"
        pangoFont = pango.FontDescription(fontName)
        self.textView.modify_font(pangoFont)

        # add TextBuffer for text view:
        self.textBuffer = gtk.TextBuffer(None)
        self.textView.set_buffer(self.textBuffer)

        # display start page:
        self.displayMarkdown('index')

    def on_mainWindow_delete_event (self, widget, dummy):
        gtk.main_quit()

    def on_miQuit_activate (self, dummy):
        gtk.main_quit()

    def on_btnEdit_clicked (self, widget):
        if self.editMode:
            if self.textChanged:
                print "(unsaved changes left)"
                parentWin = self.tree.get_widget("mainWindow")
                saveDialog = gtk.MessageDialog(parentWin, gtk.DIALOG_MODAL,
                    gtk.MESSAGE_WARNING, gtk.BUTTONS_YES_NO,
                    "There are unsaved changes.")
                saveDialog.format_secondary_text("Do you want to save?")
                saveDialog.set_default_response(gtk.RESPONSE_YES)

                result = saveDialog.run()
                saveDialog.destroy()
                if result == gtk.RESPONSE_YES:
                    print "(do save)"
                    self.on_btnSave_clicked(None)
                else:
                    print "(don't save)"

            print "(back to view)"
            parent = self.tree.get_widget('mainScrollWin')
            child = parent.get_children()[0]
            assert(child == self.textView)
            parent.remove(child)

            self.textBuffer.disconnect(self.changeHandlerId)
            self.changeHandlerId = None
            self.tree.get_widget('btnSave').set_property('sensitive', False)
            self.tree.get_widget('miSave').set_property('sensitive', False)
            self.displayMarkdown(self.currentPage)

            parent.add(self.viewer.getWidget())
            self.tree.get_widget('btnEdit').set_property('stock_id', 'gtk-edit')
            self.editMode = False
        else:
            print "(edit)"
            parent = self.tree.get_widget('mainScrollWin')
            child = parent.get_children()[0]
            assert(child == self.viewer.getWidget())
            parent.remove(child)

            # load page content:
            text = self.storage.getPageContent(self.currentPage)
            self.textBuffer.set_text(text)
            self.textChanged = False
            self.changeHandlerId = self.textBuffer.connect('changed', self.on_textBuffer_changed)

            parent.add(self.textView)
            self.tree.get_widget('btnEdit').set_property('stock_id', 'gtk-ok')
            self.editMode = True

    def on_btnSave_clicked (self, widget):
        print "(save)"
        text = self.textBuffer.get_text(*self.textBuffer.get_bounds())
        self.storage.savePageContent(self.currentPage, text)
        self.textChanged = False
        self.tree.get_widget('btnSave').set_property('sensitive', False)
        self.tree.get_widget('miSave').set_property('sensitive', False)

    def on_miSave_activate (self, dummy):
        print "(miSave)"
        if self.editMode:
            self.on_btnSave_clicked(dummy)

    def on_btnHome_clicked (self, widget):
        print "(home)"
        if not(self.editMode): # TODO: what to do if we're in edit mode?
            self.displayMarkdown('index')

    def on_textBuffer_changed (self, textBuffer):
        self.textChanged = True
        self.tree.get_widget('btnSave').set_property('sensitive', True)
        self.tree.get_widget('miSave').set_property('sensitive', True)

    def on_btnGoBack_clicked (self, widget):
        print "(go back)"
        self.linkHistory.goBack()

    def on_btnGoForward_clicked (self, widget):
        print "(go forward)"
        self.linkHistory.goForward()

    def on_backMenuItem_activate (self, item, position):
        print "(back menu item at pos. %d)" % position
        self.linkHistory.goBack(position)

    def on_forwardMenuItem_activate (self, item, position):
        print "(forward menu item at pos. %d)" % position
        self.linkHistory.goForward(position)

    def setHistoryButtonState (self, backEnabled, forwardEnabled):
        self.tree.get_widget('btnGoBack').set_property('sensitive', backEnabled)
        self.tree.get_widget('btnGoForward').set_property('sensitive', forwardEnabled)

        # delete all entries from back button menu:
        for mi in self.backMenu.get_children():
            self.backMenu.remove(mi)

        # add current entries to back button menu:
        itemPos = 1
        for page in self.linkHistory.getBackPages():
            mi = gtk.MenuItem(page)
            mi.connect('activate', self.on_backMenuItem_activate, itemPos)
            mi.show()
            self.backMenu.append(mi)
            itemPos = itemPos + 1

        # delete all entries from forward button menu:
        for mi in self.forwardMenu.get_children():
            self.forwardMenu.remove(mi)

        # add current entries to forward button menu:
        itemPos = 1
        for page in self.linkHistory.getForwardPages():
            mi = gtk.MenuItem(page)
            mi.connect('activate', self.on_forwardMenuItem_activate, itemPos)
            mi.show()
            self.forwardMenu.append(mi)
            itemPos = itemPos + 1

    def linkHandler (self, url):
        """Is called when a link is clicked in HTML view"""
        print "link clicked (%s)" % url
        if url.startswith('wiki://'):
            wikiword = url[7:]
            print "(internal link to '%s')" % wikiword

            # create new page if necessary:
            if not(self.storage.pageExists(wikiword)):
                self.storage.createNewPage(wikiword)
                # TODO: maybe switch to edit mode here?

            self.displayMarkdown(wikiword)
        else:
            os.system("xdg-open '%s' &" % url)

    def wikiwordToHtmlLink (self, wikiword):
        """ Returns an HTML link tag for the given wikiword. """
        if self.storage.pageExists(wikiword):
            return "<a class='wikilink' href='wiki://%s'>%s</a>" % (wikiword, wikiword)
        else:
            return "<a class='wikilinkbroken' href='wiki://%s'>%s</a>" % (wikiword, wikiword)

    # TODO: maybe use another syntax for wiki links.
    # See http://boodler.org/wiki/show/Markdown/ for an idea
    def convertWikiLinks (self, html):
        """ Converts Wiki links in the given HTML text to HTML tags """
        newHtml = re.sub("\[\[([\w ]+)\]\]",
            lambda x: self.wikiwordToHtmlLink(x.groups()[0]), html)
        return newHtml

    def displayMarkdown (self, wikiword):
        """ Convert the Markdown+WikiLink text to HTML, and display the HTML """
        filename = self.storage.pageToFile(wikiword)
        cmd = "perl Markdown.pl < '%s'" % filename
        html = os.popen(cmd).read()
        if (html):
            html = self.convertWikiLinks(html)
            html = """<html>
<head>
<title>%s</title>
<style type="text/css">
a { color:#6666FF; font-style: italic; }
a:after { content:" (ext)"; }
.wikilink { color:#0000FF; font-style: normal; }
.wikilink:after { content:""; }
.wikilinkbroken { color:#FF0000; font-style: normal; }
.wikilinkbroken:after { content:""; }
</style>

</head>
<body>
%s
</body>
</html>
""" % (wikiword, html)
            self.viewer.setHTML(html)
            self.currentPage = wikiword
            self.tree.get_widget("lblStatusBar").set_label("<i>%s</i>" % wikiword)
            self.linkHistory.pushPageName(wikiword)

if __name__ == "__main__":
    gui = WikiOrgGui()
    gtk.main()
