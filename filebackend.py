
#
# Simple file-based storage for WikiOrg
#

import os

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
