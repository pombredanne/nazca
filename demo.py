#!/usr/bin/python
#-*- coding:utf-8 -*-

import alignment.distances as d
import alignment.normalize as n
from alignment.aligner import align, parsefile

if __name__ == '__main__':
    targetset = parsefile('data/FR.txt', indexes = [0, 1, (4, 5)], nbmax = 2000)
    alignset = parsefile('data/frenchbnf', indexes = [0, 2, (14, 12)],
                           nbmax = 1000)

    tr_name = { 'normalization': [n.simplify],
                'distance': d.levenshtein,
                'weighting': 1
              }
    tr_geo = { 'normalization': [],
               'distance': d.geographical,
               'distance_args': {'units' : 'km'},
               'weighting': 1
             }

    mat, _ = align(alignset, targetset, [tr_name, tr_geo], 0.4, 'alignment_results')

    print mat
