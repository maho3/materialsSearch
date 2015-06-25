__author__ = 'eager55'

#!/cygdrive/c/python27/python.exe

from gevent.pywsgi import WSGIServer
from flask import Flask, Response, request
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

@app.route("/submit", methods=['GET', 'POST'])
def mainapp(environ, start_response):
    try:
        request_body_size = int(environ.get('CONTENT_LENGTH', 0))
    except ValueError:
        request_body_size = 0

    prevload = os.listdir(os.path.join(os.getcwd(), 'materialsSearchLoadFiles'))

    if environ['REQUEST_METHOD'] == 'POST':
        request_body = environ['wsgi.input'].read(request_body_size)
        d = parse_qs(request_body)

        queries = d.get('queries', [''])[0]
        keywords = d.get('keywords', [''])[0]
        searchname = d.get('name', [''])[0]
        searchlimit = d.get('searchlimit', [''])[0]
        searchtype = d.get('searchtype', [''])[0]

        queries = escape(queries)
        keywords = escape(keywords)
        searchname = escape(searchname)
        searchlimit = escape(searchlimit)
        searchtype = escape(searchtype)

        i = 0

        if searchtype == 'mp':
            if searchname == '':
                while True:
                    i += 1
                    if 'search' + str(i) + '_mp.txt' not in prevload:
                        searchname = 'search' + str(i) + '_mp.txt'
                        break
            else:
                searchname += '_mp.txt'

            mpsearch, keys = searchWoK.handlehtmlsearch_mp(queries, keywords)

            with open(os.path.join(os.getcwd(), 'materialsSearchLoadFiles', searchname), 'wb') as outfile:
                dump([mpsearch, queries, keywords], outfile)

            response_body = searchWoK.parsempdata(mpsearch, searchname, queries, keywords)

        elif searchtype == 'wok':
            if searchname == '':
                while True:
                    i += 1
                    if 'search' + str(i) + '_wok.txt' not in prevload:
                        searchname = 'search' + str(i) + '_wok.txt'
                        break
            else:
                searchname += '_wok.txt'

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
            loadsearch = d.get('load', [''])[0]

            loadsearch = escape(loadsearch)

            with open(os.path.join(os.getcwd(), 'materialsSearchLoadFiles', loadsearch), 'rb') as f:
                loaddata = load(f)

            if loadsearch[-7:] == '_mp.txt':
                response_body = searchWoK.parsempdata(loaddata[0], '', loaddata[1], loaddata[2])
            elif loadsearch[-8:] == '_wok.txt':
                response_body = searchWoK.parsewokdata(loaddata[0], loaddata[1], loaddata[2], '', loaddata[3], loaddata[4])
            else:
                start_response('500 INTERNAL SERVER ERROR', [('Content-Type', 'text/plain')])
                return ['']
        else:
            start_response('500 INTERNAL SERVER ERROR', [('Content-Type', 'text/plain')])
            return ['']

        response_headers = [('Content-Type', 'application/json')]

    elif environ['REQUEST_METHOD'] == 'GET' and (len(environ['QUERY_STRING']) != 0):
        d = parse_qs(environ['QUERY_STRING'])

        if 'set' in d.keys():
            name = d['set'][0]

            setfull = searchWoK.readsearchcriteria(name)
            setfull = searchWoKTools.updatesc(setfull)

            setnames = []

            for n in setfull:
                setnames.append(n['material'])

            response_body = str(setnames)[2:-2]
        elif 'cif' in d.keys():
            cifpath = os.path.join(os.getcwd(), 'cifs', d['cif'][0] + '.cif')

            with open(cifpath, 'rb') as f:
                cif = f.read()

            response_body = cif
        else:
            start_response('500 INTERNAL SERVER ERROR', [('Content-Type', 'text/plain')])
            return ['']

        response_headers = [('Content-Type', 'text/html')]

    else:
        with open('materialsSearch.html', 'r') as f:
            response_body = f.read().replace('[PRELOAD]', searchWoK.parseprevload(prevload))

        response_headers = [('Content-Type', 'text/html')]

    status = '200 OK'

    response_headers.append(('Content-Length', str(len(response_body))))
    start_response(status, response_headers)

    return [response_body.encode('utf-8')]

@app.route("/update")
def updateapp(text):
    def sendupdate(s):
        ev = ServerSentEvent(s)
        yield ev.encode()

    return Response(sendupdate(text), mimetype="text/event-stream")


if __name__ == '__main__':
    WSGIServer(('', 8051), app).serve_forever()
