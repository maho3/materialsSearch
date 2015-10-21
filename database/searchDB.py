"""Toolbox for matdb.json"""

import json

with open('matdb.json','rb') as rawdb:
    dbrec = rawdb.read()
    
    try:
        db = json.loads(dbrec)
    except ValueError:
        db = {}

def returnRec(mpid):
    return db[mpid]

def findKey(key, value):
    result = []
    
    for item in db.keys():
        if db[item][key] == value:
            result.append(db[item])
    
    return result

def findProperty(prop, value):
    result = []
    
    for item in db.keys():
        if db[item]['properties'][prop] == value:
            result.append(db[item])
    
    return result
    
def getValues(array, key):
    result = []

    for entry in array:
        result.append(entry[key])
    
    return result
    
def getProperty(array, prop):
    result = []
    
    for entry in array:
        result.append(entry['properties'][prop])
        
    return result
    
def sort():
    with open('matdb.json','rb') as rawdb:
        dbrec = rawdb.read()
        
        try:
            db = json.loads(dbrec)
        except ValueError:
            db = {}
    def getKey(item):
        return item[1]['icsd']['structype']
    
    ndb = sorted(db.items(), key=getKey);
    
    with open('matdb_sort.json','wb') as mdb:
        json.dump(ndb, mdb)
