"""Generates comprehensive materials database from wokRecord.json"""

import json
import os
import csv
import bibtexparser
import requests

def getsource(material):
    print('Grabbing MP BIB info for ' + material + '...')

    key = '0cVziFePTUfsawW8'

    url = 'https://www.materialsproject.org/materials/' + material + '/bibtex?API_KEY=' + key
    
    t=0
    rbib = []
    while t<4:
        try:
            r = requests.get(url)
            if r.status_code == 200:
                rbib = bibtexparser.loads(r.text).entries
                break
            else:
                print('error' + str(t))
                t = t+1
            
        except requests.ConnectionError:
            print('error' + str(t))
            t = t+1
    
    source = []
    
    for entry in rbib:
        if entry['ID'] != 'MaterialsProject' and entry['ID'] != 'Bergerhoff1983' and entry['ID'] != 'Karlsruhe':
            try:
                source.append(entry)
            except KeyError:
                pass
    
    return source
            

with open('matdb.json','rb') as prevmdb:
    pmdb = prevmdb.read()
    
    try:
        pdb = json.loads(pmdb)
    except ValueError:
        pdb = {}

with open(os.path.join(os.path.dirname(os.getcwd()),'resources','json','wokRecord.json'),'rb') as wrecord:
    wrec = wrecord.read()
    
    try:
        wlist = json.loads(wrec)
    except ValueError:
        wlist = {}

db={}

for item in wlist.keys():

    icsd = {'source':[],
            'cif':wlist[item][0]['cif'],
            'icsd':[],
            'structype':''}
    
    mp = {'totmag':wlist[item][0]['total_magnetization'],
            'forme':wlist[item][0]['formation_energy_per_atom'],
            'bgap':wlist[item][0]['band_gap'],
            'strucdata':wlist[item][0]['spacegroup'],
            'eabovehull':wlist[item][0]['e_above_hull'],
            'ishubbard':wlist[item][0]['is_hubbard'],
            'mpurl':'https://www.materialsproject.org/materials/'+item}
    exp = {'Tc':None,
            'movector':[None,None,None],
            'mag':[None,None,None],
            'To':None,
            'sbcoeff':None,
            'magresistB':[None],
            'magresistP':[None],
            'TresistT':[None],
            'TresistP':[None],
            'TsuscepT':[None],
            'TsuscepX':[None],
            'references':[None]}
    
    for cat in [[icsd,'icsd'],[mp,'mp'],[exp,'exp']]:
        for key in cat[0].keys():
            try:
                if pdb[item][cat[1]][key] not in [None,[None]]:
                    cat[0][key] = pdb[item][cat[1]][key]
            except KeyError:
                pass

    for entry in getsource(item):
        try:
            icsd['source'].append(entry)
            exp['references'].append(entry['link'])
        except KeyError:
            pass
        
        print(exp['references'])
        print(icsd['source'])
    
    db[item] = {'elements':wlist[item][0]['unit_cell_formula'],
                'formula':wlist[item][0]['pretty_formula'],
                'icsd':icsd,
                'mp':mp,
                'exp':exp,
                'comments':pdb[item]['comments']
                }
 
with open(os.path.join(os.path.dirname(os.getcwd()),'resources','json','mpRecord.json'), 'rb') as record:
        rec = record.read()
        try:
            rlist = json.loads(rec)
        except ValueError:
            rlist = {}

rawicsd = os.listdir(os.path.join(os.path.dirname(os.getcwd()), 'resources', 'rawICSD'))

for filename in rawicsd:
    with open(os.path.join(os.path.dirname(os.getcwd()), 'resources', 'rawICSD', filename), 'rb') as f:
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
    
    for icsd in icsdlist:
        result = rlist['queries']['#'+icsd]
        
        for rec in result:
            try:
                db[rec['material_id']]['icsd']['structype'] = filename[:-4]
                db[rec['material_id']]['icsd']['icsd'].append(icsd)
            except KeyError:
                pass
                
with open('matdb.json','wb') as mdb:
    json.dump(db, mdb)
                
