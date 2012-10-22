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


from nltk import ngrams
from scipy.sparse import lil_matrix
from scipy import matrix
from numpy.random import shuffle
from numpy import arange, ones
from random import randint

def kshingle(content, k = 7):
    """ Return the set of k-grams of content

        eg : content = 'abcab'
             k = 2

             k-grams are : 'ab', 'bc', 'ca', 'ab'
             return is set('ab', 'ba', 'ca')
    """


    return set(''.join(t) for t in ngrams(content, k))

def matrixdocument(sentences, k = 7):
    """ Return a sparse matrix where :

        - Each sentence is a column
        - Each row is a element of the universal set

        Each value (r, c) is set to 1 if the element at row r is in the sentence
        c, 0 otherwise

    """

    sets = []
    universe = set()
    for sent in sentences:
        sets.append(kshingle(sent, k))
        universe = universe.union(sets[-1])

    matrixdoc = lil_matrix((len(universe), len(sets)))

    for inde, elt in enumerate(universe):
        for inds, curset in enumerate(sets):
            matrixdoc[inde, inds] = int(elt in curset)

    return matrixdoc

def randomhashfunction(zr):
    """ Return a random hash function, mapping x in Z to ZR
        h:x -> ax + b mod R

    """
    a = randint(1, zr - 1)
    b = randint(1, zr - 1)

    def hashfunc(x):
        return (a * x + b) % zr

    return hashfunc

def signaturematrix(matrixdocument, siglen = 4):
    """ Return a matrix where each column is the signature the document
        The signature is composed of siglen number

        The more the document have rows in commun, the closer they are.
    """

    nrows, ncols = matrixdocument.shape
    sig = ones((siglen, ncols)) * (nrows + 1)
    hashfunc = [randomhashfunction(nrows) for _ in xrange(siglen)]

    for r in xrange(nrows):
        for c in matrixdocument.rows[r]:
            for i, func in enumerate(hashfunc):
                hashr = func(r)
                if hashr < sig[i, c]:
                    sig[i, c] = hashr
    return sig

def colsimilar(signature, threahold = 0.5):
    """ Read the signature matrix return index (i, j) if column (ie sentence) i
        and j are similar


        /!\ This function should be used for testing purpose only
    """
    def sim(a, b):
        eq = (v[a] == v[b]).sum()
        return 1.0 * eq / len(v[a])

    similarity = []
    v = [signature[:, i] for i in xrange(signature.shape[1])]
    for i in xrange(len(v)):
        for j in xrange(len(v)):
            if sim(i, j) >= threahold:
                similarity.append((i, j))
    return similarity

if __name__ == '__main__':
    from normalize import (loadlemmas, lemmatized)

    sentences = ["j'aime le poisson", "le poisson c'est bon", 
                 "je cuis le poisson", "je fais du sport",
                 "le sport c'est bon pour la sante",
                 "pour la sante le sport est bon",
                 "le programme TV de ce soir est interessant",
                 "le poisson est cuit",
                 "les carottes sont cuites"]

    lemmas = loadlemmas('data/french_lemmas.txt')
    m = matrixdocument([lemmatized(s, lemmas) for s in sentences], 3)
    signature = signaturematrix(m, 100)
    simi = colsimilar(signature)

    print 'Les phrases sont : '
    for s in sentences:
        print ' - %s' % s

    print '\nLes phrases similaires sont : '
    (ip, _) = simi[0]
    for (i, j) in simi:
        if ip != i:
            print
        print ' -', sentences[i], '---', sentences[j]
        ip = i
