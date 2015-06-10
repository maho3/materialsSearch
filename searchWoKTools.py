__author__ = 'eager55'

import requests
from bs4 import BeautifulSoup
import re
from urlparse import urlparse
from wordcloud import WordCloud, STOPWORDS


def pingmaterialsproject(material):
    key = '0cVziFePTUfsawW8'

    url = 'https://www.materialsproject.org/rest/v1/materials/'+material+'/vasp?API_KEY='+key

    r = requests.get(url)

    rdict = eval(r.text, {'true': 'true', 'false': 'false', 'null': 'null'})['response'][0]

    return rdict

def getsearchtype(searchtype):
    # Returns search code for posting requests to http://apps.webofknowledge.com/UA_GeneralSearch.do

    if searchtype == 'title':
        search = 'TI'
    elif searchtype == 'topic':
        search = 'TS'
    elif searchtype == 'author':
        search = 'AU'
    elif searchtype == 'author identifiers':
        search = 'AI'
    elif searchtype == 'editor':
        search = 'ED'
    elif searchtype == 'group author':
        search = 'GP'
    elif searchtype == 'publication name':
        search = 'SO'
    elif searchtype == 'doi':
        search = 'DO'
    elif searchtype == 'year published':
        search = 'PY'
    elif searchtype == 'address':
        search = 'AD'
    else:
        raise Exception('Error searchType invalid')

    return search


def getreltype(reltype):
    # Returns search parameter relation codes for posting requests to http://apps.webofknowledge.com/UA_GeneralSearch.do

    if reltype == 'and':
        rel = 'AND'
    elif reltype == 'or':
        rel = 'OR'
    elif reltype == 'not':
        rel = 'NOT'
    else:
        raise Exception('Error relType invalid')

    return rel


def getsearchparameterdict(searchparameters):
    #  Parses search parameter string; returns data relevant to the request headers in a dictionary
    #  Example: searchParameters='TITLE:BaVS3 AND Topic:magnetism OR TOPIC:ferromagnetic'
    plist = searchparameters.lower()
    plist = plist.split()

    if len(plist) % 2 == 0:
        raise Exception('SearchParameters has even arguments')

    spdict = {}

    for n in range(0, (len(plist) + 1) / 2):
        parameter = plist[2 * n].replace(':', ' ').split()
        parameterdict = {'value(hidInput' + str(n + 1) + ')': '',
                         'value(select' + str(n + 1) + ')': getsearchtype(parameter[0]),
                         'value(input' + str(n + 1) + ')': parameter[1]}

        spdict.update(parameterdict)

    for n in range(1, (len(plist) + 1) / 2):
        parameterrel = plist[2 * n - 1]
        reldict = {'value(bool_' + str(n) + '_' + str(n + 1) + ')': getreltype(parameterrel)}

        spdict.update(reldict)

    return spdict


def getdatainfo(pagedata):
    #  Searches article HTML for relevant data; returns a dictionary of this data

    authorblock = pagedata.find('div', 'block-record-info').p
    pubblock = pagedata.find('div', 'block-record-info block-record-info-source')

    paperauthors = []

    paperauthorlist = authorblock.find_all('a', {'title': 'Find more records by this author'})

    for o in paperauthorlist:
        paperauthors.append(o.get_text())

    try:
        pubtitle = pubblock.find('p', 'sourceTitle').next_element.next_element.string
    except AttributeError:
        print('Error pubTitle')
        pubtitle = 'N/A'
    try:
        pubvol = pubblock.find(text='Volume:').next_element.next_element.string
        if pubvol == u'\n':
            pubvol = pubblock.find(text='Volume:').next_element.string
            print('\\n trouble')
    except AttributeError:
        print('Error pubVol')
        pubvol = 'N/A'
    try:
        pubissue = pubblock.find(text='Issue:').next_element.next_element.string
        if pubissue == u'\n':
            pubissue = pubblock.find(text='Issue:').next_element.string
            print('\\n trouble')
    except AttributeError:
        print('Error pubIssue')
        pubissue = 'N/A'
    try:
        pubpages = pubblock.find(text='Pages:').next_element.next_element.string
        if pubpages == u'\n':
            pubpages = pubblock.find(text='Pages:').next_element.string
            print('\\n trouble')
    except AttributeError:
        print('Error pubPages')
        pubpages = 'N/A'
    try:
        pubdoi = pubblock.find(text='DOI:').next_element.next_element.string
        if pubdoi == u'\n':
            pubdoi = pubblock.find(text='DOI:').next_element.string
            print('\\n trouble')
    except AttributeError:
        print('Error pubDOI')
        pubdoi = 'N/A'
    try:
        pubdate = pubblock.find(text='Published:').next_element.next_element.string
        if pubdate == u'\n':
            pubdate = pubblock.find(text='Published:').next_element.string
            print('\\n trouble')
    except AttributeError:
        print('Error pubDate')
        pubdate = 'N/A'

    try:
        pubissn = pagedata.find(text='ISSN:').next_element.next_element.string
        if pubissn == u'\n':
            pubissn = pagedata.find(text='ISSN:').next_element.string
            print('\\n trouble')
    except AttributeError:
        print('Error pubISSN')
        pubissn = 'N/A'

    try:
        abstract = pagedata.find(text='Abstract').next_element.next_element.text
        if abstract == u'\n':
            abstract = pagedata.find(text='Abstract').next_element.string
            print('\\n trouble')
    except AttributeError:
        print('Error Abstract')
        abstract = 'N/A'

    infodict = dict(authors=paperauthors,
                    pub=pubtitle,
                    volume=pubvol,
                    issue=pubissue,
                    pages=pubpages,
                    DOI=pubdoi,
                    pubDate=pubdate,
                    ISSN=pubissn,
                    abstract=abstract)
    return infodict


def getdoilink(doi):
    # Pings universal DOI server for a given DOI number; returns URL of journal article
    if doi == 'N/A':
        return 'N/A'
    else:
        pingurl = 'http://dx.doi.org/' + doi

        pingdoi = requests.Session()

        print('Pinging DOI...')

        pingdoi.get('http://dx.doi.org')

        try:
            pingr = pingdoi.get(pingurl, timeout=5)
            return pingr.url
        except Exception:
            print('DOI problem')
            return pingurl


def findpdf(url):
    # Searches journal article page for PDF link; returns PDF link
    if url == 'N/A':
        return 'N/A'
    else:
        pdflink = 'N/A'
        match = re.compile('\.pdf')

        print('Getting PDF url...')

        r = requests.get(url, timeout=5)
        page = BeautifulSoup(r.text)

        for link in page.findAll('a'):
            try:
                href = link['href']
                if re.search(match, href):
                    pdflink = href
            except KeyError:
                pass

        if (pdflink != 'N/A') and (pdflink[:7] != 'http://'):
            parsed_uri = urlparse(url)
            domain = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)

            pdflink = domain + pdflink
        elif pdflink == 'N/A':
            print('PDF link not found')

        return pdflink


def expandname(name):
    op = re.search("\(", name)
    cl = re.search("\)", name)

    exp = int(name[cl.start() + 1])
    inside = name[op.start() + 1:cl.start()]

    result = name[:op.start()]

    for n in range(len(inside)):
        if re.match('[A-Z]', inside[n]) or re.match('[a-z]', inside[n]):
            result += inside[n]
            if (n < (len(inside) - 1) and (re.match('[A-Z]', inside[n + 1]))) or (n == len(inside) - 1):
                result += str(exp)
        elif re.match('\d', inside[n]):
            result += str(int(inside[n]) * exp)

    return result


def updatesc(searchcriteria):
    upcrit = []
    for n in range(len(searchcriteria)):
        marker = 0
        for m in range(n + 1, len(searchcriteria)):
            if searchcriteria[n]['material'] == searchcriteria[m]['material']:
                marker = 1
                searchcriteria[m]['crystalsystem'] += ', ' + searchcriteria[n]['crystalsystem']
                searchcriteria[m]['spacegroup'] += ', ' + searchcriteria[n]['spacegroup']
                searchcriteria[m]['bandgap'] += ', ' + searchcriteria[n]['bandgap']
                break
        if marker == 0:
            upcrit.append(searchcriteria[n])

    for n in range(len(upcrit)):
        if re.search("\)", upcrit[n]['material']):
            upcrit[n]['numQueries'] = 2
            upcrit[n]['material'] += ', ' + expandname(upcrit[n]['material'])

        else:
            upcrit[n]['numQueries'] = 1

    return upcrit


def getsearchdata(searchparameters, doclimit=10):
    #  General Search of searchParameters
    #  Searches WoK and journal pages for all result data; Returns all relevant search data
    #  Example: searchParameters='TITLE:BaVS3 AND Topic:magnetism OR TOPIC:ferromagnetic'

    spdict = getsearchparameterdict(searchparameters)

    print("Searching for '" + searchparameters + "'...\n")

    try:
        s = requests.Session()
        s.get(r'http://www.webofknowledge.com', timeout=10)

        gs_url = 'http://apps.webofknowledge.com/UA_GeneralSearch.do'

        payload = {'SID': s.cookies['SID'],
                   'SinceLastVisit_DATE=': '',
                   'SinceLastVisit_UTC=': '',
                   'action': 'search',
                   'endYear': '2015',
                   'exp_notice': 'Search Error: Patent search term could be found in more than one family (unique '
                                 'patent number required for Expand option) ',
                   'fieldCount': '1',
                   'formUpdated': 'true',
                   'input_invalid_notice': 'Search Error: Please enter a search term',
                   'input_invalid_notice_limits': '<br/>Note: Fields displayed in scrolling boxes must be combined '
                                                  'with at least one other search field.',
                   'limitStatus': 'collapsed',
                   'max_field_count': '25',
                   'max_field_notice': 'Notice: You cannot add another field.',
                   'period': 'Range Selection',
                   'product': 'UA',
                   'range': 'ALL',
                   'rs_sort_by': 'TC.D;PY.D;AU.A;SO.A;VL.D;PG.A',
                   'sa_params': "UA||" + s.cookies['SID'] + "|http://apps.webofknowledge.com|'",
                   'search_mode': 'GeneralSearch',
                   'ssStatus': 'display:none',
                   'ss_lemmatization': 'On',
                   'ss_numDefaultGeneralSearchFields': '1',
                   'ss_query_language': 'auto', 'ss_showsuggestions': 'ON',
                   'ss_spellchecking': 'Suggest',
                   'startYear': '1864',
                   'update_back2search_link_param': 'yes',
                   'x': '12',
                   'y': '36'}

        payload.update(spdict)

        print('Getting results page...')

        r = s.post(gs_url, data=payload, timeout=10)

        result_html = r.text
        result_url = r.url
    except requests.exceptions.Timeout:
        print('WoK Timeout Error')
        result_html = ''
        result_url = 'N/A'

    resultsoup = BeautifulSoup(result_html)

    try:
        truedocnum = int(resultsoup.find('span', id='trueFinalResultCount').get_text())

        print(str(truedocnum) + ' results found')

        if truedocnum > doclimit:
            docnum = doclimit
        else:
            docnum = truedocnum

        print('Searching first ' + str(docnum) + ' results...\n')

        page_url = 'http://apps.webofknowledge.com/full_record.do'
        resultdata = []
        prevtitle = ''
        i = 0

        for m in range(1, docnum + 1):
            pagenum = (m - 1) % 10 + 1
            print('Document ' + str(m) + ' loading...')

            try:
                pagepayload = {'SID': s.cookies['SID'],
                               'doc': str(m),
                               'page': str(pagenum),
                               'product': 'UA',
                               'qid': '1',
                               'search_mode': 'GeneralSearch'}
                page_r = s.post(page_url, data=pagepayload, timeout=5)

                page_html = page_r.text

                pagesoup = BeautifulSoup(page_html)

                pagedata = pagesoup.find('div', 'l-content')

                papertitle = pagedata.find('div', 'title').get_text()[1:-1]

                if papertitle == prevtitle:
                    print('End of Results')
                    break
                else:
                    i += 1
                    prevtitle = papertitle

                    infodict = getdatainfo(pagedata)
                    infodict.update({'title': papertitle})

                    infodict.update({'DOIlink': getdoilink(infodict['DOI'])})

                    infodict.update({'pdflink': findpdf(infodict['DOIlink'])})

                    resultdata.append(infodict)
            except Exception as inst:
                print(type(inst))

        searchdata = ({'numResults': truedocnum, 'searchURL': result_url}, resultdata)

        print('\n\nEnd Search\n' + str(i) + ' results found\n')
        return searchdata
    except AttributeError:
        print('NO RESULTS')
        infodict = dict(authors='N/A',
                        pub='N/A',
                        volume='N/A',
                        issue='N/A',
                        pages='N/A',
                        DOI='N/A',
                        pubDate='N/A',
                        ISSN='N/A',
                        abstract='N/A',
                        title='N/A',
                        DOIlink='N/A',
                        pdflink='N/A')
        resultdata = [infodict]

        searchdata = ({'numResults': 0, 'searchURL': result_url}, resultdata)
        return searchdata


def getkeyfrequency(data, keyword):
    #  Counts number of occurrences of keyword within the result abstracts; returns a list of integer values
    findresult = []

    for n in range(len(data[1])):
        try:
            abstract = data[1][n]['abstract']
            find = re.findall(keyword, abstract)
            findresult.append(len(find))
        except KeyError:
            findresult.append(0)

    return findresult


def getkeylist(data, keywords):
    # Iterates getKeyFrequency for each keyword; returns a dictionary of frequency lists corresponding to each keyword

    datadict = []
    for n in keywords:
        freq = getkeyfrequency(data, n)
        datadict.append((n, freq))

    return datadict


def generateabstractwc(searchdata):
    stop = {'compound', 'angstrom', 'measurements', 'respectively', 'temperature', 't', 'k', 'show', 'element', 'ions',
            'degrees', 'structure', 'observed', 'c', 'p', 'n', 'a', 'pressure', 'nm', 'atoms', 'compounds', 'x'}

    for n in searchdata[0]['material'].split(', '):
        stop.add(n.lower())
        for m in range(len(n)):
            for o in range((m + 1), len(n)):
                stop.add(n[m:o].lower())

    stop.update(STOPWORDS)

    wc = WordCloud(background_color='white',
                   width=600,
                   height=600,
                   stopwords=stop)
    absstring = ''

    for result in searchdata[1]:
        if result['abstract'] != 'N/A':
            absstring += result['abstract']

    if absstring == '':
        absstring = 'None'

    wc.generate(absstring)

    return wc
