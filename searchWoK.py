
from __future__ import print_function

__author__ = 'eager55'

import csv
import json
import os
import searchWoKTools
import itertools

try:
    import wordcloud
    wcexists = True
except ImportError:
    wcexists = False

mainKeywords = ['superconduct', 'conduct', 'resist', 'metal', 'insulator', 'doped', 'ferromagnetism',
                'antiferromagnetism', 'ferrimagnetism', 'magnet', '\d K', 'DFT', 'DMFT',
                'charge density wave', 'band structure', 'susceptibility', 'NMR',
                'nuclear magnetic resonance', 'neutron', 'mu-SR', 'x-ray']

def readrawicsd(filename):
    with open(os.path.join(os.getcwd(), 'rawICSD', filename + '.csv'), 'rb') as f:
        reader = list(csv.reader(f))
    icsdlist = []
    for row in reader:
        icsd_id = ''
        for character in row[0]:
            try:
                int(character)
            except ValueError:
                icsdlist.append(icsd_id)
                break
            else:
                icsd_id += character

    resultstring='#' + '; #'.join(icsdlist)

    return resultstring

def readsearchcriteria(filename):
    with open(os.path.join(os.getcwd(), 'search_criteria', filename + '.csv'), 'rb') as f:
        reader = list(csv.reader(f))
        rowlist = []
        for row in reader:
            if row[0] != '' and row[0] != 'formula':
                rowdict = {'material': row[0]}

                for n in range(3, 10):
                    if row[n] == 'monoclinic' or row[n] == 'cubic' or row[n] == 'trigonoal' or \
                                    row[n] == 'hexagonal' or row[n] == 'tetragonal' or len(row[n]) > 4:

                        rowdict.update({'crystalsystem': row[n], 'spacegroup': row[n + 1],
                                   'bandgap': row[n + 2]})
                        break
                rowlist.append(rowdict)

        return rowlist


def parsempdata(data, name, querystring, keystring):
    resultstring = ''
    i=0
    for search in data:
        for result in search:
            cifpath = os.path.join(os.getcwd(), 'cifs', result['pretty_formula'] + '.cif')

            with open(cifpath, 'wb') as f:
                f.write(result['cif'])

            resultstring += '<tr class="results" value="' + str(i) + '" id="mpresult' + str(i) + '_con" onclick="expand(\'con\', \'result' + str(i) + '\')" onmouseover="hoveron(\'result' + str(i) + '\')" onmouseout="hoveroff(\'result' + str(i) + '\')">'
            resultstring += '<td class="results"><a href="https://www.materialsproject.org/materials/' + result['material_id'] + '/" target="_blank">' + result['pretty_formula'] + '</a></td>'
            resultstring += '<td class="results">' + result['full_formula'] + '</td>'
            resultstring += '<td class="results">' + str(result['total_magnetization'])[:6] + '</td>'
            resultstring += '<td class="results">' + str(result['is_hubbard']) + '</td>'
            resultstring += '<td class="results">' + str(result['formation_energy_per_atom'])[:6] + '</td>'
            resultstring += '<td class="results">' + str(result['e_above_hull'])[:6] + '</td>'
            resultstring += '<td class="results">' + str(result['band_gap']) + '</td>'
            resultstring += '<td class="results">' + str(result['nsites']) + '</td>'
            resultstring += '<td class="results">' + str(result['density'])[:6] + '</td>'
            resultstring += '<td class="results">' + str(result['volume'])[:6] + '</td>'
            resultstring += '<td class="results">' + result['spacegroup']['symbol'] + '</td>'
            resultstring += '<td class="results"><a href="/getcif?cif=' + result['pretty_formula'] + '" target="_blank">CIF</a></td>'
            resultstring += '<td class="results"><button onclick="window.open(\'https://www.materialsproject.org/materials/' + result['material_id'] + '/jsmol\',\'newwindow\',\'width=600,height=800\'); return false;">Open Model</button>'
            resultstring += '</tr>'

            resultstring += '<tr class="results selected" value="' + str(i) + '" style="display:none" value="full" id="mpresult' + str(i) + '_full" onclick="expand(\'full\', \'result' + str(i) + '\')" onmouseover="hoveron(\'result' + str(i) + '\')" onmouseout="hoveroff(\'result' + str(i) + '\')">'
            resultstring += '<td class="results"><a href="https://www.materialsproject.org/materials/' + result['material_id'] + '/" target="_blank">' + result['pretty_formula'] + '</a></td>'
            resultstring += '<td class="results">' + result['full_formula'] + '</td>'
            resultstring += '<td class="results">' + str(result['total_magnetization'])[:6] + '</td>'
            resultstring += '<td class="results">' + str(result['is_hubbard']) + '</td>'
            resultstring += '<td class="results">' + str(result['formation_energy_per_atom'])[:6] + '</td>'
            resultstring += '<td class="results">' + str(result['e_above_hull'])[:6] + '</td>'
            resultstring += '<td class="results">' + str(result['band_gap']) + '</td>'
            resultstring += '<td class="results">' + str(result['nsites']) + '</td>'
            resultstring += '<td class="results">' + str(result['density'])[:6] + '</td>'
            resultstring += '<td class="results">' + str(result['volume'])[:6] + '</td>'
            try:
                resultstring += '<td class="results">Sym: ' + result['spacegroup']['symbol'] + '<br> Num:  ' + str(result['spacegroup']['number']) + '<br>PG: ' + result['spacegroup']['point_group'] + '<br>Sys: ' + result['spacegroup']['crystal_system'] + '<br>Hall: ' + str(result['spacegroup']['hall']) + '</td>'
            except:
                resultstring += '<td class="results">' + result['spacegroup']['symbol'] + '</td>'
            resultstring += '<td class="results"><a href="/getcif?cif=' + result['pretty_formula'] + '" target="_blank">CIF</a></td>'
            resultstring += '<td class="results"><button onclick="window.open(\'https://www.materialsproject.org/materials/' + result['material_id'] + '/jsmol\',\'newwindow\',\'width=600,height=800\'); return false;">Open Model</button>'
            resultstring += '</tr>'

            i+=1
    return [resultstring, name, querystring, keystring]


def parsewokkeys(keywords):
    resultstring = '<td class="resultTitle">Material</td><td class="resultTitle">Publications</td>'

    for key in keywords:
        resultstring += '<td class="resultTitle">' + key + '</td>'

    return resultstring


def parsewokdata(keywords, mpdata, wokdata, keydata, name, querystring, keystring):
    resultstring = ''

    for i in range(len(wokdata)):
        hidestring = ''
        resultstring += '<tr value="' + str(i) + '" class="results" id="wokresult' + str(i) + '_con" onclick="expand(\'con\', \'result' + str(i) + '\')" onmouseover="hoveron(\'result' + str(i) + '\')" onmouseout="hoveroff(\'result' + str(i) + '\')">'

        resultstring += '<td class="results"><a href="' + wokdata[i][0]['searchURL'] + '" target="_blank">' + wokdata[i][0]['pretty_formula'] + '</a></td>'
        resultstring += '<td class="results">' + str(wokdata[i][0]['numResults']) + '</td>'
        hidestring += '<td class="results"><a href="' + wokdata[i][0]['searchURL'] + '" target="_blank">' + wokdata[i][0]['pretty_formula'] + '</a></td>'
        hidestring += '<td class="results">' + str(wokdata[i][0]['numResults']) + '</td>'

        for key in keydata[i].keys():
            numpapers = 0
            hidestring += '<td class="results">'
            for m in range(len(keydata[i][key])):
                paper = keydata[i][key][m]
                if paper != 0:
                    numpapers += 1
                    hidestring+='<a href="' + wokdata[i][1][m]['DOIlink'] + '" target="_blank">(' + str(paper) + ')</a> '

            resultstring += '<td class="results">'
            if numpapers != 0:
                resultstring += str(numpapers)
            resultstring += '</td>'
            hidestring+='</td>'

        resultstring += '</tr>'

        resultstring += '<tr value="' + str(i) + '" class="results selected" style="display:none" id="wokresult' + str(i) + '_full" value="full" onclick="expand(\'full\', \'result' + str(i) + '\')" onmouseover="hoveron(\'result' + str(i) + '\')" onmouseout="hoveroff(\'result' + str(i) + '\')">'
        resultstring += hidestring + '</tr>'

    return [parsewokkeys(keywords), parsempdata(mpdata,name,querystring,keystring)[0], resultstring, name, querystring, keystring]


def parseprevload(prevload):
    resultstring = ''

    for f in prevload:
        resultstring += '<option value="' + f + '">' + f + '</option>'

    return resultstring


def handlehtmlsearch_mp(querystring, keywordstring, cache, smartconstrain):
    queries, permqueries, constraints, keywords = searchWoKTools.parsehtmlinput(querystring, keywordstring)

    with open('mpRecord.json', 'rb') as record:
        rec = record.read()
        try:
            rlist = json.loads(rec)
        except ValueError:
            rlist = {}

    if 'queries' not in rlist.keys() or 'permqueries' not in rlist.keys():
        rlist = {'queries': {}, 'permqueries': {}}

    mpresults = []

    for i in range(len(queries)):
        query = queries[i]
        if query in rlist['queries'].keys() and cache:
            print('loading mp for ' + query + ' (' + str(i+1) + '/' + str(len(queries)) + ')')
            mpresults.append(rlist['queries'][query])
        else:
            print('searching mp for ' + query + ' (' + str(i+1) + '/' + str(len(queries)) + ')')

            try:
                if query[0] == '#':
                    result = searchWoKTools.postmaterialsproject({'criteria':{'icsd_ids':{'$in':[int(query[1:])]}}})
                else:
                    result = searchWoKTools.getmaterialsproject(query)
            except:
                with open('mpRecord.json', 'wb') as record:
                    json.dump(rlist, record)
                raise
            rlist['queries'][query] = result
            mpresults.append(result)

    for permquery in permqueries:
        permlist = permquery[1:-1].split('][')

        for i in range(len(permlist)):
            permlist[i] = permlist[i].split(',')

        lenperms = 1

        for n in permlist:
            lenperms *= len(n)

        queryarray = []
        for i in range(lenperms):
            queryarray.append([])

        repeat = 1

        for n in range(len(permlist)):
            elemlist = permlist[n]
            divlen = lenperms/len(elemlist)
            listmarker = 0

            for rep in range(repeat):
                for elem in elemlist:
                    for i in range(listmarker, listmarker + divlen):
                        queryarray[i].append(elem)
                    listmarker += divlen

            lenperms = divlen
            repeat *= len(permlist[n])

        print(queryarray)
        for query in queryarray:
            search = '-'.join(query)

            if search in rlist['queries'].keys():
                print('loading mp for ' + search)
                mpresults.append(rlist['queries'][search])
            else:
                print('searching mp for ' + search)
                try:
                    result = searchWoKTools.getmaterialsproject(search, len(query))
                except:
                    with open('mpRecord.json', 'wb') as record:
                        json.dump(rlist, record)
                    raise
                rlist['queries'][search] = result
                mpresults.append(result)

    with open('mpRecord.json', 'wb') as record:
        json.dump(rlist, record)

    mpresults = searchWoKTools.removerepeats(mpresults)

    if smartconstrain:
        mpresults = searchWoKTools.smartconstraint(mpresults)

    mpresults = searchWoKTools.removeconstrainedmp(mpresults, constraints)

    return mpresults, keywords, constraints


def handlehtmlsearch_wok(querystring, keywordstring, searchlimit, cache, smartconstrain):
    mpsearch, keywords, constraints = handlehtmlsearch_mp(querystring, keywordstring, cache, smartconstrain)

    with open('wokRecord.json', 'rb') as record:
        try:
            wlist = json.load(record)
        except ValueError:
            wlist={}

    searchtotal=0
    for search in mpsearch:
        searchtotal += len(search)

    wokresults = []
    i=0

    for search in mpsearch:
        for n in search:
            iterinput=[]
            for m in n['unit_cell_formula'].keys():
                iterinput.append(m + str(int(n['unit_cell_formula'][m])))

            iterlist = list(itertools.permutations(iterinput))

            searchparam = 'topic:' + n['pretty_formula'] + ' or topic:' + n['full_formula']

            for term in iterlist:
                searchparam += ' or topic:' + ''.join(term)

            i += 1
            if n['material_id'] in wlist.keys() and cache:
                print('loading wok for ' + n['full_formula'] + ' (' + str(i) + '/' + str(searchtotal) + ')')
                wokresults.append(wlist[n['material_id']])
            else:
                print('searching wok for ' + n['full_formula'] + ' (' + str(i) + '/' + str(searchtotal) + ')')
                try:
                    searchdata = searchWoKTools.getsearchdata(searchparam, searchlimit)
                except:
                    with open('wokRecord.json', 'wb') as record:
                        json.dump(wlist, record)
                    raise

                searchdata[0].update(n)
                wlist[n['material_id']] = searchdata
                wokresults.append(searchdata)

    mpsearch, wokresults = searchWoKTools.removeconstrainedwok(mpsearch, wokresults, constraints)

    with open('wokRecord.json', 'wb') as record:
        json.dump(wlist, record)

    keyresults = []
    for search in wokresults:
        keyresults.append(searchWoKTools.getkeylist(search, keywords))

    return keywords, mpsearch, wokresults, keyresults


def handlehtmlsearch_csv(querystring, keywordstring, searchlimit, searchname, cache, smartconstrain):
    fulltitle = os.path.join(os.getcwd(), 'materialsSearchCSV-WC', searchname + 'Full.csv')
    contitle = os.path.join(os.getcwd(), 'materialsSearchCSV-WC', searchname + 'Condensed.csv')

    if wcexists:
        if not os.path.exists(os.path.join(os.getcwd(), 'materialsSearchCSV-WC', searchname)):
            os.makedirs(os.path.join(os.getcwd(), 'materialsSearchCSV-WC', searchname))

    with open(fulltitle, 'wb') as csvFull, open(contitle, 'wb') as csvCon:
        fwriter = csv.writer(csvFull, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        cwriter = csv.writer(csvCon, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        keywords, wokresults, keyresults = handlehtmlsearch_wok(querystring, keywordstring, searchlimit, cache, smartconstrain)

        conheader = ['Material', 'Publications', 'Space Group', 'Calculated Band Gap']
        for n in keywords:
            conheader.append(n)
        cwriter.writerow(conheader)

        linenum = 0

        for i in range(len(wokresults)):
            searchdata = wokresults[i]

            if wcexists:
                wc = searchWoKTools.generateabstractwc(searchdata)
                imgpath = os.path.join(os.getcwd(), 'materialsSearchCSV-WC', searchname,
                                       searchdata[0]['pretty_formula'] + '.png')
                wc.to_file(imgpath)

            fwriter.writerow([searchdata[0]['pretty_formula'],
                              str(searchdata[0]['numResults']) + ' publications',
                              str(searchdata[0]['spacegroup']) + '  spacegroup',
                              str(searchdata[0]['band_gap']) + '  band gap',
                              searchdata[0]['searchURL'],
                              '=HYPERLINK("' + imgpath + '","Word Cloud")'])
            linenum += 1

            conline = [
                '=HYPERLINK("[' + fulltitle + ']' + searchname + 'Full' + '!A' + str(linenum) + '","' +
                searchdata[0]['pretty_formula'] + '")',

                str(searchdata[0]['numResults']),
                str(searchdata[0]['spacegroup']),
                str(searchdata[0]['band_gap'])]

            fwriter.writerow([])
            linenum += 1

            for key in keyresults[i].keys():
                keyrow = []
                conkeynum = 0
                for n in range(len(keyresults[i][key])):
                    paper = keyresults[i][key][n]
                    if paper != 0:
                        cellstring = '=HYPERLINK("' + searchdata[1][n]['DOIlink'] + '","' + key + '(' + str(
                            paper) + ')")'
                        keyrow.append(cellstring)
                        conkeynum += 1
                if keyrow:
                    fwriter.writerow(keyrow)
                    linenum += 1
                if conkeynum != 0:
                    constring = '=HYPERLINK("[' + fulltitle + ']' + searchname + 'Full' + '!A' + str(
                        linenum) + '","' + str(conkeynum) + '")'
                    conline.append(constring)
                else:
                    conline.append('')

            cwriter.writerow(conline)

            fwriter.writerow([])
            fwriter.writerow([])
            linenum += 2

    return json.dumps([os.path.join(os.getcwd(), 'materialsSearchCSV-WC', searchname)])


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

            for key in keylist.keys():
                keyrow = []
                conkeynum = 0
                for n in range(len(keylist[key])):
                    if keylist[key][n] != 0:
                        cellstring = '=HYPERLINK("' + searchData[1][n]['DOIlink'] + '","' + key + '(' + str(
                            keylist[key][n]) + ')")'
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

