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

from cubes.alignment.distances import (levenshtein, soundex, soundexcode, \
                                       jaccard, temporal, euclidean)
from cubes.alignment.normalize import (lunormalize, loadlemmas, lemmatized, \
                                       roundstr, rgxformat, tokenize)

from cubes.alignment.matrix import Distancematrix

class DistancesTest(unittest2.TestCase):
    def test_levenshtein(self):
        self.assertEqual(levenshtein('niche', 'chiens'), 5)
        self.assertEqual(levenshtein('bonjour', 'bonjour !'), 2)
        self.assertEqual(levenshtein('bon', 'bonjour'), 4)

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
        self.assertAlmostEqual(jaccard('boujour', 'bonjour'), 0.166, 2)
        self.assertAlmostEqual(jaccard('rubert', 'robert'), 0.333, 2)

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

class NormalizerTestCase(unittest2.TestCase):
    def setUp(self):
        self.lemmas = loadlemmas('../data/french_lemmas.txt')

    def test_unormalize(self):
        self.assertEqual(lunormalize(u'bépoèàÀêùï'),
                                     u'bepoeaaeui')

    def test_tokenize(self):
        self.assertEqual(tokenize(u"J'aime les frites !"),
                         [u'J', u"'", u'aime', u'les', u'frites', u'!',])

    def test_lemmatizer(self):
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
        self.matrix = Distancematrix(self.input1, self.input2, self.distance)

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
        self.assertEqual(m.matched(), {1: [1]})

        #Victor Hugo --> Victor Wugo
        #Albert Camus --> Albert Camus, Albert Camu
        self.assertEqual(m.matched(cutoff = 0.1, normalized = True),
                        {0: [0], 1: [1, 2]})


if __name__ == '__main__':
    unittest2.main()
