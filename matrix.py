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

from collections import defaultdict
from copy import deepcopy

from scipy import array, empty
from scipy import where

import alignment.distances as ds

METRICS = {'euclidean': ds.euclidean, 'levenshtein': ds.levenshtein,
           'soundex': ds.soundex, 'jaccard': ds.jaccard,
           'temporal': ds.temporal, 'geographical': ds.geographical}


def pdist(X, metric='euclidean', matrix_normalized=True, metric_params=None):
    """ Compute the upper triangular matrix in a way similar
    to scipy.spatial.metric

    If matrix_normalized is True, the distance between two points is changed to
    a value between 0 (equal) and 1 (totaly different). To avoid useless
    computation and scale problems the following “normalization” is done:
        d = 1 - 1/(1 + d(x, y))

    """
    metric = metric if not isinstance(metric, basestring) else METRICS.get(metric, ds.euclidean)
    values = []
    for i in xrange(len(X)):
        for j in xrange(i+1, len(X)):
            d = 1
            if X[i] and X[j]:
                d = metric(X[i], X[j], **(metric_params or {}))
                if matrix_normalized:
                    d = 1 - (1.0/(1.0 + d))
            values.append(d)
    return values

def cdist(X, Y, metric='euclidean', matrix_normalized=True, metric_params=None):
    """ Compute the metric matrix, given two inputs and a metric

    If matrix_normalized is True, the distance between two points is changed to
    a value between 0 (equal) and 1 (totaly different). To avoid useless
    computation and scale problems the following “normalization” is done:
        d = 1 - 1/(1 + d(x, y))

    """
    metric = metric if not isinstance(metric, basestring) else METRICS.get(metric, ds.euclidean)
    distmatrix = empty((len(X), len(Y)), dtype='float32')
    size = distmatrix.shape
    for i in xrange(size[0]):
        for j in xrange(size[1]):
            d = 1
            if X[i] and Y[j]:
                d = metric(X[i], Y[j], **(metric_params or {}))
                if matrix_normalized:
                    d = 1 - (1.0/(1.0 + d))
            distmatrix[i, j] = d
    return distmatrix

def matched(distmatrix, cutoff=0, normalized=False):
    """ Return the matched elements within a dictionnary,
    each key being the indice from X, and the corresponding
    values being a list of couple (indice from Y, distance)
    """
    match = defaultdict(list)
    if normalized:
        distmatrix /= distmatrix.max()

    ind = (distmatrix <= cutoff).nonzero()
    indrow = ind[0].tolist()
    indcol = ind[1].tolist()

    for (i, j) in zip(indrow, indcol):
        match[i].append((j, distmatrix[i, j]))

    return match

def globalalignmentmatrix(items):
    """ Compute and return the global alignment matrix.
        Let's explain :

        - `items` is a list of tuples where each tuple is built as following :

            `(weighting, input1, input2, distance_function, normalize, args)`

            * `input1` : a list of "things" (names, dates, numbers) to align onto
                `input2`. If a value is unknown, set it as `None`.

            * `distance_function` : the distance function used to compute the
                 distance matrix between `input1` and `input2`

            * `weighting` : the weight of the "things" computed, compared
                 with the others "things" of `items`

            * `normalize` : boolean, if true, the matrix values will be between 0
                and 1, else the real result of `distance_function` will be
                stored

            * `args` : a dictionnay of the extra arguments the
                `distance_function` could take (as language or granularity)

     - For each tuple of `items` a `Distancematrix` is built, then all the
       matrices are summed with their own weighting and the result is the global
       alignment matrix, which is returned.

       /!\ All `input1` and `input2` of each tuple must have the same size
           in twos
      XXX Write an assertion
    """
    globalmatrix = items[0][0]*cdist(*items[0][1:])
    for item in items[1:]:
        globalmatrix += item[0]*cdist(*item[1:])
    return globalmatrix
