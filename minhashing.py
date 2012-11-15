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

import numpy as np
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
        return ((a*x + b)%zr)

    return hashfunc


class Minlsh(object):
    """ Operate minhashing + locally-sensitive-hashing to find similar sentences
    """

    def __init__(self):
        self._trained = False
        self.sigmatrix = None

    def train(self, sentences, k=2, siglen=200):
        """ Train the minlsh on the given sentences.

            - `k` is the length of the k-wordgrams used
              (the lower k is, the faster is the training)
            - `siglen` the length of the sentences signature

        """

        rows, shape = self._buildmatrixdocument(sentences, k)
        print "Training is done. Wait while signaturing"

        self._computesignaturematrix(rows, shape, siglen)
        self._trained = True


    def _buildmatrixdocument(self, sentences, k):
        """ Return a sparse matrix where :

            - Each sentence is a column
            - Each row is a element of the universal set

            Each value (r, c) is set to 1 if the element at row r is in the
            sentence c, 0 otherwise

        """

        rows, universe, sizeofuniverse = [], {}, 0
        for sent in sentences:
            row = []
            for w in iter_wordgrams(sent, k):
                row.append(universe.setdefault(w, sizeofuniverse))
                if row[-1] == sizeofuniverse:
                    sizeofuniverse += 1
            rows.append(row)

        return rows, (len(rows), sizeofuniverse)

    def _computesignaturematrix(self, rows, shape, siglen):
        """ Return a matrix where each column is the signature the document
            The signature is composed of `siglen` numbers

            The more the documents have rows in commun, the closer they are.
        """

        nrows, ncols = shape
        sig = np.empty((siglen, nrows))
        #Generate the random hash functions
        hashfunc = [randomhashfunction(ncols) for _ in xrange(siglen)]
        #Compute hashing values just for once.
        #Avoid multiple recomputations for the same column.
        hashvalues = np.array([[hashfunc[i](r) for r in xrange(ncols)]
                                for i in  xrange(siglen)])

        docind = 0
        while rows:
            doc = rows.pop(0)
            #Concatenate the needed rows.
            tmp = np.dstack([hashvalues[:, r] for r in doc])
            #Take the mininum of hashes
            sig[:, docind] = np.min(tmp[0], 1)
            docind += 1
        self.sigmatrix = sig

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

    def computebandsize(self, threshold, nbrows):
        """ Compute the bandsize according to the threshold given """

        ### t ~ (1/b)^(1/r), where t is the threshold, b the number of
        ### bands, and r the number of rows per band. And nbrows (the length
        ### of the matrix is nbrows = b*r, so t ~ (r/L)^(1/r). So, let's
        ### find the root of f(x) = (x/L)^(1/r) - t.
        def f(x):
            y = pow(x/nbrows, 1. /x) - threshold
            return y

        ## Solve f(x) = 0, with x having values in [1, nbrows]
        return int(bisect(f, 1, nbrows))

    def predict(self, threshold):
        """ Return a set of tuples of *possible* similar sentences
        """
        if not self._trained:
            print "Train it before"
            return

        if not (0 < threshold <= 1):
            print "Threshold must be in ]0 ; 1]"
            return

        sig = self.sigmatrix
        # Treshold is a percent of similarity
        # It should be inverted here (0 is closed, 1 is far)
        threshold = 1 - threshold
        bandsize = self.computebandsize(threshold, self.sigmatrix.shape[0])

        buckets = defaultdict(set)
        similars = set()
        for r in xrange(0, sig.shape[0], bandsize):
            buckets.clear()
            for i in xrange(sig.shape[1]):
                buckets[tuple(sig[r:r+bandsize, i])].add(i)
            similars.update(set(tuple(v) for v in buckets.itervalues()
                                         if len(v) > 1))
        return similars


if __name__ == '__main__':
    from alignment.normalize import (loadlemmas, simplify)
    from alignment.dataio import parsefile
    from time import time
    import matplotlib.pyplot as plt
    from scipy import polyfit

    sentences = [s[0] for s in parsefile('data/US.txt', indexes=[1],
                               field_size_limit=1000000000, nbmax=None) if s[0]]


    lemmas = loadlemmas('data/french_lemmas.txt')
    minlsh = Minlsh()

    def compute_complexite(size):
        print "%d%%" % size
        t0 = time()
        length = int(size*len(sentences)/100)
        minlsh.train((simplify(s, lemmas) for s in sentences[:length]), 1, 100)
        t1 = time()
        r = minlsh.predict(0.3)
        t2 = time()
        print 'Nb sentences : %d' % length
        print 'Training + signaturing time : %.3fs' % (t1 - t0)
        print 'Similarity %.3fs' % (t2 - t1)
        print 'Total : %.3fs' % (t2 - t0)
        return len(sentences[:length]), (t1 - t0), (t2 - t1)

    x = []
    ytrain = []
    ysimil = []
    ycumul = []
    print "Start the computation"
    for size in xrange(1, 100, 5):
        p = compute_complexite(size)
        x.append(p[0])
        ytrain.append(p[1])
        ysimil.append(p[2])
        ycumul.append(p[1] + p[2])

    plt.plot(x, ytrain, label='trainning')
    plt.plot(x, ysimil, label='buckets')
    plt.plot(x, ycumul, label='cumul')
    plt.legend()
    print polyfit(x, ytrain, 1)
    print polyfit(x, ysimil, 1)
    plt.show()
