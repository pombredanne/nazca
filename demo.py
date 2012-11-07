#!/usr/bin/python
#-*- coding:utf-8 -*-

import alignment.distances as d
import alignment.normalize as n
from alignment.aligner import align, parsefile

def demo_0():
    # prixgoncourt is the list of Goncourt Prize, extracted
    # from wikipedia

    # dbfrenchauthors is an extract dbpedia for the query :
    #   SELECT ?writer, ?name WHERE {
    #      ?writer  <http://purl.org/dc/terms/subject> <http://dbpedia.org/resource/Category:French_novelists>.
    #      ?writer rdfs:label ?name.
    #      FILTER(lang(?name) = 'fr')
    #   }

    #We try to align Goncourt winers onto dbpedia results

    alignset = parsefile('demo/prixgoncourt', indexes = [1, 1])
    targetset = parsefile('demo/dbfrenchauthors', indexes = [0, 1], delimiter='#')

    def removeparenthesis(string):
        if '(' in string:
            return string[:string.index('(')]
        return string

    tr_name = { 'normalization' : [removeparenthesis, n.simplify],
                'distance': d.levenshtein
              }

    dmatrix, hasmatched = align(alignset, targetset, [tr_name],
                                0.4, 'demo/demo0_results')

    print dmatrix


def demo_1():
    # FR.txt is an extract of geonames, where locations have been sorted by name
    # frenchbnf is an extract of french BNF's locations, sorted by name too

    # For each line (ie location) we keep the identifier, the name and the
    # position (longitude, latitude)
    # ``nbmax`` is the number of locations to load

    targetset = parsefile('demo/FR.txt', indexes = [0, 1, (4, 5)], nbmax = 2000)
    alignset = parsefile('demo/frenchbnf', indexes = [0, 2, (14, 12)], nbmax = 1000)


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
                                'demo/demo1_results')    # Filename of the output
                                                    #   result file
    # the ``align()`` function return two items
    # 0. the computed distance matrix
    # 1. a boolean, True if at least one alignment has been done, False
    #    otherwise
    print dmatrix

if __name__ == '__main__':
    demo_0()
    demo_1()

