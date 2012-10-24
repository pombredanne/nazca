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

from cubes.alignment.distances import (levenshtein, soundex, \
                                       jaccard, temporal, euclidean)
from collections import defaultdict
from scipy.sparse import lil_matrix
from scipy import where
from copy import deepcopy

class Distancematrix(object):
    """ Construct and compute a matrix of distance given a distance function.

        Given :
            input1 = ['Victor Hugo', 'Albert Camus']
            input2 = ['Victor Wugo', 'Albert Camus']
            distance = levensthein

            constructs the following matrix :
                 +----+----+
                 | 1  | 11 |
                 +----+----+
                 | 11 | 0  |
                 +----+----+
    """

    def __init__(self, input1, input2, distance, defvalue, kargs = {}):
        self.distance = distance
        self._matrix = lil_matrix((len(input1), len(input2)), dtype='float32')
        self.size = self._matrix.get_shape()
        self._maxdist = 0
        self._compute(input1, input2, defvalue, kargs)

    def _compute(self, input1, input2, defvalue, kargs):
        for i in xrange(self.size[0]):
            for j in xrange(self.size[1]):
                if not (input1[i] and input2[j]):
                    self._matrix[i, j] = defvalue
                    continue

                self._matrix[i, j] = self.distance(input1[i], input2[j], **kargs)
                if self._matrix[i, j] > self._maxdist:
                    self._maxdist = self._matrix[i, j]

    def __getitem__(self, index):
        return self._matrix[index]

    def __repr__(self):
        return self._matrix.todense().__repr__()

    def __rmul__(self, number):
        return self * number

    def __mul__(self, number):
        if not (isinstance(number, int) or isinstance(number, float)):
            raise NotImplementedError

        other = deepcopy(self)
        other._matrix *= number
        other._maxdist *= number
        return other

    def __add__(self, other):
        if not isinstance(other, Distancematrix):
            raise NotImplementedError

        result = deepcopy(self)
        result._maxdist = self._maxdist + other._maxdist
        result._matrix = (self._matrix + other._matrix).tolil()
        return result

    def __sub__(self, other):
        if not isinstance(other, Distancematrix):
            raise NotImplementedError

        result = deepcopy(self)
        result._maxdist = self._maxdist - other._maxdist
        result._matrix = (self._matrix - other._matrix).tolil()
        return result

    def __eq__(self, other):
        if not isinstance(other, Distancematrix):
            return False

        if (self._matrix.rows != other._matrix.rows).any():
            return False

        if (self._matrix.data != other._matrix.data).any():
            return False

        if self.distance != other.distance:
            return False

        return True


    def matched(self, cutoff = 0, normalized = False):
        match = defaultdict(list)
        if normalized:
            cutoff *= self._maxdist

        for i in xrange(self._matrix.shape[0]):
            for j in xrange(self._matrix.shape[1]):
                if self._matrix[i, j] <= cutoff:
                    if normalized:
                        match[i].append((j, self._matrix[i, j]/self._maxdist))
                    else:
                        match[i].append((j, self._matrix[i, j]))
        return match

def globalalignmentmatrix(items):
    """ Compute and return the global alignment matrix.
        Let's explain :

        - `items` is a list of tuples where each tuple is built as following :

            `(weighting, input1, input2, distance_function, defvalue, args)`

            * `input1` : a list of "things" (names, dates, numbers) to align on
                 `input2`. If a value is unknown, set it as `None`.

            * `distance_function` : the distance function used to compute the
                 distance matrix between `input1` and `input2`

            * `weighting` : the weighting of the "things" computed, compared
                 with the others "things" of `items`

            * `defvalue` : default value to use if an element of `input1` or
                 `input2` is unknown. A good idea should be `defvalue` has an
                 upper bound of the possible values to maximize the distance

            * `args` : a dictionnay of the extra arguments the
                `distance_function` could take (as language or granularity)

     - For each tuple of `items` as `Distancematrix` is built, then all the
       matrices are summed with their own weighting and the result is the global
       alignement matrix, which is returned.

       /!\ All `input1` and `input2` of each tuple must have the same size
           in twos
    """
    globalmatrix = items[0][0] * Distancematrix(*items[0][1:])
    for item in items[1:]:
        tmp =  item[0] * Distancematrix(*item[1:])
        print tmp._maxdist
        globalmatrix +=  tmp
    return globalmatrix
