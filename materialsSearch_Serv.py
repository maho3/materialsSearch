__author__ = 'eager55'

#!/cygdrive/c/python27/python.exe

from wsgiref.simple_server import make_server
from cgi import escape
from urlparse import parse_qs
import searchWoK
import os
from json import dump, load

def application(environ, start_response):
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

    elif environ['REQUEST_METHOD'] == 'GET' and (len(environ['QUERY_STRING']) != 0):
        d = parse_qs(environ['QUERY_STRING'])

        if 'set' in d.keys():
            name = d['set'][0]

            setfull = searchWoK.readsearchcriteria(name)
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

    else:
        with open('materialsSearch.html', 'r') as f:
            response_body = f.read().replace('[PRELOAD]', searchWoK.parseprevload(prevload))

    status = '200 OK'

    response_headers = [('Content-Type', 'text/html'),
                        ('Content-Length', str(len(response_body)))]
    start_response(status, response_headers)

    return [response_body.encode('utf-8')]

httpd = make_server('localhost', 8051, application)

httpd.serve_forever()
