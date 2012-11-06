#!/usr/bin/python
#-*- coding:utf-8 -*-

import alignment.distances as d
import alignment.normalize as n
from alignment.aligner import align


def parsefile(filename, indexes = [], nbmax = None, fielddelimiter = '\t'):
    """ Read filename line by line, (``nbmax`` line as maximum if given). Each
        line is splitted according ``fielddelimiter`` and keep ``indexes``
    """
    result = []
    with open(filename) as fobj:
        for ind, line in enumerate(fobj):
            data = []
            if nbmax and ind > nbmax:
                break
            line = line.strip().decode('utf-8')
            line = line.split(fielddelimiter)
            if not indexes:
                data = line
            else:
                for ind in indexes:
                    try:
                        if isinstance(ind, tuple):
                            data.append(tuple([line[i] for i in ind]))
                        else:
                            data.append(line[ind])
                    except IndexError:
                        data.append(None)
            result.append(data)
    return result



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
