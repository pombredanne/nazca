#!/usr/bin/python
#-*- coding:utf-8 -*-

import alignment.distances as d
import alignment.normalize as n
from alignment.aligner import align, parsefile

if __name__ == '__main__':

    # FR.txt is an extract of geonames, where locations have been sorted by name
    # frenchbnf is an extract of french BNF's locations, sorted by name too

    # For each line (ie location) we keep the identifier, the name and the
    # position (longitude, latitude)
    # ``nbmax`` is the number of locations to load

    targetset = parsefile('data/FR.txt', indexes = [0, 1, (4, 5)], nbmax = 2000)
    alignset = parsefile('data/frenchbnf', indexes = [0, 2, (14, 12)], nbmax = 1000)


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
                                'alignment_results')# Filename of the output
                                                    #   result file
    # the ``align()`` function return two items
    # 0. the computed distance matrix
    # 1. a boolean, True if at least one alignment has been done, False
    #    otherwise
    print dmatrix
