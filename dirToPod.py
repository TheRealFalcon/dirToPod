#!/usr/bin/python2

import sys
import os
import unicodedata
import datetime
import re

WEB_ROOT = '/var/www'
SERVER = os.environ.get('DOMAIN', 'http://example.com')

class RssGenerator(object):
    def __init__(self, directory, title):
        rssFilePath = WEB_ROOT + os.sep + title + ".xml"
        symlinkPath = WEB_ROOT + os.sep + title
        if os.path.exists(rssFilePath) or os.path.exists(symlinkPath):
            print(rssFilePath + " or " + symlinkPath + " already exist! Get rid of them if you want to continue")
            exit(1)
        self.rssFile = open(rssFilePath, 'w')
        self.createHeader(title, directory)
        publishTime = datetime.datetime.now()
        oneHour = datetime.timedelta(hours=1)
        for root,dirs,files in os.walk(directory):
            files.sort(reverse=True)
            for ttcFile in files:
                if ttcFile.endswith('.mp3'):
                    self.createItem(root, title, ttcFile, publishTime)
                    publishTime -= oneHour
        self.createFooter()
        self.rssFile.close()

        os.symlink(os.path.abspath(directory), symlinkPath)
        print("Point podcatcher to %s/%s.xml" % (SERVER,title))

    def put(self, text):
        # Force unicode characters to look Ascii
        if not isinstance(text, unicode):
            text = unicode(text, errors='replace')
        self.rssFile.write(unicodedata.normalize('NFKD', text).encode('ascii', 'ignore'))


    def createHeader(self, title, rootDir):
        self.put('<rss xmlns:atom="http://www.w3.org/2005/Atom" version="2.0">\n')
        self.put('\t<channel>\n')
        self.put('\t\t<title>%s</title>\n' % title)
        # If an image exists in the dir, grab one at random since we have no way of distinguishing between images.
        imageList = [image for image in os.listdir(rootDir) if re.search('.*\.(jpg|jpeg|png|gif|bmp)', image)]
        if imageList:
            self.put('\t\t<image><url>%s/%s/%s</url></image>\n' % (SERVER, title, imageList[0].replace(' ', '%20')))


    def createItem(self, rootDir, title, filename, publishTime):
        self.put('\t\t<item>\n')
        self.put('\t\t\t<title>%s</title>\n' % filename)
        link = SERVER + '/' + title + '/' + filename
        self.put('\t\t\t<link>%s</link>\n' % link.replace(' ', '%20'))
        self.put('\t\t\t<enclosure url="%s" />\n' % link.replace(' ', '%20'))
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
    gen = RssGenerator(directory, title)


