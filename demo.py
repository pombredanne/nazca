#!/usr/bin/python
#-*- coding:utf-8 -*-

from os import path

#XXX aln, ald
import alignment.distances as d
import alignment.normalize as n
from alignment.aligner import align, subalign, findneighbours
from alignment.dataio import parsefile, sparqlquery, write_results

DEMODIR = path.dirname(__file__)

def dpath(filename):
    return path.join(DEMODIR, 'demo', filename)

def demo_0():
    # prixgoncourt is the list of Goncourt Prize, extracted
    # from wikipedia

    #We try to align Goncourt winers onto dbpedia results

    #XXX Make some prints


    query = """
       SELECT ?writer, ?name WHERE {
          ?writer  <http://purl.org/dc/terms/subject> <http://dbpedia.org/resource/Category:French_novelists>.
          ?writer rdfs:label ?name.
          FILTER(lang(?name) = 'fr')
       }
    """

    print "Sending query to dbpedia"
    targetset = sparqlquery('http://dbpedia.org/sparql', query)
    alignset = parsefile(dpath('prixgoncourt'), indexes=[1, 1])

    def removeparenthesis(string):
        if '(' in string:
            return string[:string.index('(')]
        return string

    tr_name = {'normalization': [removeparenthesis, n.simplify],
               'metric': d.levenshtein
              }

    treatments = {1: tr_name}

    dmatrix, hasmatched = align(alignset, targetset, 0.4, treatments,
                                dpath('demo0_results'))

    print dmatrix


def demo_1():
    # FR.txt is an extract of geonames, where locations have been sorted by name
    # frenchbnf is an extract of french BNF's locations, sorted by name too

    # For each line (ie location) we keep the identifier, the name and the
    # position (longitude, latitude)
    # ``nbmax`` is the number of locations to load

    targetset = parsefile(dpath('FR.txt'), indexes=[0, 1, (4, 5)],
                          nbmax=2000)
    alignset = parsefile(dpath('frenchbnf'),
                         indexes=[0, 2, (14, 12)], nbmax=1000)


    # Let's define the treatments to apply on the location's name
    tr_name = {'normalization': [n.simplify], # Simply all the names (remove
                                              #   punctuation, lower case, etc)
               'metric': d.levenshtein,       # Use the levenshtein distance
               'weighting': 1                 # Use 1 a name-distance matrix
                                              #   weighting coefficient
              }
    tr_geo = {'normalization': [],              # No normalization needed
              'metric': d.geographical,         # Use the geographical distance
              'metric_params': {'units': 'km'},# Arguments given the
                                                #   distance function. Here,
                                                #   the unit to use
              'weighting': 1
             }

    treatments = {1: tr_name, 2: tr_geo}

    dmatrix, hasmatched = align(alignset,           # The dataset to align
                                targetset,          # The target dataset
                                0.4,                # The maximal distance
                                                    #   threshold
                                treatments,         # The list of treatments to
                                                    #   apply.
                                dpath('demo1_results'))
                                                    # Filename of the output
                                                    #   result file
    # the ``align()`` function return two items
    # 0. the computed distance matrix
    # 1. a boolean, True if at least one alignment has been done, False
    #    otherwise
    print dmatrix

#def parsefile(filepath, transforms):
#    pass
#
#
#parsefile('fr.txt', {0: int, 1: lambda x: x.decode('utf-8'), 14: float, 12:
#                     float}, indexes=[0, 2, (14, 12)])
#
#
#def make_index_transformer(indexes, transform_map):
#    def xxx(row):
#        data = [transform_map[i](row[i]) for in indexes]
#        return data
#    return xxx
#
#
#
#parsefile('fr.txt', line_transformer=make_index_transformer)
#
#
def demo_2():
    targetset = parsefile(dpath('FR.txt'), indexes=[0, 1, (4, 5)])
    alignset = parsefile(dpath('frenchbnf'), indexes=[0, 2, (14, 12)],
                         nbmax=30000)

    print "Finding neighbours"
    neighbours = findneighbours(alignset, targetset, indexes=(2, 2),
                               mode='minibatch')

    # Let's define the treatments to apply on the location's name
    tr_name = {'normalization': [lambda x: str(x),#Some names are casted to
                                                  #int/float, just correct it
                                 n.simplify], # Simply all the names (remove
                                              #   punctuation, lower case, etc)
               'metric': d.levenshtein,       # Use the levenshtein distance
               'weighting': 1                 # Use 1 a name-distance matrix
                                              #   weighting coefficient
              }

    treatments = {1: tr_name}
    print "Start computation"
    for ind, (alignid, targetid) in enumerate(neighbours):
        print '%3d' % ind, len(alignid), 'x', len(targetid)
        mat, matched = subalign(alignset,   # The dataset to align
                                targetset,  # The target dataset
                                alignid,
                                targetid,
                                0.3,
                                treatments)
        write_results(matched, alignset, targetset, dpath('demo2_results'))

if __name__ == '__main__':
    import sys
    from time import time
    runall = (len(sys.argv) == 1)

    t = time()
    if runall or '0' in sys.argv:
        print "Running demo_0"
        demo_0()

    if runall or '1' in sys.argv:
        print "Running demo_1"
        demo_1()

    if runall or '2' in sys.argv:
        print "Running demo_2"
        ## Same as demo_1, but in a more efficient way, using a KDTree
        demo_2()

    print "Demo terminated"
    print "Took %d min" % ((time() - t)/60)
