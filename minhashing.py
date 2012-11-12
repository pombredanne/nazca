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

import cPickle

from random import randint
from collections import defaultdict

from numpy import ones
from scipy.sparse import lil_matrix
from scipy.optimize import bisect

from alignment.normalize import iter_wordgrams

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

        rows, data, universe, sizeofuniverse = [], [], {}, 0
        for sent in sentences:
            row = []
            for w in iter_wordgrams(sent, k):
                row.append(universe.setdefault(w, sizeofuniverse))
                if row[-1] == sizeofuniverse:
                    sizeofuniverse += 1
            rows.append(row)
            data.append([1] * len(row))

        matrixdoc = lil_matrix((len(rows), sizeofuniverse))
        matrixdoc.rows = rows
        matrixdoc.data = data

        return matrixdoc.T

    def _signaturematrix(self, matrixdocument, siglen):
        """ Return a matrix where each column is the signature the document
            The signature is composed of `siglen` numbers

            The more the documents have rows in commun, the closer they are.
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

    def save(self, savefile):
        """ Save the training into `savefile` for a future use """

        if not self._trained:
            print "Not trained, nothing to save"
            return

        with open(savefile, 'wb') as fobj:
            pickler = cPickle.Pickler(fobj)
            pickler.dump(self.sigmatrix)

    def load(self, savefile):
        """ Load a trained minhashing """

        with open(savefile, 'rb') as fobj:
            pickler = cPickle.Unpickler(fobj)
            self.sigmatrix = pickler.load()

        if self.sigmatrix is not None:
            self._trained = True
        else:
            self._trained = False

    def findsimilarsentences(self, threshold, sentenceid = None):
        """ Return a set of tuples of *possible* similar sentences

            If 0 <= sentenceid <= nbsentences is given:
                return a set of tuples of *possible* similar sentences to this
                one
        """

        def computebandsize(threshold, nbrows):
            """ Compute the bandsize according to the threshold given """

            ### t ~ (1/b)^(1/r), where t is the threshold, b the number of
            ### bands, and r the number of rows per band. And nbrows (the length
            ### of the matrix is nbrows = b * r, so t ~ (r / L)^(1 / r). So, let's
            ### find the root of f(x) = (x / L)^(1/r) - t.
            def f(x):
                y = pow(x / nbrows, 1. /x) - threshold
                return y

            ## Solve f(x) = 0, with x having values in [1, nbrows]
            return int(bisect(f, 1, nbrows))


        if not self._trained:
            print "Train it before"
            return

        if not (0 < threshold <= 1):
            print "Threshold must be in ]0 ; 1]"
            return

        col = [self.sigmatrix[:, i] for i in xrange(self.sigmatrix.shape[1])]
        bandsize = computebandsize(threshold, self.sigmatrix.shape[0])

        buckets = defaultdict(set)
        for r in xrange(0, self.sigmatrix.shape[0], bandsize):
            for i in xrange(len(col)):
                buckets[tuple(col[i][r:r+bandsize])].add(i)
            #print "Progress : %.3f" % (r * 100. / self.sigmatrix.shape[0])

        if sentenceid and 0 <= sentenceid < self.sigmatrix.shape[1]:
            return set(tuple(v) for v in buckets.itervalues()
                       if len(v) > 1 and sentenceid in v)
        return set(tuple(v) for v in buckets.itervalues() if len(v) > 1)

if __name__ == '__main__':
    from alignment.normalize import (loadlemmas, simplify)
    from time import time

    with open('data/french_sentences.txt') as fobj:
        sentences = [line.strip() for line in fobj]


    lemmas = loadlemmas('data/french_lemmas.txt')
    minlsh = Minlsh()

    t0 = time()
    minlsh.train((simplify(s, lemmas) for s in sentences), 1, 100)
    t1 = time()


#    print 'Les phrases sont : '
#    for s in sentences:
#        print ' - %s' % s

    print '\nLes phrases *possiblement* similaires sont : '
    t2 = None
    for s in minlsh.findsimilarsentences(0.7):
        if not t2:
            t2 = time()
        for e in s:
            print ' -', sentences[e]
        print
        if raw_input():
            break

    print 'Training + signaturing time : %.3fs (for %d sentences)' \
          % ((t1 - t0), len(sentences))

    print '%.3fs' % (t2 - t1)

