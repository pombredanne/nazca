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

    def __init__(self, input1, input2, distance):
        self.distance = distance
        self._matrix = lil_matrix((len(input1), len(input2)), dtype='float32')
        self.size = self._matrix.get_shape()
        self._maxdist = 0
        self._compute(input1, input2)

    def _compute(self, input1, input2):
       for i in xrange(self.size[0]):
           for j in xrange(self.size[1]):
               self._matrix[i,j] = self.distance(input1[i], input2[j])
               if self._matrix[i,j] > self._maxdist:
                   self._maxdist = self._matrix[i,j]

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

        row, col = self._matrix.nonzero()
        rowcol = zip(row, col)

        #Get those that exactly matched
        allindexes = ((i, j) for i in xrange(self.size[0])
                                 for j in xrange(self.size[1]))
        zeros = [index for index in allindexes if index not in rowcol]
        for (i, j) in zeros:
            match[i].append((j, 0))

        if cutoff > 0: #If more is wanted, return it too
            for (i, j) in rowcol:
                if self._matrix[i, j] <= cutoff:
                    match[i].append((j, self._matrix[i, j]))
        return match
