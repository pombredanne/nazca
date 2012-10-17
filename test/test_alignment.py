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
from cubes.alignment.distances import (levenshtein, soundex)

class DistancesTest(testlib.CubicWebTC):
    def test_levenshtein(self):
        self.assertEqual(levenshtein('niche', 'chiens'), 5)
        self.assertEqual(levenshtein('bonjour', 'bonjour !'), 2)
        self.assertEqual(levenshtein('bon', 'bonjour'), 4)

    def test_soundex(self):
        self.assertEqual(soundex('Robert', 'english'), 'R163')
        self.assertEqual(soundex('Rubert', 'english'), 'R163')
        self.assertEqual(soundex('Rubin', 'english'), 'R150')
        self.assertEqual(soundex('Ashcraft', 'english'), 'A261')


if __name__ == '__main__':
    from logilab.common.testlib import unittest_main
    unittest_main()
