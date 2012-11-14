# -*- coding:utf-8 -*-
#
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

"""cubicweb-alignment automatic tests


uncomment code below if you want to activate automatic test for your cube:

.. sourcecode:: python

    from cubicweb.devtools.testlib import AutomaticWebTest

    class AutomaticWebTest(AutomaticWebTest):
        '''provides `to_test_etypes` and/or `list_startup_views` implementation
        to limit test scope
        '''

        def to_test_etypes(self):
            '''only test views for entities of the returned types'''
            return set(('My', 'Cube', 'Entity', 'Types'))

        def list_startup_views(self):
            '''only test startup views of the returned identifiers'''
            return ('some', 'startup', 'views')
"""

import unittest2
import random
import numpy as np

from os import path
random.seed(6) ### Make sure tests are repeatable

from alignment.distances import (levenshtein, soundex, soundexcode,   \
                                 jaccard, temporal, euclidean,        \
                                 geographical)
from alignment.normalize import (lunormalize, loadlemmas, lemmatized, \
                                 roundstr, rgxformat, tokenize, simplify)
import alignment.matrix as am
from alignment.minhashing import Minlsh
from alignment.dataio import parsefile, autocasted
import alignment.aligner as alig


TESTDIR = path.dirname(__file__)

class DistancesTest(unittest2.TestCase):
    def test_levenshtein(self):
        self.assertEqual(levenshtein('niche', 'chiens'), 5)
        self.assertEqual(levenshtein('bonjour', 'bonjour !'), 1)
        self.assertEqual(levenshtein('bon', 'bonjour'), 4)
        self.assertEqual(levenshtein('Victor Hugo', 'Hugo Victor'), 0)

        #Test symetry
        self.assertEqual(levenshtein('Victor Hugo', 'Vitor Wugo'),
                         levenshtein('Vitor Wugo', 'Victor Hugo'))

    def test_soundex(self):
        ##     Test extracted from Wikipedia en :
        #Using this algorithm :
        #both "Robert" and "Rupert" return the same string "R163"
        #while "Rubin" yields "R150".
        #
        # "Ashcraft" and "Ashcroft" both yield "A261" and not "A226"
        #(the chars 's' and 'c' in the name would receive a single number
        #of 2 and not 22 since an 'h' lies in between them).
        #
        # "Tymczak" yields "T522" not "T520"
        #(the chars 'z' and 'k' in the name are coded as 2 twice since a vowel
        #lies in between them).
        #
        #"Pfister" yields "P236" not "P123" (the first two letters have the same
        #number and are coded once as 'P').

        self.assertEqual(soundexcode('Robert', 'english'), 'R163')
        self.assertEqual(soundexcode('Rubert', 'english'), 'R163')
        self.assertEqual(soundexcode('Rubin', 'english'), 'R150')
        self.assertEqual(soundexcode('Ashcraft', 'english'), 'A261')
        self.assertEqual(soundexcode('Tymczak', 'english'), 'T522')
        self.assertEqual(soundexcode('Pfister', 'english'), 'P236')

        self.assertEqual(soundex('Rubert', 'Robert', 'english'), 0)
        self.assertEqual(soundex('Rubin', 'Robert', 'english'), 1)

    def test_jaccard(self):
        #The jaccard indice between two words is the ratio of the number of
        #identical letters and the total number of letters
        #Each letter is counted once only
        #The distance is 1 - jaccard_indice

        self.assertEqual(jaccard('bonjour', 'bonjour'), 0.0)
        self.assertAlmostEqual(jaccard('boujour', 'bonjour'), 1, 2)
        self.assertAlmostEqual(jaccard(u'sacré rubert', u'sacré hubert'), 0.667, 2)

        #Test symetry
        self.assertEqual(jaccard('orange', 'morange'),
                         jaccard('morange', 'orange'))

    def test_temporal(self):
        #Test the distance between two dates. The distance can be given in
        #``days``, ``months`` or ``years``

        self.assertEqual(temporal('14 aout 1991', '14/08/1991'), 0)
        self.assertEqual(temporal('14 aout 1991', '08/14/1991'), 0)
        self.assertEqual(temporal('14 aout 1991', '08/15/1992'), 367)
        #Test a case of ambiguity
        self.assertEqual(temporal('1er mai 2012', '01/05/2012'), 0)
        self.assertEqual(temporal('1er mai 2012', '05/01/2012', dayfirst = False), 0)
        #Test the different granularities available
        self.assertAlmostEqual(temporal('14 aout 1991', '08/15/1992', 'years'), 1.0, 1)
        self.assertAlmostEqual(temporal('1991', '1992', 'years'), 1.0, 1)
        self.assertAlmostEqual(temporal('13 mars', '13 mai', 'months'), 2.0, 1)
        self.assertAlmostEqual(temporal('13 march', '13 may', 'months',
                                        'english'), 2.0, 1)

        #Test fuzzyness
        self.assertEqual(temporal('Jean est né le 1er octobre 1958',
                                  'Le 01-10-1958, Jean est né'), 0)

        #Test symetry
        self.assertEqual(temporal('14-08-1991', '15/08/1992'),
                         temporal('15/08/1992', '14/08/1991'))

    def test_euclidean(self):
        self.assertEqual(euclidean(10, 11), 1)
        self.assertEqual(euclidean(-10, 11), 21)
        self.assertEqual(euclidean('-10', '11'), 21)

        #Test symetry
        self.assertEqual(euclidean(10, 11),
                         euclidean(11, 10))

    def test_geographical(self):
        paris = (48.856578, 2.351828)
        london = (51.504872, -0.07857)
        dist_parislondon = geographical(paris, london, in_radians = False)

        self.assertAlmostEqual(dist_parislondon, 341564, 0)


class NormalizerTestCase(unittest2.TestCase):
    def setUp(self):
        self.lemmas = loadlemmas(path.join(TESTDIR, 'data', 'french_lemmas.txt'))

    def test_unormalize(self):
        self.assertEqual(lunormalize(u'bépoèàÀêùï'),
                                     u'bepoeaaeui')

    def test_simplify(self):
        self.assertEqual(simplify(u"J'aime les frites, les pommes et les" \
                                  u" scoubidous !", self.lemmas),
                         u"aimer frites pomme scoubidou")

    def test_tokenize(self):
        self.assertEqual(tokenize(u"J'aime les frites !"),
                         [u"J'", u'aime', u'les', u'frites', u'!',])

    def test_lemmatizer(self):
        self.assertEqual(lemmatized(u'sacré rubert', self.lemmas), u'sacré rubert')
        self.assertEqual(lemmatized(u"J'aime les frites !", self.lemmas),
                         u'je aimer le frite')
        self.assertEqual(lemmatized(u", J'aime les frites", self.lemmas),
                         u'je aimer le frite')

    def test_round(self):
        self.assertEqual(roundstr(3.14159, 2), '3.14')
        self.assertEqual(roundstr(3.14159), '3')
        self.assertEqual(roundstr('3.14159', 3), '3.142')

    def test_format(self):
        string = u'[Victor Hugo - 26 fev 1802 / 22 mai 1885]'
        regex  = r'\[(?P<firstname>\w+) (?P<lastname>\w+) - ' \
                 r'(?P<birthdate>.*) \/ (?P<deathdate>.*?)\]'
        output = u'%(lastname)s, %(firstname)s (%(birthdate)s - %(deathdate)s)'
        self.assertEqual(rgxformat(string, regex, output),
                         u'Hugo, Victor (26 fev 1802 - 22 mai 1885)')

        string = u'http://perdu.com/42/supertop/cool'
        regex  = r'http://perdu.com/(?P<id>\d+).*'
        output = u'%(id)s'
        self.assertEqual(rgxformat(string, regex, output),
                         u'42')

class MatrixTestCase(unittest2.TestCase):

    def setUp(self):
        self.input1 = [u'Victor Hugo', u'Albert Camus', 'Jean Valjean']
        self.input2 = [u'Victor Wugo', u'Albert Camus', 'Albert Camu']
        self.distance = levenshtein
        self.matrix = am.cdist(self.input1, self.input2, self.distance, False)

    def test_matrixconstruction(self):
        d = self.distance
        i1, i2 = self.input1, self.input2
        m = self.matrix

        for i in xrange(len(i1)):
            for j in xrange(len(i2)):
                self.assertAlmostEqual(m[i, j], d(i1[i], i2[j]), 4)

    def test_matched(self):
        d = self.distance
        i1, i2 = self.input1, self.input2
        m = self.matrix

        #Only the element 1 of input1 has *exactly* matched with the element 1
        #of input2
        self.assertEqual(am.matched(m), {1: [(1, 0)]})

        #Victor Hugo --> Victor Wugo
        #Albert Camus --> Albert Camus, Albert Camu
        self.assertEqual(am.matched(m, cutoff = 2),
                        {0: [(0, d(i1[0], i2[0]))], 1: [(1, d(i1[1], i2[1])),
                                                        (2, d(i1[1], i2[2]))]})

    def test_operation(self):
        m = self.matrix
        self.assertTrue((3 * m == m * 3).all())
        self.assertTrue(((m - 0.5*m) == (0.5 * m)).all())
        self.assertTrue(((m + 10*m - m * 3) == (8 * m)).all())

    def test_pdist(self):
        _input = [u'Victor Wugo', u'Albert Camus', 'Albert Camu']
        d = self.distance
        pdist = am.pdist(_input, self.distance, False)
        self.assertEqual(pdist, [6, 6, 1])


class MinLSHTest(unittest2.TestCase):
    def test_all(self):
        sentences = [u"Un nuage flotta dans le grand ciel bleu.",
                     u"Des grands nuages noirs flottent dans le ciel.",
                     u"Je n'aime pas ce genre de bandes dessinées tristes.",
                     u"J'aime les bandes dessinées de genre comiques.",
                     u"Pour quelle occasion vous êtes-vous apprêtée ?",
                     u"Je les vis ensemble à plusieurs occasions.",
                     u"Je les ai vus ensemble à plusieurs occasions.",
                    ]
        minlsh = Minlsh()
        lemmas = loadlemmas(path.join(TESTDIR, 'data', 'french_lemmas.txt'))
        # XXX Should works independantly of the seed. Unstability due to the bands number ?
        minlsh.train((simplify(s, lemmas, remove_stopwords=True) for s in sentences), 1, 200)
        self.assertEqual(minlsh.predict(0.4), set([(0, 1), (2, 3), (5,6)]))


class DataIOTestCase(unittest2.TestCase):
    def test_parser(self):
        data = parsefile(path.join(TESTDIR, 'data', 'file2parse'),
                         [0, (2, 3), 4, 1], delimiter=',')
        self.assertEqual(data, [[1, (12, 19), 'apple', 'house'],
                                [2, (21.9, 19), 'stramberry', 'horse'],
                                [3, (23, 2.17), 'cherry', 'flower']])

    def test_autocasted(self):
        self.assertEqual(autocasted('1'), 1)
        self.assertEqual(autocasted('1.'), 1.)
        self.assertEqual(autocasted('1,'), 1.)
        self.assertEqual(autocasted('1,2'), 1.2)
        self.assertEqual(autocasted('1,2X'), '1,2X')
        self.assertEqual(autocasted(u'tété'), u'tété')


class AlignerTestCase(unittest2.TestCase):

    def test_findneighbours_kdtree(self):
        alignset = [['V1', 'label1', (6.14194444444, 48.67)],
                    ['V2', 'label2', (6.2, 49)],
                    ['V3', 'label3', (5.1, 48)],
                    ['V4', 'label4', (5.2, 48.1)],
                    ]
        targetset = [['T1', 'labelt1', (6.2, 48.9)],
                     ['T2', 'labelt2', (5.3, 48.2)],
                     ['T3', 'labelt3', (6.25, 48.91)],
                     ]
        neighbours = alig.findneighbours_kdtree(alignset, targetset, indexes=(2, 2), threshold=0.3)
        self.assertEqual(neighbours, [[[0], [0, 2]], [[1], [0, 2]], [[2], [1]], [[3], [1]]])

    def test_findneighbours_minhashing(self):
        lemmas = loadlemmas(path.join(TESTDIR, 'data', 'french_lemmas.txt'))
        treatments = {2: {'normalization': [simplify,], 'norm_params': {'lemmas': lemmas}}}
        alignset = [['V1', 'label1', u"Un nuage flotta dans le grand ciel bleu."],
                    ['V2', 'label2', u"Pour quelle occasion vous êtes-vous apprêtée ?"],
                    ['V3', 'label3', u"Je les vis ensemble à plusieurs occasions."],
                    ['V4', 'label4', u"Je n'aime pas ce genre de bandes dessinées tristes."],
                    ['V5', 'label5', u"Ensemble et à plusieurs occasions, je les vis."],
                    ]
        targetset = [['T1', 'labelt1', u"Des grands nuages noirs flottent dans le ciel."],
                     ['T2', 'labelt2', u"Je les ai vus ensemble à plusieurs occasions."],
                     ['T3', 'labelt3', u"J'aime les bandes dessinées de genre comiques."],
                     ]
        alignset = alig.normalize_set(alignset, treatments)
        targetset = alig.normalize_set(targetset, treatments)
        neighbours = alig.findneighbours_minhashing(alignset, targetset, indexes=(2, 2), threshold=0.4)
        for align in ([[2, 4], [1]], [[0], [0]], [[3], [2]]):
            self.assertIn(align, neighbours)

    def test_findneighbours_clustering(self):
        alignset = [['V1', 'label1', (6.14194444444, 48.67)],
                    ['V2', 'label2', (6.2, 49)],
                    ['V3', 'label3', (5.1, 48)],
                    ['V4', 'label4', (5.2, 48.1)],
                    ]
        targetset = [['T1', 'labelt1', (6.2, 48.9)],
                     ['T2', 'labelt2', (5.3, 48.2)],
                     ['T3', 'labelt3', (6.25, 48.91)],
                     ]
        neighbours = alig.findneighbours_clustering(alignset, targetset, indexes=(2, 2))
        for neighbour in neighbours:
            self.assertIn(neighbour, [[[0, 1], [0, 2]], [[2, 3], [1]]])

    def test_align(self):
        alignset = [['V1', 'label1', (6.14194444444, 48.67)],
                    ['V2', 'label2', (6.2, 49)],
                    ['V3', 'label3', (5.1, 48)],
                    ['V4', 'label4', (5.2, 48.1)],
                    ]
        targetset = [['T1', 'labelt1', (6.17, 48.7)],
                     ['T2', 'labelt2', (5.3, 48.2)],
                     ['T3', 'labelt3', (6.25, 48.91)],
                     ]
        treatments = {2: {'metric': 'geographical', 'matrix_normalized':False,
                          'metric_params': {'units': 'km', 'in_radians': False}}}
        mat, matched = alig.align(alignset, targetset, 30, treatments)
        true_matched = [(0,0), (0, 2), (1,2), (3,1)]
        for k, values in matched.iteritems():
            for v, distance in values:
                self.assertIn((k,v), true_matched)

    def test_neighbours_align(self):
        alignset = [['V1', 'label1', (6.14194444444, 48.67)],
                    ['V2', 'label2', (6.2, 49)],
                    ['V3', 'label3', (5.1, 48)],
                    ['V4', 'label4', (5.2, 48.1)],
                    ]
        targetset = [['T1', 'labelt1', (6.17, 48.7)],
                     ['T2', 'labelt2', (5.3, 48.2)],
                     ['T3', 'labelt3', (6.25, 48.91)],
                     ]
        true_matched = set([(0,0), (0, 2), (1,2), (3,1)])
        neighbours = alig.findneighbours_kdtree(alignset, targetset, indexes=(2, 2), threshold=0.3)
        treatments = {2: {'metric': 'geographical', 'matrix_normalized':False,
                          'metric_params': {'units': 'km', 'in_radians': False}}}
        predict_matched = set()
        for alignind, targetind in neighbours:
            mat, matched = alig.subalign(alignset, targetset, alignind, targetind, 30, treatments)
            for k, values in matched.iteritems():
                for v, distance in values:
                    predict_matched.add((k, v))
        self.assertEqual(predict_matched, true_matched)

    def test_divide_and_conquer_align(self):
        true_matched = set([(0,0), (0, 2), (1,2), (3,1)])
        alignset = [['V1', 'label1', (6.14194444444, 48.67)],
                    ['V2', 'label2', (6.2, 49)],
                    ['V3', 'label3', (5.1, 48)],
                    ['V4', 'label4', (5.2, 48.1)],
                    ]
        targetset = [['T1', 'labelt1', (6.17, 48.7)],
                     ['T2', 'labelt2', (5.3, 48.2)],
                     ['T3', 'labelt3', (6.25, 48.91)],
                     ]
        neighbours = alig.findneighbours_kdtree(alignset, targetset, indexes=(2, 2), threshold=0.3)
        treatments = {2: {'metric': 'geographical', 'matrix_normalized':False,
                          'metric_params': {'units': 'km', 'in_radians': False}}}
        global_mat, global_matched = alig.conquer_and_divide_alignment(alignset, targetset,
                                                                       threshold=30,
                                                                       treatments=treatments,
                                                                       indexes=(2,2),
                                                                       neighbours_threshold=0.3)
        predict_matched = set()
        for k, values in global_matched.iteritems():
            for v, distance in values:
                predict_matched.add((k, v))
        self.assertEqual(predict_matched, true_matched)

    def test_alignall(self):
        alignset = [['V1', 'label1', (6.14194444444, 48.67)],
                    ['V2', 'label2', (6.2, 49)],
                    ['V3', 'label3', (5.1, 48)],
                    ['V4', 'label4', (5.2, 48.1)],
                    ]
        targetset = [['T1', 'labelt1', (6.17, 48.7)],
                     ['T2', 'labelt2', (5.3, 48.2)],
                     ['T3', 'labelt3', (6.25, 48.91)],
                     ]
        all_matched = set([('V1','T1'), ('V1', 'T3'), ('V2','T3'), ('V4','T2')])
        uniq_matched = set([('V2', 'T3'), ('V4', 'T2'), ('V1', 'T1')])
        neighbours = alig.findneighbours_kdtree(alignset, targetset, indexes=(2, 2), threshold=0.3)
        treatments = {2: {'metric': 'geographical', 'matrix_normalized': False,
                          'metric_params': {'units': 'km', 'in_radians': False}}}

        predict_uniq_matched = set(alig.alignall(alignset, targetset,
                                                 threshold=30,
                                                 treatments=treatments,
                                                 indexes=(2,2),
                                                 neighbours_threshold=0.3,
                                                 uniq=True))
        predict_matched = set(alig.alignall(alignset, targetset,
                                            threshold=30,
                                            treatments=treatments,
                                            indexes=(2,2),
                                            neighbours_threshold=0.3,
                                            uniq=False))

        self.assertEqual(predict_matched, all_matched)
        self.assertEqual(predict_uniq_matched, uniq_matched)



if __name__ == '__main__':
    unittest2.main()

