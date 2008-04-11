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
        self.gladeFile = "wikiorg.glade"
        self.tree = gtk.glade.XML(self.gladeFile)
        self.editMode = False

        self.tree.signal_autoconnect(self)

        self.viewer = HtmlViewer()
        self.viewer.setLinkHandler(self.linkHandler)
        self.viewer.setHTML("<h1>HTML viewer test</h1>\n<p>This is a test text; and a <a href='http://google.de'>link</a></p>");
        self.viewer.getWidget().show()

        viewerParent = self.tree.get_widget('mainScrollWin')

        # remove the TextView from ScrolledWindow but keep it for later:
        self.textView = viewerParent.get_children()[0]
        viewerParent.remove(self.textView)

        viewerParent.add(self.viewer.getWidget())

        self.displayMarkdown('index.markdown')

    def on_mainWindow_delete_event (self, widget, dummy):
        gtk.main_quit()

    def on_btnEdit_clicked (self, widget):
        if self.editMode:
            print "(back to view)"
            parent = self.tree.get_widget('mainScrollWin')
            child = parent.get_children()[0]
            assert(child == self.textView)
            parent.remove(child)
            parent.add(self.viewer.getWidget())
            self.tree.get_widget('btnEdit').set_property('stock_id', 'gtk-edit')
            self.editMode = False
        else:
            print "(edit)"
            parent = self.tree.get_widget('mainScrollWin')
            child = parent.get_children()[0]
            assert(child == self.viewer.getWidget())
            parent.remove(child)
            parent.add(self.textView)
            self.tree.get_widget('btnEdit').set_property('stock_id', 'gtk-ok')
            self.editMode = True

    def linkHandler (self, url):
        print "link clicked (%s)" % url
        if url.startswith('wiki://'):
            wikiword = url[7:]
            filename = "./%s.markdown" % wikiword
            print "(internal link to '%s'; file: '%s')" % (wikiword, filename)
            self.displayMarkdown(filename)
        else:
            os.system("xdg-open '%s' &" % url)

    # TODO: maybe use another syntax for wiki links.
    # See http://boodler.org/wiki/show/Markdown/ for an idea
    def convertWikiLinks (self, html):
        newHtml = re.sub("\[\[([\w ]+)\]\]",
            lambda x: "<a href='wiki://"+x.groups()[0]+"'>"+x.groups()[0]+"</a>", html)
        return newHtml

    def displayMarkdown (self, filename):
        cmd = "perl Markdown.pl < '%s'" % filename
        html = os.popen(cmd).read()
        if (html):
            html = self.convertWikiLinks(html)
            self.viewer.setHTML(html)


if __name__ == "__main__":
    gui = WikiOrgGui()
    gtk.main()
