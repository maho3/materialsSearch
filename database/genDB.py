"""Generates comprehensive materials database from wokRecord.json"""

import json
import os
import csv
import searchWoKTools

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
    db[item] = {'formula':wlist[item][0]['pretty_formula'],
                'fformula':wlist[item][0]['full_formula'],
                'elements':wlist[item][0]['unit_cell_formula'],
                'totmag':wlist[item][0]['total_magnetization'],
                'forme':wlist[item][0]['formation_energy_per_atom'],
                'bgap':wlist[item][0]['band_gap'],
                'structype':'',
                'strucdata':wlist[item][0]['spacegroup'],
                'eabovehull':wlist[item][0]['e_above_hull'],
                'ishubbard':wlist[item][0]['is_hubbard'],
                'mpurl':'https://www.materialsproject.org/materials/'+item,
                'icsd':[],
                'numpub':wlist[item][0]['numResults']
                }
    try:
        db[item]['properties'] = pdb[item]['properties']
    except KeyError:
        db[item]['properties'] = {'superconducts':'',
                                'conduct':'',
                                'magnetism':'',
                                'CDW':'',
                                'Tn':0,
                                'comments':'',
                                'references':[]
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
                db[rec['material_id']]['structype'] = filename[:-4]
                db[rec['material_id']]['icsd'].append(icsd)
            except KeyError:
                pass
                
with open('matdb.json','wb') as mdb:
    json.dump(db, mdb)
                
