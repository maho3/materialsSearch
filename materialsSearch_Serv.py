__author__ = 'eager55'

#!/cygdrive/c/python27/python.exe

from wsgiref.simple_server import make_server
from cgi import escape
from urlparse import parse_qs
import searchWoK
import os

def application(environ, start_response):
    try:
        request_body_size = int(environ.get('CONTENT_LENGTH', 0))
    except ValueError:
        request_body_size = 0

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

        if searchtype == 'mp':
            mpsearch, keyss = searchWoK.handlehtmlsearch_mp(queries, keywords)

            response_body = searchWoK.parsempdata(mpsearch)
        elif searchtype == 'wok':
            woksearch = searchWoK.handlehtmlsearch_wok(queries, keywords, int(searchlimit))

            response_body = woksearch

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
        with open('materialsSearch.html', 'r') as f:
            response_body = f.read()

    status = '200 OK'

    response_headers = [('Content-Type', 'text/html'),
                        ('Content-Length', str(len(response_body)))]
    start_response(status, response_headers)

    return [response_body.encode('utf-8')]

httpd = make_server('localhost', 8051, application)

httpd.serve_forever()
