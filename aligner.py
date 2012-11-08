# -*- coding:utf-8 -*-
# copyright 2012 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
# contact http://www.logilab.fr -- mailto:contact@logilab.fr
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 2.1 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.

from os.path import exists as fileexists

import csv


import alignment.matrix as m

def _autocasted(data, encoding=None):
    data = data.strip()
    try:
        return int(data)
    except ValueError:
        try:
            return float(data)
        except ValueError:
            if encoding:
                return data.decode(encoding)
            return data



def findneighbours(alignset, targetset, indexes = (1, 1), mode = 'kdtree',
                   threshold = 0.1, k = 2, n_clusters = None):

    SEARCHERS = set(['kdtree', 'minhashing', 'kmeans', 'minibatch'])
    mode = mode.lower()

    if mode not in SEARCHERS:
        raise NotImplementedError('Unknown mode given')

##### KDTree #######
    if mode == 'kdtree':
        from scipy.spatial import KDTree
        # XXX : If there are more than 2 dimensions ??
        aligntree  = KDTree([elt[indexes[0]] or (0, 0) for elt in alignset])
        targettree = KDTree([elt[indexes[1]] or (0, 0) for elt in targetset])
        extraneighbours = aligntree.query_ball_tree(targettree, threshold)
        neighbours = []
        for ind in xrange(len(alignset)):
            neighbours.append([[ind], extraneighbours[ind]])
            if len(neighbours[-1][1]) == 0:
                neighbours.pop()
        return neighbours

#### Minhashing #####
    elif mode == 'minhashing':
        from alignment.minhashing import Minlsh
        minhasher = Minlsh()
        minhasher.train([elt[indexes[0]] or '' for elt in alignset] +
                        [elt[indexes[1]] or '' for elt in targetset],
                        k)
        rawneighbours = minhasher.findsimilarsentences(threshold)
        neighbours = []
        for data in rawneighbours: #XXX: Return an iterator
            neighbours.append([[], []])
            for i in data:
                if i >= len(alignset):
                    neighbours[-1][1].append(i - len(alignset))
                else:
                    neighbours[-1][0].append(i)
            if len(neighbours[-1][0]) == 0 or len(neighbours[-1][1]) == 0:
                neighbours.pop()
        return neighbours

#### Kmeans #####
    elif mode in set(['kmeans', 'minibatch']):
        from sklearn import cluster
        n_clusters = n_clusters or len(alignset) / 10

        if mode == 'kmeans':
            kmeans = cluster.KMeans(n_clusters=n_clusters)
        else:
            kmeans = cluster.MiniBatchKMeans(n_clusters=n_clusters)
        # XXX : If there are more than 2 dimensions ??
        kmeans.fit([elt[indexes[0]] or (0, 0) for elt in alignset])
        predicted = kmeans.predict([elt[indexes[1]] or (0, 0) for elt in targetset])

        clusters = [[[], []] for _ in xrange(kmeans.n_clusters)]
        for ind, i in enumerate(predicted):
            clusters[i][1].append(ind)
        for ind, i in enumerate(kmeans.labels_):
            clusters[i][0].append(ind)
        return clusters

def align(alignset, targetset, treatments, threshold, resultfile):
    """ Try to align the items of alignset onto targetset's ones

        `alignset` and `targetset` are the sets to align. Each set contains
        lists where the first column is the identifier of the item, and the others are
        the attributs to align. (Note that the order is important !) Both must
        have the same number of columns.

        `treatments` is a list of dictionnaries. Each dictionnary contains the
        treatments to do on the different attributs. The first dictionnary is
        for the first attribut (not the identifier !), the second for the
        second, etc. Each dictionnary is built as the following:

            treatment = { 'normalization': [f1, f2, f3],
                          'norm_args': { 'arg1': arg01, 'arg2': arg02},
                          'distance': d1,
                          'distance_args': { 'arg1': arg11 },
                          'weighting': w,
                          'matrix_normalize': True
                        }

            `normalization` is the list of functions called to normalize the
            given attribut (in order). Each functions is called with `norm_args`
            as arguments

            Idem for `distance` and `distance_args`

            `weighting` is the weighting for the current attribut in regard to
            the others

        `resultfile` is the name of the output csv.
    """

    def normalizerset(rset):
        """ Apply all the normalization functions to the given rset """
        for row in rset:
            for ind, attribut in enumerate(row[1:]):
                treat = treatments[ind]
                if not attribut:
                    continue
                for f in treat['normalization']:
                    farg = f.func_code.co_varnames #List of the arguments of f
                    # A kind of union between the arguments needed by f, and the
                    # provided ones
                    givenargs = dict((arg, treat['norm_args'][arg])
                                 for arg in farg if arg in treat['norm_args'])
                    attribut = f(attribut, **givenargs)
                row[ind + 1] = attribut
        return rset

    ## Just to be certain we have all the keys
    for t in treatments:
        t.setdefault('norm_args', {})
        t.setdefault('distance_args', {})
        t.setdefault('weighting', 1)
        t.setdefault('matrix_normalize', True)

    ralignset = normalizerset(alignset)
    rtargetset = normalizerset(targetset)

    items = []
    for ind, tr in enumerate(treatments):
        item = (tr['weighting'],
                [ralignset[i][ind + 1] for i in xrange(len(ralignset))],
                [rtargetset[i][ind + 1] for i in xrange(len(rtargetset))],
                tr['distance'],
                tr['matrix_normalize'],
                tr['distance_args'])
        items.append(item)

    mat = m.globalalignmentmatrix(items)
    matched = mat.matched(threshold)

    if not matched:
        return mat, False

    openmode = 'a' if fileexists(resultfile) else 'w'
    with open(resultfile, openmode) as fobj:
        if openmode == 'w':
            fobj.write('aligned;targetted;distance\n')
        for aligned in matched:
            for target, dist in matched[aligned]:
                alignid = ralignset[aligned][0]
                targetid = rtargetset[target][0]
                fobj.write('%s;%s;%s\n' %
                    (alignid.encode('utf-8') if isinstance(alignid, basestring)
                                             else alignid,
                     targetid.encode('utf-8') if isinstance(targetid, basestring)
                                              else targetid,
                     dist
                    ))
    return mat, True

def sparqlquery(endpoint, query, indexes=[]):
    """ Run the sparql query on the given endpoint, and wrap the items in the
    indexes form. If indexes is empty, keep raw output"""

    from SPARQLWrapper import SPARQLWrapper, JSON

    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    rawresults = sparql.query().convert()
    labels = rawresults['head']['vars']
    results = []

    for raw in rawresults["results"]["bindings"]:
        data = []
        if not indexes:
            data = [_autocasted(raw[label]['value']) for label in labels]
        else:
            for ind in indexes:
                if isinstance(ind, tuple):
                    data.append(tuple([_autocasted(raw[labels[i]]['value']) for i in ind]))
                else:
                    data.append(_autocasted(raw[labels[ind]]['value']))
        results.append(data)
    return results


def parsefile(filename, indexes=[], nbmax=None, delimiter='\t', encoding='utf-8'):
    """ Parse the file (read ``nbmax`` line at maximum if given). Each
        line is splitted according ``delimiter`` and only ``indexes`` are kept

        eg : The file is :
                1, house, 12, 19, apple
                2, horse, 21.9, 19, stramberry
                3, flower, 23, 2.17, cherry

            data = parsefile('myfile', [0, (2, 3), 4, 1], delimiter=',')

            The result will be :
            data = [[1, (12,   19), 'apple', 'house'],
                    [2, (21.9, 19), 'stramberry', 'horse'],
                    [3, (23,   2.17), 'cherry', 'flower']]

    """
    def formatedoutput(filename):
        with open(filename, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=delimiter)
            for row in reader:
                yield [_autocasted(cell) for cell in row]



    result = []
    for ind, row in enumerate(formatedoutput(filename)):
        data = []
        if nbmax and ind > nbmax:
            break
        if not indexes:
            data = row
        else:
            for ind in indexes:
                if isinstance(ind, tuple):
                    data.append(tuple([row[i] for i in ind]))
                    if '' in data[-1]:
                        data[-1] = None
                elif row[ind]:
                    data.append(row[ind])
                else:
                    data.append(None)

        result.append(data)
    return result
