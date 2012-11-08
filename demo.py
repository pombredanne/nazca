#!/usr/bin/python
#-*- coding:utf-8 -*-

from os import path

import alignment.distances as d
import alignment.normalize as n
from alignment.aligner import align, parsefile, findneighbours, sparqlquery

DEMODIR = path.dirname(__file__)

def demo_0():
    # prixgoncourt is the list of Goncourt Prize, extracted
    # from wikipedia

    #We try to align Goncourt winers onto dbpedia results


    query = """
       SELECT ?writer, ?name WHERE {
          ?writer  <http://purl.org/dc/terms/subject> <http://dbpedia.org/resource/Category:French_novelists>.
          ?writer rdfs:label ?name.
          FILTER(lang(?name) = 'fr')
       }
    """

    targetset = sparqlquery('http://dbpedia.org/sparql', query)
    alignset = parsefile(path.join(DEMODIR, 'demo','prixgoncourt'), indexes = [1, 1])

    def removeparenthesis(string):
        if '(' in string:
            return string[:string.index('(')]
        return string

    tr_name = { 'normalization' : [removeparenthesis, n.simplify],
                'distance': d.levenshtein
              }

    dmatrix, hasmatched = align(alignset, targetset, [tr_name],
                                0.4, 'demo0_results')

    print dmatrix


def demo_1():
    # FR.txt is an extract of geonames, where locations have been sorted by name
    # frenchbnf is an extract of french BNF's locations, sorted by name too

    # For each line (ie location) we keep the identifier, the name and the
    # position (longitude, latitude)
    # ``nbmax`` is the number of locations to load

    targetset = parsefile(path.join(DEMODIR, 'demo', 'FR.txt'), indexes = [0, 1, (4, 5)],
                          nbmax = 2000)
    alignset = parsefile(path.join(DEMODIR, 'demo', 'frenchbnf'),
                         indexes = [0, 2, (14, 12)], nbmax = 1000)


    # Let's define the treatements to apply on the location's name
    tr_name = { 'normalization': [n.simplify], # Simply all the names (remove
                                               #   punctuation, lower case, etc)
                'distance': d.levenshtein,     # Use the levenshtein distance
                'weighting': 1                 # Use 1 a name-distance matrix
                                               #   weighting coefficient
              }
    tr_geo = { 'normalization': [],              # No normalization needed
               'distance': d.geographical,       # Use the geographical distance
               'distance_args': {'units' : 'km'},# Arguments given the
                                                 #   distance function. Here,
                                                 #   the unit to use
               'weighting': 1
             }

    dmatrix, hasmatched = align(alignset,           # The dataset to align
                                targetset,          # The target dataset
                                [tr_name, tr_geo],  # The list of treatements to
                                                    #   apply. One per item,
                                                    #   given by order.
                                0.4,                # The maximal distance
                                                    #   threshold
                                'demo1_results')    # Filename of the output
                                                    #   result file
    # the ``align()`` function return two items
    # 0. the computed distance matrix
    # 1. a boolean, True if at least one alignment has been done, False
    #    otherwise
    print dmatrix

def demo_2():
    targetset = parsefile(path.join(DEMODIR, 'demo', 'FR.txt'), indexes=[0, 1, (4, 5)])
    alignset = parsefile(path.join(DEMODIR, 'demo', 'frenchbnf'), indexes=[0, 2, (14, 12)])

    neighbors = findneighbours(alignset, targetset, indexes=(2, 2),
                               mode='kdtree', threshold=0.1)

    # Let's define the treatements to apply on the location's name
    tr_name = { 'normalization': [lambda x: str(x),#Some names are casted to
                                                   #int/float, just correct it
                                  n.simplify], # Simply all the names (remove
                                               #   punctuation, lower case, etc)
                'distance': d.levenshtein,     # Use the levenshtein distance
                'weighting': 1                 # Use 1 a name-distance matrix
                                               #   weighting coefficient
              }

    print "Start computation"
    for ind, nei in enumerate(neighbors):
#        print alignset[ind][1]
#        print [targetset[i][1] for i in nei]
        m, b = align([alignset[ind][:2]],      # The dataset to align
              [targetset[i][:2] for i in nei], # The target dataset
              [tr_name],
              0.3,
              'demo2_results')  # Filename of the output
                                #   result file

if __name__ == '__main__':
    print "Running demo_0"
    demo_0()

    print "Running demo_1"
    demo_1()

    print "Running demo_2"
    ## Same as demo_1, but in a more efficient way, using a KDTree
    demo_2()
