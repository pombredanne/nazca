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

from nazca.normalize import loadlemmas, simplify
from nazca.old_api import (normalize_set,
                           findneighbours_clustering,
                           findneighbours_kdtree,
                           findneighbours_minhashing,
                           align, subalign,
                           conquer_and_divide_alignment,
                           alignall, alignall_iterative)


TESTDIR = path.dirname(__file__)


# Backward compatibility. Now, use the BaseAligner inside the functions.
# Perhaps these functions may be removed later...


###############################################################################
### NORMALIZE TESTS ###########################################################
###############################################################################
class NormalizerFunctionTestCase(unittest2.TestCase):
    def test_normalize_set(self):
        processings = {1: {'normalization': [simplify,]}}

        alignlist = [['Label1', u"Un nuage flotta dans le grand ciel bleu."],
                     ['Label2', u"Pour quelle occasion vous êtes-vous apprêtée ?"],
                     ['Label3', u"Je les vis ensemble à plusieurs occasions."],
                     ['Label4', u"Je n'aime pas ce genre de bandes dessinées tristes."],
                     ['Label5', u"Ensemble et à plusieurs occasions, je les vis."],
                    ]
        aligntuple = [tuple(l) for l in alignlist]

        normalizedlist = normalize_set(alignlist, processings)
        normalizedtuple = normalize_set(aligntuple, processings)

        self.assertListEqual(normalizedlist, normalizedtuple)
        self.assertListEqual(normalizedlist,
                        [['Label1', u"nuage flotta grand ciel bleu"],
                         ['Label2', u"occasion êtes apprêtée"],
                         ['Label3', u"vis ensemble à plusieurs occasions"],
                         ['Label4', u"n aime genre bandes dessinées tristes"],
                         ['Label5', u"ensemble à plusieurs occasions vis"],
                        ])


###############################################################################
### ALIGNER TESTS #############################################################
###############################################################################
class AlignerFunctionsTestCase(unittest2.TestCase):

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
        processings = {2: {'metric': 'geographical', 'matrix_normalized':False,
                          'metric_params': {'units': 'km', 'in_radians': False}}}
        mat, matched = align(alignset, targetset, 30, processings)
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
        true_matched = set([((0, 'V1'), (0, 'T1')),
                           ((1, 'V2'), (2, 'T3')),
                           ((0, 'V1'), (2, 'T3')),
                           ((3, 'V4'), (1, 'T2'))])
        neighbours = findneighbours_kdtree(alignset, targetset, indexes=(2, 2), threshold=0.3)
        processings = {2: {'metric': 'geographical', 'matrix_normalized':False,
                          'metric_params': {'units': 'km', 'in_radians': False}}}
        predict_matched = set()
        for alignind, targetind in neighbours:
            mat, matched = subalign(alignset, targetset, alignind, targetind, 30, processings)
            for k, values in matched.iteritems():
                for v, distance in values:
                    predict_matched.add((k, v))
        self.assertEqual(true_matched, predict_matched)

    def test_divide_and_conquer_align(self):
        true_matched = set([((0, 'V1'), (0, 'T1')),
                            ((1, 'V2'), (2, 'T3')),
                            ((0, 'V1'), (2, 'T3')),
                            ((3, 'V4'), (1, 'T2'))])
        alignset = [['V1', 'label1', (6.14194444444, 48.67)],
                    ['V2', 'label2', (6.2, 49)],
                    ['V3', 'label3', (5.1, 48)],
                    ['V4', 'label4', (5.2, 48.1)],
                    ]
        targetset = [['T1', 'labelt1', (6.17, 48.7)],
                     ['T2', 'labelt2', (5.3, 48.2)],
                     ['T3', 'labelt3', (6.25, 48.91)],
                     ]
        processings = {2: {'metric': 'geographical', 'matrix_normalized':False,
                          'metric_params': {'units': 'km', 'in_radians': False}}}
        global_mat, global_matched = conquer_and_divide_alignment(alignset, targetset,
                                                                  threshold=30,
                                                                  processings=processings,
                                                                  indexes=(2,2),
                                                                  neighbours_threshold=0.3)
        predict_matched = set()
        for k, values in global_matched.iteritems():
            for v, distance in values:
                predict_matched.add((k, v))
        self.assertEqual(true_matched, predict_matched)

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
        processings = {2: {'metric': 'geographical', 'matrix_normalized': False,
                          'metric_params': {'units': 'km', 'in_radians': False}}}

        predict_uniq_matched = set(alignall(alignset, targetset,
                                            threshold=30,
                                            processings=processings,
                                            indexes=(2,2),
                                            neighbours_threshold=0.3,
                                            uniq=True))
        predict_matched = set(alignall(alignset, targetset,
                                       threshold=30,
                                       processings=processings,
                                       indexes=(2,2),
                                       neighbours_threshold=0.3,
                                       uniq=False))

        self.assertEqual(all_matched, predict_matched)
        self.assertEqual(uniq_matched, predict_uniq_matched)

    def test_alignall_iterative(self):
        matched = set([('V2', 'T3'), ('V4', 'T2'), ('V1', 'T1')])
        processings = {2: {'metric': 'geographical', 'matrix_normalized': False,
                          'metric_params': {'units': 'km', 'in_radians': False}}}

        _format={'indexes': [0, 1, (2, 3)]}
        alignements = alignall_iterative(path.join(TESTDIR, 'data',
                                                   'alignfile.csv'),
                                         path.join(TESTDIR, 'data',
                                                   'targetfile.csv'),
                                         _format, _format, threshold=30,
                                         size=2, #very small files ;)
                                         processings=processings,
                                         indexes=(2,2),
                                         neighbours_threshold=0.3)
        predict_matched = set([(a, t) for (a, (t, _)) in
                               alignements.iteritems()])
        self.assertEqual(matched, predict_matched)


###############################################################################
### NEIGHBOUR TESTS ###########################################################
###############################################################################
class NeigbhoursFunctionsTest(unittest2.TestCase):
    # For backward compatibility

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
        neighbours = findneighbours_kdtree(alignset, targetset, indexes=(2, 2), threshold=0.3)
        self.assertEqual([([(0, 'V1')], [(0, 'T1'), (2, 'T3')]),
                          ([(1, 'V2')], [(0, 'T1'), (2, 'T3')]),
                          ([(2, 'V3')], [(1, 'T2')]),
                          ([(3, 'V4')], [(1, 'T2')])], neighbours)

    def test_findneighbours_minhashing(self):
        lemmas = loadlemmas(path.join(TESTDIR, 'data', 'french_lemmas.txt'))
        processings = {2: {'normalization': [simplify,], 'norm_params': {'lemmas': lemmas}}}
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
        alignset = normalize_set(alignset, processings)
        targetset = normalize_set(targetset, processings)
        neighbours = findneighbours_minhashing(alignset, targetset, indexes=(2, 2), threshold=0.4)
        true_set = [([(0, 'V1')], [(0, 'T1')]), ([(3, 'V4')], [(2, 'T3')]),
                    ([(2, 'V3'), (4, 'V5')], [(1, 'T2')])]
        for align in true_set:
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
        try:
            import sklearn as skl
        except ImportError:
            self.skipTest('Scikit learn does not seem to be installed')
        if int(skl.__version__.split('-')[0].split('.')[1])<=11:
            self.skipTest('Scikit learn version is too old - Skipping test')
        neighbours = findneighbours_clustering(alignset, targetset, indexes=(2, 2))
        for neighbour in neighbours:
            self.assertIn(neighbour, [([0, 1], [0, 2]), ([2, 3], [1])])


if __name__ == '__main__':
    unittest2.main()

