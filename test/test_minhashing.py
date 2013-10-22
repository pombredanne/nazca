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

import unittest2
from os import path
import random
random.seed(6) ### Make sure tests are repeatable

from nazca.normalize import loadlemmas, simplify
from nazca.minhashing import Minlsh

TESTDIR = path.dirname(__file__)



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
        self.assertEqual(set([(0, 1), (2, 3), (5,6)]), minlsh.predict(0.4))


if __name__ == '__main__':
    unittest2.main()

