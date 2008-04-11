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

        self.tree.signal_autoconnect(self)

        self.viewer = HtmlViewer()
        self.viewer.setLinkHandler(self.linkHandler)
        self.viewer.setHTML("<h1>HTML viewer test</h1>\n<p>This is a test text; and a <a href='http://google.de'>link</a></p>");
        self.viewer.getWidget().show()

        viewerParent = self.tree.get_widget('mainScrollWin')
        viewerParent.add(self.viewer.getWidget())

        self.displayMarkdown('example.markdown')

    def on_mainWindow_delete_event (self, widget, dummy):
        gtk.main_quit()

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
    #viewer = HtmlViewer()
    #viewer.setLinkHandler(linkHandler)
    ##viewer.setHTML("<h1>HTML viewer test</h1>\n<p>This is a test text; and a <a href='abc'>link</a></p>");

    #sw = gtk.ScrolledWindow()
    #sw.add(viewer.getWidget())

    #window = gtk.Window()
    #window.add(sw)
    #window.set_default_size(400, 400)

    #window.show_all()

    #displayMarkdown(viewer, "example.markdown")

    gui = WikiOrgGui()

    gtk.main()
