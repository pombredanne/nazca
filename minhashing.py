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


from scipy.sparse import lil_matrix
from numpy import ones
from random import randint
from collections import defaultdict
from time import time

from cubes.alignment.normalize import wordgrams

def randomhashfunction(zr):
    """ Return a random hash function, mapping x in Z to ZR
        h:x -> ax + b mod R

    """
    a = randint(1, zr - 1)
    b = randint(1, zr - 1)

    def hashfunc(x):
        return ((a * x + b) % zr)

    return hashfunc


class Minlsh(object):
    """ Operate minhashing + locally-sensitive-hashing to find similar sentences
    """

    def __init__(self):
        self._trained = False
        self.sigmatrix = None

    def train(self, sentences, k = 2, siglen = 200):
        """ Train the minlsh on the given sentences.

            - `k` is the length of the k-wordgrams used
              (the lower k is, the faster is the training)
            - `siglen` the length of the sentences signature

        """

        matrixdocument = self._buildmatrixdocument(sentences, k)
        print "Training is done. Wait while signaturing"

        self.sigmatrix = self._signaturematrix(matrixdocument, siglen)
        self._trained = True


    def _buildmatrixdocument(self, sentences, k):
        """ Return a sparse matrix where :

            - Each sentence is a column
            - Each row is a element of the universal set

            Each value (r, c) is set to 1 if the element at row r is in the
            sentence c, 0 otherwise

        """

        rows = []
        data = []
        universe = {}
        sizeofuniverse = 0
        for sent in sentences:
            row = []
            rowdata = []
            for w in wordgrams(sent, k):
                row.append(universe.setdefault(w, sizeofuniverse))
                if row[-1] == sizeofuniverse:
                    sizeofuniverse += 1
                rowdata.append(1)
            rows.append(row)
            data.append(rowdata)

        matrixdoc = lil_matrix((len(rows), sizeofuniverse))
        matrixdoc.rows = rows
        matrixdoc.data = data

        return matrixdoc.T

    def _signaturematrix(self, matrixdocument, siglen):
        """ Return a matrix where each column is the signature the document
            The signature is composed of siglen number

            The more the document have rows in commun, the closer they are.
        """

        nrows, ncols = matrixdocument.shape
        sig = ones((siglen, ncols)) * (nrows + 1)
        hashfunc = [randomhashfunction(nrows) for _ in xrange(siglen)]

        for r in xrange(nrows):
            hashrs = [(i, func(r)) for i, func in enumerate(hashfunc)]
            for c in matrixdocument.rows[r]:
                for i, hashr in hashrs:
                    if hashr < sig[i, c]:
                        sig[i, c] = hashr
        return sig

    def findsimilarsentences(self, bandsize, sentenceid = -1, dispThreshold = False):
        """ Return a set of tuples of *possible* similar sentences

            If 0 <= sentenceid <= nbsentences is given:
                return a set of tuples of *possible* similar sentences to this
                one
        """

        if not self._trained:
            print "Train it before"
            return

        col = [self.sigmatrix[:, i] for i in xrange(self.sigmatrix.shape[1])]
        buckets = defaultdict(set)

        nbbands = int(self.sigmatrix.shape[0] / bandsize)
        if dispThreshold:
            print "threshold is %.3f" % pow(1./nbbands, 1./bandsize)

        for r in xrange(0, self.sigmatrix.shape[0], bandsize):
            for i in xrange(len(col)):
                stri = ''.join(str(val) for val in col[i][r:r+bandsize])
                buckets[hash(stri)].add(i)

        if 0 <= sentenceid < self.sigmatrix.shape[1]:
            return set(tuple(v) for v in buckets.values()
                       if len(v) > 1 and sentenceid in v)
        return set(tuple(v) for v in buckets.values() if len(v) > 1)

if __name__ == '__main__':
    from cubes.alignment.normalize import (loadlemmas, simplify)

    sentences = ["j'aime le poisson", "le poisson c'est bon",
                 "je cuis le poisson", "je fais du sport",
                 "le sport c'est bon pour la sante",
                 "pour la sante le sport est bon",
                 "le programme TV de ce soir est interessant",
                 "le poisson est cuit",
                 "les carottes sont cuites"]

    lemmas = loadlemmas('data/french_lemmas.txt')
    minlsh = Minlsh()
    minlsh.train((simplify(s, lemmas) for s in sentences), 1, 200)

    print 'Les phrases sont : '
    for s in sentences:
        print ' - %s' % s

    print '\nLes phrases *possiblement* similaires sont : '
    for s in minlsh.findsimilarsentences(6):
        for e in s:
            print ' -', sentences[e]
        print

