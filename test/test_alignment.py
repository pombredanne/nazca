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

from cubicweb.devtools import testlib
from cubes.alignment.distances import (levenshtein, soundex, soundexcode, \
                                       jaccard)

class DistancesTest(testlib.CubicWebTC):
    def test_levenshtein(self):
        self.assertEqual(levenshtein('niche', 'chiens'), 5)
        self.assertEqual(levenshtein('bonjour', 'bonjour !'), 2)
        self.assertEqual(levenshtein('bon', 'bonjour'), 4)

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

        self.assertEqual(soundex('Rubert', 'Robert', 'english'), 1)
        self.assertEqual(soundex('Rubin', 'Robert', 'english'), 0)

    def test_jaccard(self):
        #The jaccard indice between two words is the ratio of the number of
        #identical letters and the total number of letters
        #Each letter is counted once only
        #The distance is 1 - jaccard_indice

        self.assertEqual(jaccard('bonjour', 'bonjour'), 0.0)
        self.assertAlmostEqual(jaccard('boujour', 'bonjour'), 0.166, 2)
        self.assertAlmostEqual(jaccard('rubert', 'robert'), 0.333, 2)

if __name__ == '__main__':
    from logilab.common.testlib import unittest_main
    unittest_main()
