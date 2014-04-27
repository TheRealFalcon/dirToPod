from flask import Flask, send_from_directory
from dirToPod import RssGenerator
import os

app = Flask(__name__)
SERVER_ROOT = '/var/www'
AUDIOBOOK_DIRECTORY = '/data/audiobooks'

@app.route("/")
def listAudiobooks():
	pageText = ''
	for item in sorted(os.listdir(AUDIOBOOK_DIRECTORY)):
		if not item.startswith('.'):
			pageText += '<p><a href="audiobook/%s">%s</a></p>' % (item.replace(' ', '_'), item)
	return pageText

@app.route("/audiobook/<path:path>")
def getRss(path):
	if not os.path.exists("%s/%s.xml" % (SERVER_ROOT, path)):
		RssGenerator("%s/%s" % (AUDIOBOOK_DIRECTORY, path.replace('_',' ')), path)
	return send_from_directory(SERVER_ROOT, "%s.xml" %  path)

if __name__ == "__main__":
	app.run('0.0.0.0', port=80, debug=True)

