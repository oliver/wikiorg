#!/usr/bin/python

import gtkhtml2
import gtk


class HtmlViewer:
    def __init__ (self):
        self.view = gtkhtml2.View()
        self.document = gtkhtml2.Document()
        self.view.set_document(self.document)

    def setHTML (self, htmlcode):
        self.document.clear()
        self.document.open_stream('text/html')
        self.document.write_stream(htmlcode)
        self.document.close_stream()

    def getWidget (self):
        return self.view

    def setLinkHandler (self, handler):
        self.document.connect('link_clicked', lambda document, link: handler(link))


def linkHandler (url):
    print "clicked on link with URL '%s'" % url

if __name__ == "__main__":
    viewer = HtmlViewer()
    viewer.setLinkHandler(linkHandler)
    viewer.setHTML("<h1>HTML viewer test</h1>\n<p>This is a test text; and a <a href='abc'>link</a></p>");
    viewer.setHTML("""<h1>Markdown example content</h1>

<p>See <a href="http://daringfireball.net/projects/markdown/dingus">here</a> for a syntax cheat sheet.</p>

<p><em>italic</em>   <strong>bold</strong>
<em>italic</em>   <strong>bold</strong></p>
""")

    sw = gtk.ScrolledWindow()
    sw.add(viewer.getWidget())

    window = gtk.Window()
    window.add(sw)
    window.set_default_size(400, 400)

    window.show_all()

    gtk.main()
