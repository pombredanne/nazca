# -*- coding:utf-8 -*-

import alignment.distances as d
import rdflib

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
    fieldsdbpedia = { 'given' : [],
                      'family' : [],
                      'birthdate' : [],
                      'birthplace' : [],
                      'deathdate' : [],
                      'deathplace' : [],
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

    g = rdflib.Graph()
    result = g.parse('data/dbpedia_data.nt', format='nt')
    predicates = (
        ('given', 'http://xmlns.com/foaf/0.1/givenName'),
        ('family', 'http://xmlns.com/foaf/0.1/surname'),
        ('birthdate', 'http://dbpedia.org/ontology/birthDate'),
        ('birthplace', 'http://dbpedia.org/ontology/birthPlace'),
        ('deathdate', 'http://dbpedia.org/ontology/deathDate'),
        ('deathplace', 'http://dbpedia.org/ontology/deathPlace')
        )

    dbpedia = {}
    for (key, p) in predicates:
        for (s, o) in g.subject_objects(rdflib.URIRef(p)):
            dbpedia.setdefault(s, {})
            dbpedia[s].update({key : o.lower()})
    for uri in dbpedia:
        for (p, _) in predicates:
            fieldsdbpedia[p].append(dbpedia[uri].get(p))
        fieldsdbpedia['uri'].append(uri)




    ## weighting of birthdate and deathdate is higher than given and familly
    ## name because they are language independant
    items = [
        (2, fieldsopencat['given'],
            fieldsdbpedia['given'],
            d.levenshtein, 10, True, {}),
        (2, fieldsopencat['family'],
            fieldsdbpedia['family'],
            d.levenshtein, 10, True, {}),
        (3, fieldsopencat['birthdate'],
            fieldsdbpedia['birthdate'],
            d.temporal, 30, True,
              {'granularity' : 'days',
               'dayfirst' : False,
               'yearfirst' : True,
              }),
#        (1, fieldsopencat['birthplace'],
#               fieldsdbpedia['birthplace'],
#               d.jaccard, 1, {}),
        (3, fieldsopencat['deathdate'],
            fieldsdbpedia['deathdate'],
            d.temporal, 30, True,
            {'granularity' : 'days',
             'dayfirst' : False,
             'yearfirst' : True,
            }),
#        (1, fieldsopencat['deathplace'],
#               fieldsdbpedia['deathplace'],
#               d.jaccard, 1, {}),
    ]

    return items, fieldsopencat['uri'], fieldsdbpedia['uri']

