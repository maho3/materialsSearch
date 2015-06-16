__author__ = 'eager55'

import csv
import json
import os
import searchWoKTools

mainKeywords = ['superconduct', 'conduct', 'resist', 'metal', 'insulator', 'doped', 'ferromagnetism',
                'antiferromagnetism', 'ferrimagnetism', 'magnet', '\d K', 'DFT', 'DMFT',
                'charge density wave', 'band structure', 'susceptibility', 'NMR',
                'nuclear magnetic resonance', 'neutron', 'mu-SR', 'x-ray']


def readsearchcriteria(filename):
    with open(os.path.join(os.getcwd(), 'search_criteria', filename + '.csv'), 'rb') as f:
        reader = csv.reader(f)
        i = 0
        rowlist = []
        for row in reader:
            if i != 0:
                rowdict = {'material': row[0],
                           'crystalsystem': row[7],
                           'spacegroup': row[8],
                           'bandgap': row[9]}
                rowlist.append(rowdict)
            i += 1

        return rowlist


def parsempdata(data):
    resultstring = ''
    for search in data:
        for result in search:
            cifpath = os.path.join(os.getcwd(), 'cifs', result['pretty_formula'] + '.cif')

            with open(cifpath, 'wb') as f:
                f.write(result['cif'])

            resultstring += '<tr class="results">'
            resultstring += '<td class="results">' + result['pretty_formula'] + '</td>'
            resultstring += '<td class="results">' + result['full_formula'] + '</td>'
            resultstring += '<td class="results">' + str(result['total_magnetization']) + '</td>'
            resultstring += '<td class="results">' + str(result['formation_energy_per_atom']) + '</td>'
            resultstring += '<td class="results">' + str(result['e_above_hull']) + '</td>'
            resultstring += '<td class="results">' + str(result['band_gap']) + '</td>'
            resultstring += '<td class="results">' + str(result['nsites']) + '</td>'
            resultstring += '<td class="results">' + str(result['density']) + '</td>'
            resultstring += '<td class="results">' + str(result['volume']) + '</td>'
            resultstring += '<td class="results">' + result['spacegroup']['symbol'] + '; ' + str(
                result['spacegroup']['number']) + '; ' + result['spacegroup']['point_group'] + '; ' + \
                result['spacegroup']['crystal_system'] + '; ' + str(result['spacegroup']['hall']) + '</td>'
            resultstring += '<td class="results"><button onclick="window.open(\'/?cif=' + result[
                'pretty_formula'] + '\')">Get CIF</button></td>'
            resultstring += '</tr>'
    return resultstring

def parsewokkeys(keywords):
    resultstring = '<td class="resultTitle">Material</td><td class="resultTitle">Publications</td>'

    for key in keywords:
        resultstring += '<td class="resultTitle">' + key + '</td>'

    return resultstring

def parsewokdata(wokdata, keydata):
    resultstring = ''
    for i in range(len(wokdata)):
        resultstring += '<tr>'
        resultstring += '<td class="results">' + wokdata[i][0]['pretty_formula'] + '</td>'
        resultstring += '<td class="results">' + str(wokdata[i][0]['numResults']) + '</td>'

        for key in keydata[i].keys():
            numpapers = 0
            for paper in keydata[i][key]:
                if paper != 0:
                    numpapers += 1

            resultstring += '<td class="results">'
            if numpapers != 0:
                resultstring += str(numpapers)
            resultstring += '</td>'

        resultstring += '</tr>'

    return resultstring

def handlehtmlsearch_mp(querystring, keywordstring):
    queries, permqueries, keywords = searchWoKTools.parsehtmlinput(querystring, keywordstring)

    with open('mpRecord.txt', 'rb') as record:
        rec = record.read()
        try:
            rlist = json.loads(rec)
        except ValueError:
            rlist = {}

    if 'queries' not in rlist.keys() or 'permqueries' not in rlist.keys():
        rlist = {'queries': {}, 'permqueries': {}}

    mpresults = []

    for query in queries:
        if query in rlist['queries'].keys():
            mpresults.append(rlist['queries'][query])
        else:
            result = searchWoKTools.pingmaterialsproject(query)
            rlist['queries'][query] = result
            mpresults.append(result)

    for permquery in permqueries:
        pquer = permquery[0] + '-' + permquery[1] + '-' + permquery[2]
        if pquer in rlist['permqueries'].keys():
            mpresults.append(rlist['permqueries'][pquer])
        else:
            result = searchWoKTools.pingmaterialsproject(pquer)
            rlist['permqueries'][pquer] = result
            mpresults.append(result)

    with open('mpRecord.txt', 'wb') as record:
        json.dump(rlist, record)

    return mpresults, keywords


def viewdata(data):
    #  Prints out readable information of the output of getSearchData

    print('_' * 50)
    print('Number of Results: ' + str(data[0]['numResults']))
    print('\nSearchURL: ' + data[0]['searchURL'])
    print('_' * 50)

    i = 1
    for m in data[1]:
        print(str(i) + '.  ')
        for n in m:
            print(str(n) + ': ' + str(m[n]))
            i += 1
    print('\n')


def handlehtmlsearch_wok(querystring, keywordstring, searchlimit):
    mpsearch, keywords = handlehtmlsearch_mp(querystring, keywordstring)

    with open('wokRecord.txt', 'rb') as record:
        rec = record.read()
        try:
            wlist = json.loads(rec)
        except ValueError:
            wlist = {}

    wokresults = []
    for search in mpsearch:
        for n in search:
            searchparam = 'topic:'+n['pretty_formula'] + ' or topic:' + n['full_formula']

            if searchparam in wlist.keys():
                wokresults.append(wlist[searchparam])
            else:
                try:
                    searchdata = searchWoKTools.getsearchdata(searchparam, searchlimit)
                except Exception:
                    searchdata = ({}, [])
                searchdata[0].update(n)
                wlist[searchparam] = searchdata
                wokresults.append(searchdata)

    with open('wokRecord.txt', 'wb') as record:
        json.dump(wlist, record)

    keyresults = []
    for search in wokresults:
        keyresults.append(searchWoKTools.getkeylist(search, keywords))

    return json.dumps([parsewokkeys(keywords), parsewokdata(wokresults, keyresults)])


def savequerydata(searchcriteria, filename='', searchlimit=10):
    # Iterates over queries and gathers search data for each query; saves .txt file of all data with JSON encoding
    # If saveQueryData reaches an exception and escapes early, data gathered until that point is returned

    searchcriteria = searchWoKTools.updatesc(searchcriteria)

    i = 0
    querydata = []
    try:
        with open(os.path.join(os.getcwd(), 'searchWoKResults', filename + 'queryData.txt'), 'wb') as output:
            for criterion in searchcriteria:
                i += 1
                query = criterion['material']
                print('Searching for ' + query + '... (' + str(i) + '/' + str(len(searchcriteria)) + ')')

                searchparam = ''
                for n in range(len(query.split(', '))):
                    searchparam += 'topic:' + query.split(', ')[n]
                    if (criterion['numQueries'] > 1) and (n < (len(query.split(', ')) - 1)):
                        searchparam += ' or '
                searchdata = searchWoKTools.getsearchdata(searchparam, searchlimit)
                searchdata[0].update(criterion)
                querydata.append(searchdata)

            json.dump(querydata, output)
    except Exception as inst:
        print(type(inst))
        return querydata


def generate_csv(filename='', datafile='queryData.txt', keywords=mainKeywords):
    # Runs getKeyList for given keywords and sorts data accordingly
    # Generates two CSV files constructed from the data within fileName+queryData.txt and the frequency lists
    # fileName+MaterialsKeySearchCondensed.csv condenses the frequency list into a form viewable in one page
    # fileName+MaterialsKeySearchFull.csv expands data and allows user to click direct links to journal web pages

    fulltitle = os.path.join(os.getcwd(), 'searchWoKResults', filename + 'MaterialsKeySearchFull.csv')
    contitle = os.path.join(os.getcwd(), 'searchWoKResults', filename + 'MaterialsKeySearchCondensed.csv')
    datatitle = os.path.join(os.getcwd(), 'searchWoKResults', filename + datafile)

    with open(fulltitle, 'wb') as csvFull, open(contitle, 'wb') as csvCon, open(datatitle, 'rb') as data:
        fwriter = csv.writer(csvFull, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        cwriter = csv.writer(csvCon, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        querydata = json.load(data)

        conheader = ['Material', 'Publications', 'Crystal System', 'Space Group', 'Calculated Band Gap']
        for n in keywords:
            conheader.append(n)
        cwriter.writerow(conheader)

        linenum = 0

        print('GETTING KEYWORD LIST:')
        print('Searching for ' + str(keywords) + '\n')

        for searchData in querydata:
            print('Searching through ' + searchData[0]['material'] + ' data')

            keylist = searchWoKTools.getkeylist(searchData, keywords)

            print('Generating clouds')
            wc = searchWoKTools.generateabstractwc(searchData)
            imgpath = os.path.join(os.getcwd(), 'searchWoKResults', filename, searchData[0]['material'] + '.png')
            wc.to_file(imgpath)

            print('Writing CSV')
            fwriter.writerow([searchData[0]['material'],
                              str(searchData[0]['numResults']) + ' publications',
                              searchData[0]['crystalsystem'],
                              searchData[0]['spacegroup'] + '  spacegroup',
                              searchData[0]['bandgap'] + '  band gap',
                              searchData[0]['searchURL'],
                              '=HYPERLINK("' + imgpath + '","Word Cloud")'])
            linenum += 1

            conline = [
                '=HYPERLINK("[' + fulltitle + ']' + filename + 'MaterialsKeySearchFull' + '!A' + str(linenum) + '","' +
                searchData[0]['material'] + '")',

                str(searchData[0]['numResults']),
                searchData[0]['crystalsystem'],
                searchData[0]['spacegroup'],
                searchData[0]['bandgap']]

            fwriter.writerow([])
            linenum += 1

            for key in keylist:
                keyrow = []
                conkeynum = 0
                for n in range(len(key[1])):
                    result = key[1][n]
                    if result != 0:
                        cellstring = '=HYPERLINK("' + searchData[1][n]['DOIlink'] + '","' + key[0] + '(' + str(
                            result) + ')")'
                        keyrow.append(cellstring)
                        conkeynum += 1
                if keyrow:
                    fwriter.writerow(keyrow)
                    linenum += 1
                if conkeynum != 0:
                    constring = '=HYPERLINK("[' + fulltitle + ']' + filename + 'MaterialsKeySearchFull' + '!A' + str(
                        linenum) + '","' + str(conkeynum) + '")'
                    conline.append(constring)
                else:
                    conline.append('')

            cwriter.writerow(conline)

            fwriter.writerow([])
            fwriter.writerow([])
            linenum += 2

        return


def automate_search(filename, searchlimit):
    sc = readsearchcriteria(filename)

    data = savequerydata(sc, filename, searchlimit)

    if data is not None:
        print('saveQueryData Error')
        return data

    generate_csv(filename)
