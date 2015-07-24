"""Tools for searchWoK; Contains backend functions for searching materials databases"""

# coding=utf-8

from __future__ import print_function

__author__ = 'eager55'

import requests
from bs4 import BeautifulSoup
import re
from urlparse import urlparse
import json

try:
    from wordcloud import WordCloud, STOPWORDS
except ImportError:
    pass


def getmaterialsproject(material, matlength=0):
    """Pings GET request from materials project for data"""
    print('Searching Materials Project for ' + material + '...')

    key = '0cVziFePTUfsawW8'

    url = 'https://www.materialsproject.org/rest/v1/materials/' + material + '/vasp?API_KEY=' + key
    respdict = []
    try:
        r = requests.get(url)
        if r.status_code == 200:
            rdict = r.json()['response']
            for n in rdict:
                if matlength > 0:
                    if len(n['unit_cell_formula']) == matlength:
                        respdict.append(n)
                else:
                    respdict.append(n)

    except requests.ConnectionError:
        pass

    return respdict


def postmaterialsproject(postdata):
    """
    Pings POST request from materials project for data
    :param postdata: Example - {'criteria':{'spacegroup.crystal_system':{'$all':['triclinic']}}}
    """
    postdata.update({'properties': ['pretty_formula',
                                    'full_formula',
                                    'total_magnetization',
                                    'is_hubbard',
                                    'formation_energy_per_atom',
                                    'e_above_hull',
                                    'band_gap',
                                    'nsites',
                                    'density',
                                    'volume',
                                    'spacegroup',
                                    'cif',
                                    'material_id',
                                    'unit_cell_formula',
                                    'elements']})

    key = '0cVziFePTUfsawW8'
    url = 'https://materialsproject.org/rest/v2/query'

    postdata = {k: json.dumps(v) for k, v in postdata.iteritems()}

    trying = True
    count = 0
    while trying and count < 10:
        try:
            r = requests.post(url,
                              headers={'X-API-KEY': key},
                              data=postdata)
        except requests.exceptions.RequestException:
            print('Trying again...' + str(count))
            count += 1
        else:
            trying = False
            count = 0

    if count >= 10:
        raise

    rdict = json.loads(r.text)['response']

    return rdict


def parsehtmlinput(querystring, keywordstring):
    """
    Reads input HTML data and returns array of parsed value strings
    :param querystring: Query string from HTML input
    :param keywordstring: Keyword string from HTML input
    :return: Tuple of array of strings
    """
    querystring = querystring.replace(' ', '')
    querylist = querystring.split(';')

    keylist = keywordstring.split(';')

    for i in range(len(keylist)):
        try:
            if keylist[i][0] == ' ':
                keylist[i] = keylist[i][1:]
            if keylist[i][-1] == ' ':
                keylist[i] = keylist[i][:-1]
        except IndexError:
            pass

    queries = []
    queryperms = []
    constraints = []

    for n in range(len(querylist)):
        marker = 0
        for m in range(n + 1, len(querylist)):
            if querylist[n] == querylist[m] or querylist[n] == '':
                marker = 1
                break
        if marker == 0:
            if querylist[n] == '':
                pass
            elif querylist[n][0] == '[':
                queryperms.append(querylist[n])
            elif querylist[n][0] == '{':
                constraints.append(eval(querylist[n].replace('[,', '[None,').replace(',]', ',None]')))
            else:
                queries.append(querylist[n])

    keywords = []
    for n in range(len(keylist)):
        marker = 0
        for m in range(n + 1, len(keylist)):
            if keylist[n] == keylist[m]:
                marker = 1
                break
        if marker == 0:
            if keylist[n] != '':
                keylist[n] = keylist[n].replace('\\\\', '\\')
                keywords.append(keylist[n])

    return queries, queryperms, constraints, keywords


def getsearchtype(searchtype):
    """Returns search code for posting requests to http://apps.webofknowledge.com/UA_GeneralSearch.do"""

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
    """Returns search relation codes for posting requests to http://apps.webofknowledge.com/UA_GeneralSearch.do"""

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
    """
    Parses search parameter string; returns data relevant to the request headers in a dictionary
    Example: searchParameters='TITLE:BaVS3 AND Topic:magnetism OR TOPIC:ferromagnetic'
    """

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
    """Searches article HTML for relevant data; returns a dictionary of this data"""

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
    """Pings universal DOI server for a given DOI number; returns URL of journal article"""

    if doi == 'N/A' or doi is None:
        return 'N/A'
    else:
        pingurl = 'http://dx.doi.org/' + doi

        pingdoi = requests.Session()

        print('Pinging DOI...')

        pingdoi.get('http://dx.doi.org')

        try:
            pingr = pingdoi.get(pingurl, timeout=5)
            return pingr.url
        except requests.exceptions.RequestException:
            print('DOI problem')
            return pingurl


def findpdf(url):
    """Searches journal article page for PDF link; returns PDF link"""

    if url == 'N/A':
        return 'N/A'
    else:
        pdflink = 'N/A'
        match = re.compile("\.pdf")

        print('Getting PDF url...')

        try:
            r = requests.get(url, timeout=5)
            page = BeautifulSoup(r.text)
        except requests.exceptions.RequestException:
            print('PDF Problem')
            return pdflink

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
    """Reads a chemical name and expands concatenation terms such as parentheses to full chemical formula"""
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
    """Checks for repeats in search criteria and expands condensed chemical names"""
    upcrit = []
    for n in range(len(searchcriteria)):
        marker = 0
        for m in range(n + 1, len(searchcriteria)):
            if searchcriteria[n]['material'] == searchcriteria[m]['material']:
                marker = 1

                for term in searchcriteria[n]['crystalsystem'].split(', '):
                    if term not in searchcriteria[m]['crystalsystem']:
                        searchcriteria[m]['crystalsystem'] += ', ' + term

                for term in searchcriteria[n]['spacegroup'].split(', '):
                    if term not in searchcriteria[m]['spacegroup']:
                        searchcriteria[m]['spacegroup'] += ', ' + term

                for term in searchcriteria[n]['bandgap'].split(', '):
                    if term not in searchcriteria[m]['bandgap']:
                        searchcriteria[m]['bandgap'] += ', ' + term

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


def removerepeats(mpresults):
    """Removes repeats in mpresults"""
    midresults = []

    for search in mpresults:
        for result in search:
            midresults.append(result)

    upresults = []
    for a in range(len(midresults)):
        marker = False
        for n in range(a + 1, len(midresults)):
            for key in midresults[a].keys():
                if midresults[a][key] != midresults[n][key]:
                    marker = True
                    break
                else:
                    marker = False
            if not marker:
                break
        if marker:
            upresults.append(midresults[a])

    return [upresults]


def smartconstraint(mpresults):
    """
    Removes uninteresting factors from mpresults
    Each 'passing' result must have a member from trmetals and anions
    If the chemical formula contains a member of electroneg, the contrmetals are valid trmetals as well
    """
    cations = {'Ba', 'Sr', 'La', 'Ca', 'K', 'Na', 'Li', 'Sc', 'Y', 'Pb', 'Bi'}

    trmetals = {'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Zr', 'Nb', 'Mo', 'Tc', 'Ru', 'Rh', 'Pd'}
    anions = {'N', 'P', 'As', 'O', 'S', 'Se', 'Te', 'F', 'Cl', 'B', 'I', 'Sb', 'Ge', 'Sr', 'C', 'B'}

    contrmetals = ['Cu', 'Ag', 'Au']
    electroneg = ['O', 'S', 'F', 'Cl', 'Br']

    newmp = []
    for search in mpresults:
        for result in search:
            composition = set(result['unit_cell_formula'].keys())
            if len(composition.intersection(anions)) != 0:
                if len(composition.intersection(trmetals)) != 0:
                    newmp.append(result)
                elif len(composition.intersection(electroneg)) != 0 and len(composition.intersection(contrmetals)):
                    newmp.append(result)

    return [newmp]


def removeconstrainedmp(mpresults, constraints):
    """Removes values in mpresults according to set constraints"""
    for constrain in constraints:
        midresults = []

        for search in mpresults:
            for result in search:
                if (constrain['bgap'][0] is not None and constrain['bgap'][0] > result['band_gap']) or \
                        (constrain['bgap'][1] is not None and constrain['bgap'][1] < result['band_gap']) or \
                        (constrain['mag'][0] is not None and constrain['mag'][0] > result['total_magnetization']) or \
                        (constrain['mag'][1] is not None and constrain['mag'][1] < result['total_magnetization']):
                    pass
                else:
                    midresults.append(result)

        mpresults = [midresults]

    return mpresults


def removeconstrainedwok(mpresults, wokresults, constraints):
    """Removes values in wokresults and mpresults according to set constraints"""
    for constrain in constraints:
        midresults = []

        for result in wokresults:
            if (constrain['pub'][0] is not None and constrain['pub'][0] > result[0]['numResults']) or \
                    (constrain['pub'][1] is not None and constrain['pub'][1] < result[0]['numResults']):
                pass
            else:
                midresults.append(result)

        wokresults = midresults

    midmp = []
    for search in mpresults:
        for result in search:
            midmp.append(result)

    newmp = []

    for j in range(len(midmp)):
        for i in range(len(wokresults)):
            if midmp[j]['material_id'] == wokresults[i][0]['material_id']:
                newmp.append(midmp[j])

    return [newmp], wokresults


def getsearchdata(searchparameters, doclimit=10):
    """
    Searches WoK and journal pages for all result data; Returns all relevant search data
    Example: searchParameters='TITLE:BaVS3 AND Topic:magnetism OR TOPIC:ferromagnetic'
    """

    spdict = getsearchparameterdict(searchparameters)

    print("Searching for '" + searchparameters + "'...\n")

    result_html = ''
    result_url = 'N/A'
    counter = 0

    pingwok = True
    while pingwok:
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
            print('WoK Timeout #' + str(counter))
            counter += 1
        except requests.exceptions.ConnectionError:
            print('WoK Connection Error #' + str(counter))
            counter += 1
        else:
            if result_html is None or result_url is None:
                print('WoK Connection Error #' + str(counter))
                counter += 1
            else:
                pingwok = False

        if counter > 10:
            print('WoK Error')
            raise

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
        m = 1
        counter = 0

        while m < (docnum + 1):
            try:
                pagenum = (m - 1) % 10 + 1
                print('Document ' + str(m) + ' loading...')

                pagepayload = {'SID': s.cookies['SID'],
                               'doc': str(m),
                               'page': str(pagenum),
                               'product': 'UA',
                               'qid': '1',
                               'search_mode': 'GeneralSearch'}

                page_r = s.post(page_url, data=pagepayload, timeout=10)
            except Exception as inst:
                print(type(inst))
                m -= 1
                counter += 1

                if counter > 10:
                    print('Connection Error')
                    raise
            else:
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

                counter = 0

            m += 1
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
    """Counts number of occurrences of keyword within the result abstracts; returns a list of integer values"""

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
    """Iterates getKeyFrequency for each keyword; returns a dictionary of frequency lists corresponding to keywords"""

    datadict = {}
    for n in keywords:
        freq = getkeyfrequency(data, n)
        datadict[n] = freq
    return datadict


def generateabstractwc(searchdata):
    """Creates and stores WordCloud images"""
    stop = {'compound', 'angstrom', 'measurements', 'respectively', 'temperature', 't', 'k', 'show', 'element', 'ions',
            'degrees', 'structure', 'observed', 'c', 'p', 'n', 'a', 'pressure', 'nm', 'atoms', 'compounds', 'x'}
    try:
        stop.add(searchdata[0]['pretty_formula'].lower())
        for m in range(len(searchdata[0]['pretty_formula'])):
            for o in range((m + 1), len(searchdata[0]['pretty_formula'])):
                stop.add(searchdata[0]['pretty_formula'][m:o].lower())
    except KeyError:
        stop.add(searchdata[0]['material'].lower())
        for m in range(len(searchdata[0]['material'])):
            for o in range((m + 1), len(searchdata[0]['material'])):
                stop.add(searchdata[0]['material'][m:o].lower())

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
