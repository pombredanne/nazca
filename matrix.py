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
from scipy import matrix, empty
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

    def __init__(self, weighting, input1, input2, distance, defvalue,
                 normalized = True, kargs = {}):
        self.distance = distance
        self._matrix = empty((len(input1), len(input2)), dtype='float32')
        self.size = self._matrix.shape
        self.normalized = normalized
        self._compute(weighting, input1, input2, defvalue, kargs)

    def _compute(self, weighting, input1, input2, defvalue, kargs):
        for i in xrange(self.size[0]):
            for j in xrange(self.size[1]):
                d = defvalue
                if input1[i] and input2[j]:
                    d = self.distance(input1[i], input2[j], **kargs)

                if self.normalized:
                    d = 1 - (1.0 / (1.0 + d))

                d *= weighting
                self._matrix[i, j] = d

    def __getitem__(self, index):
        return self._matrix[index]

    def __repr__(self):
        return self._matrix.__repr__()

    def __rmul__(self, number):
        return self * number

    def __mul__(self, number):
        if not (isinstance(number, int) or isinstance(number, float)):
            raise NotImplementedError

        other = deepcopy(self)
        other._matrix *= number
        return other

    def __add__(self, other):
        if not isinstance(other, Distancematrix):
            raise NotImplementedError

        result = deepcopy(self)
        result._matrix = (self._matrix + other._matrix)
        return result

    def __sub__(self, other):
        if not isinstance(other, Distancematrix):
            raise NotImplementedError

        result = deepcopy(self)
        result._matrix = (self._matrix - other._matrix)
        return result

    def __eq__(self, other):
        if not isinstance(other, Distancematrix):
            return False

        if (self._matrix != other._matrix).any():
            return False

        if self.distance != other.distance:
            return False

        return True


    def matched(self, cutoff = 0, normalized = False):
        match = defaultdict(list)
        if normalized:
            self._matrix /= self._matrix.max()

        ind = (self._matrix <= cutoff).nonzero()
        indrow = ind[0].tolist()
        indcol = ind[1].tolist()

        for (i, j) in zip(indrow, indcol):
            match[i].append((j, self._matrix[i, j]))

        return match

def globalalignmentmatrix(items):
    """ Compute and return the global alignment matrix.
        Let's explain :

        - `items` is a list of tuples where each tuple is built as following :

            `(weighting, input1, input2, distance_function, defvalue, normalize, args)`

            * `input1` : a list of "things" (names, dates, numbers) to align on
                 `input2`. If a value is unknown, set it as `None`.

            * `distance_function` : the distance function used to compute the
                 distance matrix between `input1` and `input2`

            * `weighting` : the weighting of the "things" computed, compared
                 with the others "things" of `items`

            * `defvalue` : default value to use if an element of `input1` or
                 `input2` is unknown. A good idea should be `defvalue` has an
                 upper bound of the possible values to maximize the distance

            * `normalize` : boolean, if true, the matrix values will between 0
                and 1, else the real result of `distance_function` will be
                stored

            * `args` : a dictionnay of the extra arguments the
                `distance_function` could take (as language or granularity)

     - For each tuple of `items` as `Distancematrix` is built, then all the
       matrices are summed with their own weighting and the result is the global
       alignment matrix, which is returned.

       /!\ All `input1` and `input2` of each tuple must have the same size
           in twos
    """
    globalmatrix = Distancematrix(*items[0])
    for item in items[1:]:
        globalmatrix +=  Distancematrix(*item)
    return globalmatrix
