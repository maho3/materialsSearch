"""Initializes and runs localhost:8051 server for searching materials"""

# coding=utf-8
# /cygdrive/c/python27/python.exe

__author__ = 'eager55'

from gevent.pywsgi import WSGIServer
from gevent.queue import Queue
from flask import Flask, request, Response
from cgi import escape
import searchWoK
import searchWoKTools
import os
from json import dump, dumps, load
from re import sub

try:
    from urlparse import parse_qs
except ImportError:
    from urllib.parse import parse_qs


class ServerSentEvent(object):
    """Initializes server variables and provides encoding procedure for sending data"""

    def __init__(self, data):
        self.data = data
        self.event = None
        self.id = None
        self.desc_map = {
            self.data: "data",
            self.event: "event",
            self.id: "id"
        }

    def encode(self):
        """Encodes sending data"""
        if not self.data:
            return ""
        lines = ["%s: %s" % (v, k)
                 for k, v in self.desc_map.iteritems() if k]

        return "%s\n\n" % "\n".join(lines)


app = Flask(__name__)
q = Queue()


@app.route("/")
def returnhtml():
    """Returns html for initial GET load; Loads [JQuery/MS] javascript into the HTML string"""

    try:
        os.makedirs('materialsSearchLoadFiles')
    except OSError:
        if not os.path.isdir('materialsSearchLoadFiles'):
            raise
    try:
        os.makedirs('rawICSD')
    except OSError:
        if not os.path.isdir('rawICSD'):
            raise

    prevload = os.listdir(os.path.join(os.getcwd(), 'materialsSearchLoadFiles'))
    rawicsd = os.listdir(os.path.join(os.getcwd(), 'rawICSD'))

    with open('materialsSearch.html') as f:
        rawhtml = f.read()
    with open('jquery-1.11.3.min.js') as f:
        jqueryjs = f.read()
    with open('materialsSearch.js') as f:
        msjs = f.read()

    html = rawhtml.replace('[JQUERY]', jqueryjs)
    html = html.replace('[PREVLOAD]', searchWoK.parseprevload(prevload))
    html = html.replace('[MSJS]', msjs)
    html = html.replace('[rawICSD]', searchWoK.parseprevload(rawicsd))

    return html


@app.route("/grabpresets")
def grabpresets():
    """Returns loadstring of preset material names"""
    name = request.args.get('set')

    setfull = searchWoK.readsearchcriteria(name)
    setfull = searchWoKTools.updatesc(setfull)

    setnames = []

    for n in setfull:
        setnames.append(n['material'])

    return str(setnames)[2:-2]

@app.route("/grabICSD")
def grabicsd():
    """Returns loadstring of preset material names"""
    name = request.args.get('set')

    return searchWoK.readrawicsd(name[:-4])

@app.route("/getcif")
def getcif():
    """Returns CIF string"""
    cifname = request.args.get('cif')

    cifpath = os.path.join(os.getcwd(), 'cifs', cifname + '.cif')

    with open(cifpath, 'rb') as f:
        cif = f.read()

    return cif


@app.route("/submit", methods=['POST'])
def mainapp():
    """Accepts input data from HTML and returns Material Data according to defined searchtype parameters"""

    prevload = os.listdir(os.path.join(os.getcwd(), 'materialsSearchLoadFiles'))

    d = request.form

    searchtype = escape(d['searchtype'])

    i = 0
    response_body = ''

    if searchtype == 'load' or searchtype == 'sort':

        if searchtype == 'load':
            loadsearch = escape(d['load'])

            print('Generating load of ' + loadsearch)

            with open(os.path.join(os.getcwd(), 'materialsSearchLoadFiles', loadsearch), 'rb') as f:
                loaddata = load(f)

            if loadsearch[-7:] == '_mp.txt':
                response_body = dumps(searchWoK.parsempdata(loaddata[0], loadsearch, loaddata[1], loaddata[2]))
            elif loadsearch[-8:] == '_wok.txt':
                response_body = dumps(
                    searchWoK.parsewokdata(loaddata[0], loaddata[1], loaddata[2], loaddata[3], loadsearch, loaddata[4],
                                           loaddata[5]))
        elif searchtype == 'sort':
            try:
                sortname = escape(d['sortname'])
                partname = escape(d['partname'])
                sorttype = escape(d['sorttype'])
                sortdir = bool(escape(d['sortdir']) == 'true')

                with open(os.path.join(os.getcwd(), 'materialsSearchLoadFiles', sortname), 'rb') as f:
                    sortdata = load(f)

                sortlist = []

                if sortname[-6:] == 'mp.txt':
                    sortmain = sortdata[0]
                else:
                    sortmain = sortdata[1]

                for search in sortmain:
                    for result in search:
                        sortlist.append(result)

                def getsort(item):
                    """Identifies proper dict key for sorting
                    :param item:
                    """
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
                    elif sorttype[:4] == "elem":
                        try:
                            return sub("(-?\d+)|(\+1)", ' ', item['full_formula']).split()[int(sorttype[4:]) - 1] + \
                                item['full_formula']
                        except IndexError:
                            print('IndexError_Element')
                            return 'zz' + item['full_formula']

                sortedlist = sorted(sortlist, key=getsort)

                if sortdir:
                    sortedlist = list(reversed(sortedlist))

                response_body = [dumps(searchWoK.parsempdata([sortedlist], '', sortdata[1], sortdata[2]),
                                       dumps(['', '', '', '', ''])), '']

                if partname != '':

                    if len(sortedlist) == len(sortdata[2]):
                        newwok = []
                        newkey = []

                        for j in range(len(sortedlist)):
                            for i in range(len(sortdata[2])):
                                if sortedlist[j]['material_id'] == sortdata[2][i][0]['material_id']:
                                    newwok.append(sortdata[2][i])
                                    newkey.append(sortdata[3][i])

                        if len(sortedlist) == len(newwok):
                            response_body[1] = dumps(
                                searchWoK.parsewokdata(sortdata[0], [sortedlist], newwok, newkey, sortdata[3],
                                                       sortdata[4], sortdata[5]))

                response_body = dumps(response_body)
            except Exception as inst:
                print(inst)
                print(type(inst))

    elif searchtype == 'mp' or searchtype == 'wok' or searchtype == 'csv':
        queries = escape(d['queries'])
        keywords = escape(d['keywords'])
        searchname = escape(d['name'])
        usecache = bool(escape(d['usecache']) == 'true')
        smartconstrain = bool(escape(d['smartconstrain']) == 'true')

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

            mpsearch, keys, constraints = searchWoK.handlehtmlsearch_mp(queries, keywords, usecache, smartconstrain)

            with open(os.path.join(os.getcwd(), 'materialsSearchLoadFiles', searchname), 'wb') as outfile:
                dump([mpsearch, queries, keywords], outfile)

            response_body = dumps(searchWoK.parsempdata(mpsearch, searchname, queries, keywords))

        elif searchtype == 'wok' or searchtype == 'csv':
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

                keys, mpdata, wokdata, keydata = searchWoK.handlehtmlsearch_wok(queries, keywords, int(searchlimit),
                                                                                usecache, smartconstrain)

                with open(os.path.join(os.getcwd(), 'materialsSearchLoadFiles', searchname), 'wb') as outfile:
                    dump([keys, mpdata, wokdata, keydata, queries, keywords], outfile)

                response_body = dumps(
                    searchWoK.parsewokdata(keys, mpdata, wokdata, keydata, searchname, queries, keywords))

            elif searchtype == 'csv':
                prevcsv = next(os.walk(os.path.join(os.getcwd(), 'materialsSearchCSV-WC')))

                if searchname == '':
                    while True:
                        i += 1
                        if 'search' + str(i) not in prevcsv:
                            searchname = 'search' + str(i)
                            break

                response_body = searchWoK.handlehtmlsearch_csv(queries, keywords, int(searchlimit), searchname,
                                                               usecache, smartconstrain)
            else:
                print('Invalid searchtype')
                raise
        else:
            print('Invalid searchtype')
            raise
    else:
        print('Invalid searchtype')
        raise

    response = Response()
    response.headers.add('Content-Type', 'application/json')
    response.headers.add('Content-Length', str(len(response_body)))

    return response_body.encode()


@app.route("/update")
def updateapp():
    """Sends server update messages in queue to HTML"""

    def sendupdate():
        """Manages server update message encoding"""
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
