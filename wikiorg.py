#!/usr/bin/python

import os
import re
import gtk
import gtk.glade
from gtk import gdk
import gobject
import pango

from htmlviewer import HtmlViewer


class WikiOrgGui:
    """ Main class for this application (holds the GUI etc.) """
    def __init__ (self):
        self.currentFile = None
        self.editMode = False

        self.gladeFile = "wikiorg.glade"
        self.tree = gtk.glade.XML(self.gladeFile)
        self.tree.signal_autoconnect(self)

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
        self.displayMarkdown('index.markdown')

    def on_mainWindow_delete_event (self, widget, dummy):
        gtk.main_quit()

    def on_miQuit_activate (self, dummy):
        gtk.main_quit()

    def on_btnEdit_clicked (self, widget):
        if self.editMode:
            print "(back to view)"
            parent = self.tree.get_widget('mainScrollWin')
            child = parent.get_children()[0]
            assert(child == self.textView)
            parent.remove(child)

            self.textBuffer.disconnect(self.changeHandlerId)
            self.changeHandlerId = None
            self.tree.get_widget('btnSave').set_property('sensitive', False)
            self.tree.get_widget('miSave').set_property('sensitive', False)
            self.displayMarkdown(self.currentFile)

            parent.add(self.viewer.getWidget())
            self.tree.get_widget('btnEdit').set_property('stock_id', 'gtk-edit')
            self.editMode = False
        else:
            print "(edit)"
            parent = self.tree.get_widget('mainScrollWin')
            child = parent.get_children()[0]
            assert(child == self.viewer.getWidget())
            parent.remove(child)

            # load file content:
            f = open(self.currentFile, "r")
            text = f.read()
            f.close()
            self.textBuffer.set_text(text)
            self.changeHandlerId = self.textBuffer.connect('changed', self.on_textBuffer_changed)

            parent.add(self.textView)
            self.tree.get_widget('btnEdit').set_property('stock_id', 'gtk-ok')
            self.editMode = True

    def on_btnSave_clicked (self, widget):
        print "(save)"
        text = self.textBuffer.get_text(*self.textBuffer.get_bounds())
        f = open(self.currentFile, "w")
        f.write(text)
        f.close()
        self.tree.get_widget('btnSave').set_property('sensitive', False)
        self.tree.get_widget('miSave').set_property('sensitive', False)

    def on_miSave_activate (self, dummy):
        print "(miSave)"
        if self.editMode:
            self.on_btnSave_clicked(dummy)

    def on_btnHome_clicked (self, widget):
        print "(home)"
        if not(self.editMode): # TODO: what to do if we're in edit mode?
            self.displayMarkdown('index.markdown')

    def on_textBuffer_changed (self, textBuffer):
        self.tree.get_widget('btnSave').set_property('sensitive', True)
        self.tree.get_widget('miSave').set_property('sensitive', True)

    def linkHandler (self, url):
        """Is called when a link is clicked in HTML view"""
        print "link clicked (%s)" % url
        if url.startswith('wiki://'):
            wikiword = url[7:]
            filename = "./%s.markdown" % wikiword
            print "(internal link to '%s'; file: '%s')" % (wikiword, filename)

            if not(os.path.exists(filename)): # TODO: check for directory, and regular file, and whatnot...
                # create new file
                f = open(filename, "w")
                f.write("enter text for %s here..." % wikiword)
                f.close()
                # TODO: maybe switch to edit mode here?
            self.displayMarkdown(filename)
        else:
            os.system("xdg-open '%s' &" % url)

    # TODO: maybe use another syntax for wiki links.
    # See http://boodler.org/wiki/show/Markdown/ for an idea
    def convertWikiLinks (self, html):
        """ Converts Wiki links in the given HTML text to HTML tags """
        newHtml = re.sub("\[\[([\w ]+)\]\]",
            lambda x: "<a href='wiki://"+x.groups()[0]+"'>"+x.groups()[0]+"</a>", html)
        return newHtml

    def displayMarkdown (self, filename):
        """ Convert the given Markdown+WikiLink text to HTML, and display the HTML """
        cmd = "perl Markdown.pl < '%s'" % filename
        html = os.popen(cmd).read()
        if (html):
            html = self.convertWikiLinks(html)
            html = """<html>
<head>
<title>%s</title>
</head>
<body>
%s
</body>
</html>
""" % (filename, html)
            self.viewer.setHTML(html)
            self.currentFile = filename


if __name__ == "__main__":
    gui = WikiOrgGui()
    gtk.main()
