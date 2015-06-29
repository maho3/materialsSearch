__author__ = 'eager55'

#!/cygdrive/c/python27/python.exe

from gevent.pywsgi import WSGIServer
from gevent.queue import Queue
from flask import Flask, Response, request, Response
from cgi import escape
from urlparse import parse_qs
import searchWoK
import searchWoKTools
import os
from json import dump, load

class ServerSentEvent(object):

    def __init__(self, data):
        self.data = data
        self.event = None
        self.id = None
        self.desc_map = {
            self.data : "data",
            self.event : "event",
            self.id : "id"
        }

    def encode(self):
        if not self.data:
            return ""
        lines = ["%s: %s" % (v, k)
                 for k, v in self.desc_map.iteritems() if k]

        return "%s\n\n" % "\n".join(lines)

app = Flask(__name__)
app.debug = True
q = Queue()

@app.route("/")
def returnhtml():
    prevload = os.listdir(os.path.join(os.getcwd(), 'materialsSearchLoadFiles'))
    with open('materialsSearch.html', 'r') as f:
            return f.read().replace('[PRELOAD]', searchWoK.parseprevload(prevload))

@app.route("/grabpresets")
def grabpresets():
    name = request.args.get('set')

    setfull = searchWoK.readsearchcriteria(name)
    setfull = searchWoKTools.updatesc(setfull)

    setnames = []

    for n in setfull:
        setnames.append(n['material'])

    return str(setnames)[2:-2]

@app.route("/getcif")
def getcif():
    cifname = request.args.get('cif')

    cifpath = os.path.join(os.getcwd(), 'cifs', cifname + '.cif')

    with open(cifpath, 'rb') as f:
        cif = f.read()

    return cif

@app.route("/submit", methods=['POST'])
def mainapp():
    print ('hello')

    prevload = os.listdir(os.path.join(os.getcwd(), 'materialsSearchLoadFiles'))

    d = request.form

    queries = d['queries']
    keywords = d['keywords']
    searchname = d['name']
    searchlimit = d['searchlimit']
    searchtype = d['searchtype']

    queries = escape(queries)
    keywords = escape(keywords)
    searchname = escape(searchname)
    searchlimit = escape(searchlimit)
    searchtype = escape(searchtype)

    i = 0

    if searchtype == 'mp':
        if searchname == '':
            q.put('Generating search name...')
            while True:
                i += 1
                if 'search' + str(i) + '_mp.txt' not in prevload:
                    searchname = 'search' + str(i) + '_mp.txt'
                    break
        else:
            searchname += '_mp.txt'

        q.put('Search name is: ' + searchname)

        mpsearch, keys = searchWoK.handlehtmlsearch_mp(queries, keywords)

        with open(os.path.join(os.getcwd(), 'materialsSearchLoadFiles', searchname), 'wb') as outfile:
            dump([mpsearch, queries, keywords], outfile)

        response_body = searchWoK.parsempdata(mpsearch, searchname, queries, keywords)

    elif searchtype == 'wok':
        if searchname == '':
            q.put('Generating search name...')
            while True:
                i += 1
                if 'search' + str(i) + '_wok.txt' not in prevload:
                    searchname = 'search' + str(i) + '_wok.txt'
                    break
        else:
            searchname += '_wok.txt'

        q.put('Search name is: ' + searchname)

        keys, wokdata, keydata = searchWoK.handlehtmlsearch_wok(queries, keywords, int(searchlimit))

        with open(os.path.join(os.getcwd(), 'materialsSearchLoadFiles', searchname), 'wb') as outfile:
            dump([keys, wokdata, keydata, queries, keywords], outfile)

        response_body = searchWoK.parsewokdata(keys, wokdata, keydata, searchname, queries, keywords)
    elif searchtype == 'csv':
        prevcsv = next(os.walk(os.path.join(os.getcwd(), 'materialsSearchCSV-WC')))

        if searchname == '':
            while True:
                i += 1
                if 'search' + str(i) not in prevcsv:
                    searchname = 'search' + str(i)
                    break

        if not os.path.exists(os.path.join(os.getcwd(), 'materialsSearchCSV-WC', searchname)):
            os.makedirs(os.path.join(os.getcwd(), 'materialsSearchCSV-WC', searchname))

        response_body = searchWoK.handlehtmlsearch_csv(queries, keywords, int(searchlimit), searchname)
    elif searchtype == 'load':
        loadsearch = d['load']

        loadsearch = escape(loadsearch)

        with open(os.path.join(os.getcwd(), 'materialsSearchLoadFiles', loadsearch), 'rb') as f:
            loaddata = load(f)

        if loadsearch[-7:] == '_mp.txt':
            response_body = searchWoK.parsempdata(loaddata[0], '', loaddata[1], loaddata[2])
        elif loadsearch[-8:] == '_wok.txt':
            response_body = searchWoK.parsewokdata(loaddata[0], loaddata[1], loaddata[2], '', loaddata[3], loaddata[4])


    response = Response()
    response.headers.add('Content-Type', 'application/json')
    response.headers.add('Content-Length', str(len(response_body)))

    return response_body.encode('utf-8')

@app.route("/update")
def updateapp():
    def sendupdate():
        try:
            while True:
                s = q.get()
                ev = ServerSentEvent(s + '&#13;&#10;')
                yield ev.encode()
        except GeneratorExit:
            pass

    return Response(sendupdate(), mimetype="text/event-stream")


if __name__ == '__main__':
    WSGIServer(('', 8051), app).serve_forever()
