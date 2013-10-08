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
from nazca.distances import LevenshteinProcessing, GeographicalProcessing


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

    def test_blocking_align(self):
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
        for alignind, targetind in blocking.iter_indice_blocks():
            mat, matched = aligner._get_match(refset, targetset, alignind, targetind)
            for k, values in matched.iteritems():
                for v, distance in values:
                    predict_matched.add((k, v))
        self.assertEqual(true_matched, predict_matched)

    def test_blocking_align_2(self):
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

    def test_unique_align(self):
        refset = [['V1', 'label1', (6.14194444444, 48.67)],
                    ['V2', 'label2', (6.2, 49)],
                    ['V3', 'label3', (5.1, 48)],
                    ['V4', 'label4', (5.2, 48.1)],
                    ]
        targetset = [['T1', 'labelt1', (6.17, 48.7)],
                     ['T2', 'labelt2', (5.3, 48.2)],
                     ['T3', 'labelt3', (6.25, 48.91)],
                     ]
        all_matched = [(('V1', 0), ('T3', 2)), (('V1', 0), ('T1', 0)),
                       (('V2', 1), ('T3', 2)), (('V4', 3), ('T2', 1))]
        uniq_matched = [(('V1', 0), ('T1', 0)), (('V2', 1), ('T3', 2)), (('V4', 3), ('T2', 1))]
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

    def test_align_from_file(self):
        uniq_matched = [(('V1', 0), ('T1', 0)), (('V2', 1), ('T3', 2)), (('V4', 3), ('T2', 1))]
        processings = (GeographicalProcessing(2, 2, units='km'),)
        aligner = alig.BaseAligner(threshold=30, processings=processings)
        aligner.register_blocking(blo.KdTreeBlocking(ref_attr_index=2,
                                                     target_attr_index=2,
                                                     threshold=0.3))
        matched = list(aligner.get_aligned_pairs_from_files(path.join(TESTDIR, 'data',
                                                                      'alignfile.csv'),
                                                            path.join(TESTDIR, 'data',
                                                                      'targetfile.csv'),
                                                            ref_indexes=[0, 1, (2, 3)],
                                                            target_indexes=[0, 1, (2, 3)],))
        self.assertEqual(len(matched), len(uniq_matched))
        for m in uniq_matched:
            self.assertIn(m, matched)


class PipelineAlignerTestCase(unittest2.TestCase):

    def test_pipeline_align(self):
        refset = [['V1', 'aaa', (6.14194444444, 48.67)],
                  ['V2', 'bbb', (6.2, 49)],
                  ['V3', 'ccc', (5.1, 48)],
                  ['V4', 'ddd', (5.2, 48.1)],
                  ]
        targetset = [['T1', 'zzz', (6.17, 48.7)],
                     ['T2', 'eec', (5.3, 48.2)],
                     ['T3', 'fff', (6.25, 48.91)],
                     ['T4', 'ccd', (0, 0)],
                     ]
        # Creation of the aligner object
        processings = (GeographicalProcessing(2, 2, units='km'),)
        aligner_1 = alig.BaseAligner(threshold=30, processings=processings)
        processings = (LevenshteinProcessing(1, 1),)
        aligner_2 = alig.BaseAligner(threshold=1, processings=processings)
        pipeline = alig.PipelineAligner((aligner_1, aligner_2))
        global_mat, global_matched = pipeline.align(refset, targetset)
        true_global_matched =  {0: set([(2, 29.124842), (0, 4.5532517)]),
                                1: set([(2, 11.396689)]), 2: set([(3, 1.0)]),
                                3: set([(1, 15.69241)])}
        self.assertEqual(len(global_matched), len(true_global_matched))
        for k, v in true_global_matched.iteritems():
            self.assertIn(k, global_matched)
            self.assertEqual(len(v), len(global_matched[k]))

    def test_pipeline_align_pairs(self):
        refset = [['V1', 'aaa', (6.14194444444, 48.67)],
                  ['V2', 'bbb', (6.2, 49)],
                  ['V3', 'ccc', (5.1, 48)],
                  ['V4', 'ddd', (5.2, 48.1)],
                  ]
        targetset = [['T1', 'zzz', (6.17, 48.7)],
                     ['T2', 'eec', (5.3, 48.2)],
                     ['T3', 'fff', (6.25, 48.91)],
                     ['T4', 'ccd', (0, 0)],
                     ]
        # Creation of the aligner object
        processings = (GeographicalProcessing(2, 2, units='km'),)
        aligner_1 = alig.BaseAligner(threshold=30, processings=processings)
        processings = (LevenshteinProcessing(1, 1),)
        aligner_2 = alig.BaseAligner(threshold=1, processings=processings)
        pipeline = alig.PipelineAligner((aligner_1, aligner_2))
        uniq_matched = [(('V1', 0), ('T1', 0)), (('V2', 1), ('T3', 2)),
                        (('V4', 3), ('T2', 1)), (('V3', 2), ('T4', 3))]
        matched = list(pipeline.get_aligned_pairs(refset, targetset, unique=True))
        self.assertEqual(len(matched), len(uniq_matched))
        for m in uniq_matched:
            self.assertIn(m, matched)




if __name__ == '__main__':
    unittest2.main()

