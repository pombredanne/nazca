# -*- coding:utf-8 -*-

import cubes.alignment.distances as d
from cubes.alignment.dbpedia import dbparse

def dbpediasent(filename, maxind = None, enco = 'unicode_escape'):
    fobj = open(filename)
    fobj.readline()
    for ind, line in enumerate(fobj):
        if maxind and ind >= maxind:
            break
        line = line.strip().decode(enco)
        line = line.split('> "')[-1].split('"@fr')[0]
        if not line:
            continue
        yield line

def printsents(filename, indastr, maxind = None):
    ind = [int(i) for i in indastr.split(' ')]
    for i, s in enumerate(dbpediasent(filename, maxind)):
        if i in ind:
            print s.encode('utf-8')
            print
            
def builtItemsFromData(datafile):
    """
        given_name;family_name;birthdate;birthplace;deathdate;deathplace
    """

    def gettuples(datafile):
        def none2None(mylist):
            cleanlist = []
            for e in mylist:
                if e == 'None':
                    cleanlist.append(None)
                else:
                    cleanlist.append(e)
            return cleanlist

        fobj = open(datafile)
        for line in fobj:
            line = line.strip().decode('utf-8')
            yield none2None(line.split(';'))

    fieldsopencat = { 'given' : [],
                      'family' : [],
                      'birthdate' : [],
                      'birthplace' : [],
                      'deathdate' : [],
                      'deathplace' : [],
                      'uri' : []
                    }
    fieldsdbpedia = { 'givenName' : [],
                      'surname' : [],
                      'birthDate' : [],
                      'birthPlace' : [],
                      'deathDate' : [],
                      'deathPlace' : [],
                      'uri' : []
                    }

    for uri, g, f, bd, bp, dd, dp in gettuples(datafile):
        fieldsopencat['given'].append(g)
        fieldsopencat['family'].append(f)
        fieldsopencat['birthdate'].append(bd)
        fieldsopencat['birthplace'].append(bp)
        fieldsopencat['deathdate'].append(dd)
        fieldsopencat['deathplace'].append(dp)
        fieldsopencat['uri'].append(uri)

    olduri = None
    for uri, attr, val in dbparse('data/dbpedia_data.nt', 
                         attributs = set(fieldsdbpedia.keys()), uri = False):
        maxlen = max([len(v) for v in fieldsdbpedia.values()])
        if olduri and uri != olduri:
            for key in fieldsdbpedia.keys():
                if key == attr or key == 'uri':
                    continue
                diff = maxlen - len(fieldsdbpedia[key])

                while diff > 0:
                    print "missing : ", olduri, key
                    fieldsdbpedia[key].append(None)
                    diff -= 1
        if olduri == uri and maxlen and len(fieldsdbpedia[attr]) == maxlen:
            continue
        olduri = uri
        print "add : ", uri, attr, val
        fieldsdbpedia[attr].append(val)
        if not fieldsdbpedia['uri'] or fieldsdbpedia['uri'][-1] != uri:
            fieldsdbpedia['uri'].append(uri)


    for key in fieldsdbpedia.keys():
        if key == attr or key == 'uri':
            continue
        diff = maxlen - len(fieldsdbpedia[key])

        while diff > 0:
            print "missing : ", olduri, key
            fieldsdbpedia[key].append(None)
            diff -= 1
    items = [
        (1, fieldsopencat['given'],
            fieldsdbpedia['givenName'],
            d.jaccard, 1, {}),
        (1, fieldsopencat['family'],
            fieldsdbpedia['surname'],
            d.jaccard, 1, {}),
        (20, fieldsopencat['birthdate'],
              fieldsdbpedia['birthDate'],
              d.temporal, 20000, {'granularity' : 'months',
                              'dayfirst' : False,
                              'yearfirst' : True,
                              }),
        (0.1, fieldsopencat['birthplace'],
               fieldsdbpedia['birthPlace'], 
               d.jaccard, 10, {}),
        (20, fieldsopencat['deathdate'],
              fieldsdbpedia['deathDate'], 
              d.temporal, 20000, {'granularity' : 'months',
                              'dayfirst' : False,
                              'yearfirst' : True,
                             }),
        (0.1, fieldsopencat['deathplace'],
               fieldsdbpedia['deathPlace'],
               d.jaccard, 10, {}),
    ]

    return items, fieldsopencat['uri'], fieldsdbpedia['uri'] 

