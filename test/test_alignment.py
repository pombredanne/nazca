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
import random
random.seed(6) ### Make sure tests are repeatable
from os import path

from nazca.normalize import simplify
import nazca.aligner as alig
import nazca.blocking as blo
from nazca.distances import GeographicalProcessing


TESTDIR = path.dirname(__file__)


class AlignerTestCase(unittest2.TestCase):

    def test_align(self):
        refset = [['V1', 'label1', (6.14194444444, 48.67)],
                  ['V2', 'label2', (6.2, 49)],
                  ['V3', 'label3', (5.1, 48)],
                  ['V4', 'label4', (5.2, 48.1)],
                  ]
        targetset = [['T1', 'labelt1', (6.17, 48.7)],
                     ['T2', 'labelt2', (5.3, 48.2)],
                     ['T3', 'labelt3', (6.25, 48.91)],
                     ]
        # Creation of the aligner object
        processings = (GeographicalProcessing(2, 2, units='km'),)
        aligner = alig.BaseAligner(threshold=30, processings=processings)
        mat, matched = aligner.align(refset, targetset)
        true_matched = [(0,0), (0, 2), (1,2), (3,1)]
        for k, values in matched.iteritems():
            for v, distance in values:
                self.assertIn((k,v), true_matched)

    def test_neighbours_align(self):
        refset = [['V1', 'label1', (6.14194444444, 48.67)],
                  ['V2', 'label2', (6.2, 49)],
                  ['V3', 'label3', (5.1, 48)],
                  ['V4', 'label4', (5.2, 48.1)],
                  ]
        targetset = [['T1', 'labelt1', (6.17, 48.7)],
                     ['T2', 'labelt2', (5.3, 48.2)],
                     ['T3', 'labelt3', (6.25, 48.91)],
                     ]
        # Creation of the aligner object
        true_matched = set([(0,0), (0, 2), (1,2), (3,1)])
        processings = (GeographicalProcessing(2, 2, units='km'),)
        aligner = alig.BaseAligner(threshold=30, processings=processings)
        blocking = blo.KdTreeBlocking(ref_attr_index=2,
                                      target_attr_index=2,
                                      threshold=0.3)
        blocking.fit(refset, targetset)
        predict_matched = set()
        for alignind, targetind in blocking.iter_blocks():
            mat, matched = aligner._get_match(refset, targetset, alignind, targetind)
            for k, values in matched.iteritems():
                for v, distance in values:
                    predict_matched.add((k, v))
        self.assertEqual(true_matched, predict_matched)

    def test_divide_and_conquer_align(self):
        refset = [['V1', 'label1', (6.14194444444, 48.67)],
                  ['V2', 'label2', (6.2, 49)],
                  ['V3', 'label3', (5.1, 48)],
                  ['V4', 'label4', (5.2, 48.1)],
                  ]
        targetset = [['T1', 'labelt1', (6.17, 48.7)],
                     ['T2', 'labelt2', (5.3, 48.2)],
                     ['T3', 'labelt3', (6.25, 48.91)],
                     ]
        # Creation of the aligner object
        true_matched = set([(0,0), (0, 2), (1,2), (3,1)])
        processings = (GeographicalProcessing(2, 2, units='km'),)
        aligner = alig.BaseAligner(threshold=30, processings=processings)
        aligner.register_blocking(blo.KdTreeBlocking(ref_attr_index=2,
                                                     target_attr_index=2,
                                                     threshold=0.3))
        global_mat, global_matched = aligner.align(refset, targetset)
        predict_matched = set()
        for k, values in global_matched.iteritems():
            for v, distance in values:
                predict_matched.add((k, v))
        self.assertEqual(true_matched, predict_matched)

    def test_alignall(self):
        refset = [['V1', 'label1', (6.14194444444, 48.67)],
                    ['V2', 'label2', (6.2, 49)],
                    ['V3', 'label3', (5.1, 48)],
                    ['V4', 'label4', (5.2, 48.1)],
                    ]
        targetset = [['T1', 'labelt1', (6.17, 48.7)],
                     ['T2', 'labelt2', (5.3, 48.2)],
                     ['T3', 'labelt3', (6.25, 48.91)],
                     ]
        all_matched = [('V1','T1'), ('V1', 'T3'), ('V2','T3'), ('V4','T2')]
        uniq_matched = [('V2', 'T3'), ('V4', 'T2'), ('V1', 'T1')]
        processings = (GeographicalProcessing(2, 2, units='km'),)
        aligner = alig.BaseAligner(threshold=30, processings=processings)
        aligner.register_blocking(blo.KdTreeBlocking(ref_attr_index=2,
                                                     target_attr_index=2,
                                                     threshold=0.3))
        unimatched = list(aligner.get_aligned_pairs(refset, targetset, unique=True))
        matched = list(aligner.get_aligned_pairs(refset, targetset, unique=False))
        self.assertEqual(len(matched), len(all_matched))
        for m in all_matched:
            self.assertIn(m, matched)
        self.assertEqual(len(unimatched), len(uniq_matched))
        for m in uniq_matched:
            self.assertIn(m, unimatched)


if __name__ == '__main__':
    unittest2.main()

