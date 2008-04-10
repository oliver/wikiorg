#!/usr/bin/python

import os
import re
import gtk
from htmlviewer import HtmlViewer

def linkHandler (url):
    print "link clicked (%s)" % url
    if url.startswith('http://'):
        os.system("xdg-open '%s' &" % url)
    elif url.startswith('wiki://'):
        wikiword = url[7:]
        filename = "./%s.markdown" % wikiword
        print "(internal link to '%s'; file: '%s')" % (wikiword, filename)
        displayMarkdown(viewer, filename)

# TODO: maybe use another syntax for wiki links.
# See http://boodler.org/wiki/show/Markdown/ for an idea
def convertWikiLinks (html):
    newHtml = re.sub("\[\[([\w ]+)\]\]",
        lambda x: "<a href='wiki://"+x.groups()[0]+"'>"+x.groups()[0]+"</a>", html)
    return newHtml

def displayMarkdown (viewer, filename):
    cmd = "perl Markdown.pl < '%s'" % filename
    html = os.popen(cmd).read()
    if (html):
        html = convertWikiLinks(html)
        viewer.setHTML(html)

if __name__ == "__main__":
    viewer = HtmlViewer()
    viewer.setLinkHandler(linkHandler)
    #viewer.setHTML("<h1>HTML viewer test</h1>\n<p>This is a test text; and a <a href='abc'>link</a></p>");

    sw = gtk.ScrolledWindow()
    sw.add(viewer.getWidget())

    window = gtk.Window()
    window.add(sw)
    window.set_default_size(400, 400)

    window.show_all()

    displayMarkdown(viewer, "example.markdown")

    gtk.main()
