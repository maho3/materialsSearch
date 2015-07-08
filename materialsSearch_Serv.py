__author__ = 'eager55'

#!/cygdrive/c/python27/python.exe

from gevent.pywsgi import WSGIServer
from gevent.queue import Queue
from flask import Flask, Response, request, Response
from cgi import escape
import searchWoK
import searchWoKTools
import os
from json import dump, dumps, load

try:
    from urlparse import parse_qs
except ImportError:
    from urllib.parse import parse_qs

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
q = Queue()

@app.route("/")
def returnhtml():
    try:
        os.makedirs('materialsSearchLoadFiles')
    except OSError:
        if not os.path.isdir('materialsSearchLoadFiles'):
            raise

    prevload = os.listdir(os.path.join(os.getcwd(), 'materialsSearchLoadFiles'))

    with open('materialsSearch.html', 'r') as f:
        rawhtml = f.read()
    with open('jquery-1.11.3.min.js', 'r') as f:
        jqueryJS = f.read()
    with open('materialsSearch.js', 'r') as f:
        msjs = f.read()

    html = rawhtml.replace('[JQUERY]', jqueryJS)
    html = html.replace('[PREVLOAD]', searchWoK.parseprevload(prevload))
    html = html.replace('[MSJS]', msjs)

    return html

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

    prevload = os.listdir(os.path.join(os.getcwd(), 'materialsSearchLoadFiles'))

    d = request.form

    searchtype = escape(d['searchtype'])

    i = 0

    if searchtype=='load' or searchtype=='sort':

        if searchtype=='load':
            loadsearch = escape(d['load'])

            with open(os.path.join(os.getcwd(), 'materialsSearchLoadFiles', loadsearch), 'rb') as f:
                loaddata = load(f)

            if loadsearch[-7:] == '_mp.txt':
                response_body = searchWoK.parsempdata(loaddata[0], '', loaddata[1], loaddata[2])
            elif loadsearch[-8:] == '_wok.txt':
                response_body = searchWoK.parsewokdata(loaddata[0], loaddata[1], loaddata[2], '', loaddata[3], loaddata[4])
        elif searchtype=='sort':
            sortname = escape(d['sortname'])
            partname = escape(d['partname'])
            sorttype = escape(d['sorttype'])
            sortdir = bool(escape(d['sortdir']) == 'true')

            with open(os.path.join(os.getcwd(), 'materialsSearchLoadFiles', sortname), 'rb') as f:
                sortdata = load(f)

            sortlist = []

            for search in sortdata[0]:
                for result in search:
                    sortlist.append(result)

            def getSort(item):
                if sorttype == "fform":
                    return item['full_formula']
                elif sorttype == "mag":
                    return item['total_magnetization']
                elif sorttype == "forme":
                    return item['formation_energy_per_atom']
                elif sorttype == "ehull":
                    return item['e_above_hull']
                elif sorttype == "gap":
                    return item['band_gap']
                elif sorttype == "nsites":
                    return item['nsites']
                elif sorttype == "den":
                    return item['density']
                elif sorttype == "vol":
                    return item['volume']
                elif sorttype == "sg":
                    return item['spacegroup']['symbol']

            sortedlist = sorted(sortlist, key=getSort)

            if sortdir:
                sortedlist = list(reversed(sortedlist))

            if sortname[-6:] == 'mp.txt':
                sorthead = 'mp'
            else:
                sorthead = 'wok'

            response_body = [searchWoK.parsempdata([sortedlist], '', sortdata[1], sortdata[2]),dumps(['','','','',''])]

            if partname != '':
                with open(os.path.join(os.getcwd(), 'materialsSearchLoadFiles', partname), 'rb') as f:
                    partdata = load(f)

                if len(sortedlist) == len(partdata[1]):
                    newWoK = []
                    newKey = []

                    for j in range(len(sortedlist)):
                        for i in range(len(partdata[1])):
                            if sortedlist[j]['material_id'] == partdata[1][i][0]['material_id']:
                                newWoK.append(partdata[1][i])
                                newKey.append(partdata[2][i])

                    if len(sortedlist) == len(newWoK):
                        response_body[1] = searchWoK.parsewokdata(partdata[0], newWoK, newKey, partname, partdata[3], partdata[4])

            response_body = dumps(response_body)



    elif searchtype=='mp' or searchtype=='wok' or searchtype=='csv':
        queries = escape(d['queries'])
        keywords = escape(d['keywords'])
        searchname = escape(d['name'])
        usecache = bool(escape(d['usecache'])=='true')

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

            mpsearch, keys = searchWoK.handlehtmlsearch_mp(queries, keywords, usecache)

            with open(os.path.join(os.getcwd(), 'materialsSearchLoadFiles', searchname), 'wb') as outfile:
                dump([mpsearch, queries, keywords], outfile)

            response_body = searchWoK.parsempdata(mpsearch, searchname, queries, keywords)

        elif searchtype=='wok' or searchtype=='csv':
            searchlimit = escape(d['searchlimit'])

            if searchtype == 'wok':
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

                keys, wokdata, keydata = searchWoK.handlehtmlsearch_wok(queries, keywords, int(searchlimit), usecache)

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



                response_body = searchWoK.handlehtmlsearch_csv(queries, keywords, int(searchlimit), searchname, usecache)


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
