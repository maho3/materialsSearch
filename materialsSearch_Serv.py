__author__ = 'eager55'

#!/cygdrive/c/python27/python.exe

from wsgiref.simple_server import make_server
from cgi import escape
from urlparse import parse_qs


def application(environ, start_response):
    if environ['REQUEST_METHOD'] == 'POST':
        try:
            request_body_size = int(environ.get('CONTENT_LENGTH', 0))
        except ValueError:
            request_body_size = 0

        request_body = environ['wsgi.input'].read(request_body_size)

        d = parse_qs(request_body)

        queries = d.get('queries', [''])[0]
        keywords = d.get('keywords', [''])[0]

        queries = escape(queries)
        keywords = escape(keywords)
        print('test')

        response_body = (queries or 'Empty') + (keywords or 'Empty')

        status = '200 OK'

        response_headers = [('Content-Type', 'text/html'),
                            ('Content-Length', str(len(response_body)))]
        start_response(status, response_headers)

        return [response_body]
    else:
        with open('materialsSearch.html', 'r') as f:
            response_body = f.read()
        status = '200 OK'
        headers = [('Content-Type', 'text/html'),
                   ('Content-Length', str(len(response_body)))]
        start_response(status, headers)
        return [response_body]

httpd = make_server('localhost', 8051, application)

httpd.serve_forever()
