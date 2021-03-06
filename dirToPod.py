#!/usr/bin/python2

import sys
import os
import unicodedata
import datetime
import re
import shutil

WEB_ROOT = '/var/www/books'
SERVER = os.environ.get('DOMAIN', 'http://www.example.com')

class RssGenerator(object):
    @property
    def link(self):
        return self.title

    def __init__(self, server, directory, title):
        self.server = server
        rssFilePath = "{}{}{}.xml".format(WEB_ROOT, os.sep, title)
        symlinkPath = "{}{}{}".format(WEB_ROOT, os.sep, title)
        if os.path.exists(rssFilePath):
            os.remove(rssFilePath)
        if os.path.exists(symlinkPath):
            os.remove(symlinkPath)
        self.rssFile = open(rssFilePath, 'w')
        self.createHeader(title, directory)

        publishTime = datetime.datetime.now()
        oneHour = datetime.timedelta(hours=1)
        # for root,dirs,files in os.walk(directory):
        files = [aFile for aFile in os.listdir(directory) if not os.path.isdir(aFile)]
        files.sort(reverse=True)
        for oldFile in files:
            newFile = oldFile.replace(' ', '_') #My podcatcher won't accept the %20 encoded URLs
            shutil.move(os.path.join(directory, oldFile), os.path.join(directory, newFile))
            if newFile.endswith('.mp3'):
                self.createItem(directory, title, newFile, publishTime)
                publishTime -= oneHour
        self.createFooter()
        self.rssFile.close()

        os.symlink(os.path.abspath(directory), symlinkPath)
        self.title = "%s.xml" % title

    def put(self, text):
        # Force unicode characters to look Ascii
        if not isinstance(text, unicode):
            text = unicode(text, errors='replace')
        self.rssFile.write(unicodedata.normalize('NFKD', text).encode('ascii', 'ignore'))


    def createHeader(self, title, rootDir):
        self.put('<rss xmlns:atom="http://www.w3.org/2005/Atom" version="2.0" xmlns:media="http://search.yahoo.com/mrss/">\n')
        self.put('\t<channel>\n')
        self.put('\t\t<title>%s</title>\n' % title)
        # If an image exists in the dir, grab one at random since we have no way of distinguishing between images.
        imageList = [image for image in os.listdir(rootDir) if re.search('.*\.(jpg|jpeg|png|gif|bmp)', image)]
        if imageList:
            self.put('\t\t<image><url>%s/%s/%s</url></image>\n' % (self.server, title, imageList[0].replace(' ', '_')))


    def createItem(self, rootDir, title, filename, publishTime):
        self.put('\t\t<item>\n')
        self.put('\t\t\t<title>%s</title>\n' % filename)
        link = '%s/%s.xml' % (self.server, title)
        self.put('\t\t\t<link>%s</link>\n' % link)
        enclosure = '%s/%s/%s' % (self.server, title, filename)
        self.put('\t\t\t<enclosure url="%s" />\n' % enclosure)
        self.put('\t\t\t<media:content url="%s" />\n' % enclosure)
        self.put('\t\t\t<lastBuildDate>' + publishTime.strftime('%a, %d %b %Y %H:%M:%S -0600') + '</lastBuildDate>\n')
        self.put('\t\t\t<pubDate>' + publishTime.strftime('%a, %d %b %Y %H:%M:%S -0600') + '</pubDate>\n')
        self.put('\t\t</item>\n')

    def createFooter(self):
        self.put('\t</channel>\n')
        self.put('</rss>\n')



if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage:")
        print("dirToPod.py <dir> <name>")
        print(" dir: Directory containing podcast files")
        print(" name: Name of podcast (no spaces!)")
        print
        print("Script must have permissions to web root: " + WEB_ROOT)
        exit(1)
    directory = sys.argv[1]
    title = sys.argv[2]
    if ' ' in title:
            print("No spaces in title!")
            exit(1)
    if not os.path.isdir(directory):
        print("Must specify directory")
        exit(1)
    gen = RssGenerator(SERVER, directory, title)
    print("Point podcatcher to %s/%s" % (SERVER,gen.link))


