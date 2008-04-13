
import os
import sys
import re

class GitStorageBackend:
    """ Handles the actual storage of wiki pages to files which reside in a Git repo. """
    def __init__ (self):
        self.directory = "/home/oliver/kdevel/wikiorg/store1/" # the directory where files are saved
        os.chdir(self.directory)
        cmd = "git status"
        pipe = os.popen(cmd)
        result = pipe.read()
        exitCode = pipe.close()
        if exitCode == None:
            exitCode = 0
        else:
            exitCode = os.WEXITSTATUS(exitCode)

        print "exitCode: %d" % exitCode

        if exitCode > 1:
            print "error opening Git repo ('git status' returned with code %d)" % (exitCode)
            sys.exit(1)

    def pageExists (self, pagename):
        filename = self.pageToFile(pagename)
        # TODO: check for directory, and regular file, and whatnot...
        return os.path.exists(filename)

    #def createNewPage (self, pagename):
        #filename = self.pageToFile(pagename)
        #f = open(filename, "w")
        #f.write("enter text for %s here..." % pagename)
        #f.close()

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

        # commit changes to Git
        shortFilename = re.sub("^%s" % self.directory, "", filename)
        cmd = "git commit --message='WikiOrg-commit' -- '%s'" % shortFilename
        print "(cmd: %s)" % cmd
        pipe = os.popen(cmd)
        result = pipe.read()
        exitCode = pipe.close()
        if exitCode != None:
            exitCode = os.WEXITSTATUS(exitCode)
            print "git-commit exitCode: %d" % exitCode
        else:
            print "successfully commited"

    def pageToFile (self, wikiword):
        """ Translates a page name (wiki word) into a file name. """
        return os.path.normpath( "%s/%s.markdown" % (self.directory, wikiword) )

