import flask
from flask import Flask, send_from_directory, render_template, jsonify, url_for, request, redirect
from dirToPod import RssGenerator
from eyed3 import id3
from random import random

import shutil

import os
import subprocess


app = Flask(__name__)
SERVER_ROOT = '/var/www'
AUDIOBOOK_DIRECTORY = '/data/audiobooks'

@app.route("/")
def listAudiobooks():
    pageText = ''
    for item in sorted(os.listdir(AUDIOBOOK_DIRECTORY)):
        if not item.startswith('.'):
            pageText += '<p><a href="%s">%s</a></p>' % (url_for('getRss', path=item.replace(' ', '_')), item)
    return pageText

@app.route("/audiobook/<path:path>")
def getRss(path):
    # if not os.path.exists("%s/%s.xml" % (SERVER_ROOT, path)):
    RssGenerator("%s/%s" % (AUDIOBOOK_DIRECTORY, path.replace('_',' ')), path)
    return send_from_directory(SERVER_ROOT, "%s.xml" %  path)
    #return redirect("http://%s/%s.xml" % (request.headers['Host'], path))

@app.route("/files")
def files():
    return render_template('files.html')


@app.route("/api/joinFiles", methods=['POST'])
def joinFiles():
    newName = request.json['newName']
    fileList = request.json['fileList']
    newName = newName + '.mp3' if not newName.endswith('.mp3') else newName
    cwd = fileList[0] if os.path.isdir(fileList[0]) else os.path.dirname(fileList[0])
    filesToJoin = [aFile for aFile in fileList if aFile.endswith('.mp3')]
    map(lambda aFile: id3.tag.Tag.remove(aFile), filesToJoin)
    filesToJoin = sorted([os.path.relpath(aFile, cwd) for aFile in filesToJoin])
    args = ['/usr/bin/ffmpeg', '-i', 'concat:%s' % '|'.join(filesToJoin), '-y', '-acodec', 'copy', newName]
    runProcess(args, cwd)
    args = ['/usr/bin/vbrfix', '-always', newName, newName]
    runProcess(args, cwd)
    # cleanup crap leftover from vbrfix
    leftoverCrap = [os.path.join(cwd, crapFile) for crapFile in ['vbrfix.log', 'vbrfix.tmp'] if os.path.isfile(os.path.join(cwd, crapFile))]
    map(lambda crap: os.remove(crap), leftoverCrap)
    return ""

@app.route("/api/hierarchy", methods=['GET'])
def getHierarchy():
    def addEntries(entryList, icon):
        for entry in entryList:
            data.append({ 'id' : os.path.join(root, entry), 'text' : entry, 'parent' : root, 'icon' : icon})

    data = [{'id' : AUDIOBOOK_DIRECTORY, 'text' : 'audiobooks', 'parent' : '#'}]
    for root,dirs,files in os.walk('/data/audiobooks'):
        files = [f for f in files if not f[0] == '.']
        dirs[:] = [d for d in dirs if not d[0] == '.']
        addEntries(dirs, 'jstree-folder')
        addEntries(files, 'jstree-file')
    
    return jsonify(data=data)

@app.route('/api/delete', methods=['POST'])
def delete():
    if request.json.has_key('nodeList'):
        nodeList = request.json['nodeList']
    else:
        nodeList = []
        nodeList.append(request.json['node'])

    for node in nodeList:
        if os.path.isdir(node):
            shutil.rmtree(node)
        elif os.path.isfile(node):
            os.remove(node)
        #If its not a file or directory, we either already deleted it by deleting the directory, or we've got a symlink, which we ideally wanna keep around
    return ''

@app.route('/api/rename', methods=['POST'])
def rename():
    oldPath = request.json['oldPath']
    newPath = os.path.join(os.path.dirname(oldPath), request.json['newNode'])
    if os.path.exists(newPath):
        raise OSError('Path already exists!')
    os.rename(oldPath, newPath)
    return ''

@app.route('/api/move', methods=['POST'])
def move():
    oldPath = request.json['oldPath']
    dropTo = request.json['dropTo']

    if os.path.isdir(dropTo):
        newPath = dropTo
    elif os.path.isfile(dropTo):
        newPath = os.path.dirname(dropTo)
    else:
        app.logger.debug('Trying to drop on file that is neither directory or file...what is it?')
    newPath = newPath + os.path.sep + os.path.basename(oldPath)

    if os.path.exists(newPath):
        raise OSError('Path already exists!')
    shutil.move(oldPath, newPath)
    return ''

@app.route('/api/reencode', methods=['POST'])
def reencode():
    fileList = request.json['fileList']
    for aFile in fileList:
        if aFile.endswith('.mp3'):
            fileDir = os.path.dirname(aFile)
            filename = os.path.basename(aFile)
            oldDir = os.path.join(fileDir, 'old')
            if not os.path.isdir(oldDir):
                os.mkdir(oldDir)
            os.rename(aFile, os.path.join(oldDir, filename))
            args = ['/usr/bin/ffmpeg', '-i', os.path.join(oldDir, filename), '-ab', '96k', aFile]
            runProcess(args, fileDir)
    return ''

def runProcess(args, cwd):
    app.logger.debug(args)
    stdout = '/tmp/stdout%s' % str(random()).split('.')[1]
    with open(stdout, 'w') as out:
        pobj = subprocess.Popen(args, stdout=out, stderr=subprocess.STDOUT, cwd=cwd)
        ret = pobj.wait()
    with open(stdout, 'r') as out:
        app.logger.debug(out.read())
    os.remove(stdout)
    
    

if __name__ == "__main__":
    app.run('0.0.0.0', port=81, debug=True)


