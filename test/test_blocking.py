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
from functools import partial
import random
random.seed(6) ### Make sure tests are repeatable / Minhashing

from nazca.distances import (levenshtein, soundex, soundexcode,   \
                             jaccard, euclidean, geographical)
from nazca.blocking import (KeyBlocking, SortedNeighborhoodBlocking,
                            NGramBlocking, PipelineBlocking,
                            SoundexBlocking, KmeansBlocking,
                            MinHashingBlocking, KdTreeBlocking)
from nazca.normalize import SimplifyNormalizer, loadlemmas


TESTDIR = path.dirname(__file__)

SOUNDEX_REFSET = (('a1', 'smith'),
                  ('a2', 'neighan'),
                  ('a3', 'meier'),
                  ('a4', 'smithers'),
                  ('a5', 'nguyen'),
                  ('a6', 'faulkner'),
                  ('a7', 'sandy'))
SOUNDEX_TARGETSET = (('b1', 'meier'),
                     ('b2', 'meier'),
                     ('b3', 'smith'),
                     ('b4', 'nguyen'),
                     ('b5', 'fawkner'),
                     ('b6', 'santi'),
                     ('b7', 'cain'))
SOUNDEX_PAIRS = (('a3', 'b1'),
                 ('a3', 'b2'),
                 ('a2', 'b4'),
                 ('a5', 'b4'),
                 ('a1', 'b3'),
                 ('a1', 'b6'),
                 ('a7', 'b3'),
                 ('a7', 'b6'),)


class BaseBlockingTest(unittest2.TestCase):

    def test_baseblocking_blocks(self):
        blocking = KeyBlocking(ref_attr_index=1, target_attr_index=1,
                               callback=partial(soundexcode, language='english'))
        blocking.fit(SOUNDEX_REFSET, SOUNDEX_TARGETSET)
        blocks = list(blocking.iter_blocks())
        self.assertEqual(len(blocks), 3)
        self.assertIn(([(0, 'a1'), (6, 'a7')], [(2, 'b3'), (5, 'b6')]), blocks)
        self.assertIn(([(1, 'a2'), (4, 'a5')], [(3, 'b4')]), blocks)
        self.assertIn(([(2, 'a3')], [(0, 'b1'), (1, 'b2')]), blocks)

    def test_baseblocking_id_blocks(self):
        blocking = KeyBlocking(ref_attr_index=1, target_attr_index=1,
                               callback=partial(soundexcode, language='english'))
        blocking.fit(SOUNDEX_REFSET, SOUNDEX_TARGETSET)
        blocks = list(blocking.iter_id_blocks())
        self.assertEqual(len(blocks), 3)
        self.assertIn((['a1', 'a7'], ['b3', 'b6']), blocks)
        self.assertIn((['a2', 'a5'], ['b4']), blocks)
        self.assertIn((['a3'], ['b1', 'b2']), blocks)

    def test_baseblocking_indice_blocks(self):
        blocking = KeyBlocking(ref_attr_index=1, target_attr_index=1,
                               callback=partial(soundexcode, language='english'))
        blocking.fit(SOUNDEX_REFSET, SOUNDEX_TARGETSET)
        blocks = list(blocking.iter_indice_blocks())
        self.assertEqual(len(blocks), 3)
        self.assertIn(([0, 6], [2, 5]), blocks)
        self.assertIn(([1, 4], [3]), blocks)
        self.assertIn(([2], [0, 1]), blocks)

    def test_baseblocking_pairs(self):
        blocking = KeyBlocking(ref_attr_index=1, target_attr_index=1,
                               callback=partial(soundexcode, language='english'))
        blocking.fit(SOUNDEX_REFSET, SOUNDEX_TARGETSET)
        pairs = list(blocking.iter_pairs())
        ref_ind = dict((r[0], ind) for ind, r in enumerate(SOUNDEX_REFSET))
        target_ind = dict((r[0], ind) for ind, r in enumerate(SOUNDEX_TARGETSET))
        true_pairs = [((ref_ind[r[0]], r[0]), (target_ind[r[1]], r[1])) for r in SOUNDEX_PAIRS]
        self.assertEqual(len(pairs), len(true_pairs))
        for pair in true_pairs:
            self.assertIn(pair, pairs)

    def test_baseblocking_id_pairs(self):
        blocking = KeyBlocking(ref_attr_index=1, target_attr_index=1,
                               callback=partial(soundexcode, language='english'))
        blocking.fit(SOUNDEX_REFSET, SOUNDEX_TARGETSET)
        pairs = list(blocking.iter_id_pairs())
        true_pairs = SOUNDEX_PAIRS
        self.assertEqual(len(pairs), len(true_pairs))
        for pair in true_pairs:
            self.assertIn(pair, pairs)

    def test_baseblocking_indice_pairs(self):
        blocking = KeyBlocking(ref_attr_index=1, target_attr_index=1,
                               callback=partial(soundexcode, language='english'))
        blocking.fit(SOUNDEX_REFSET, SOUNDEX_TARGETSET)
        pairs = list(blocking.iter_indice_pairs())
        ref_ind = dict((r[0], ind) for ind, r in enumerate(SOUNDEX_REFSET))
        target_ind = dict((r[0], ind) for ind, r in enumerate(SOUNDEX_TARGETSET))
        true_pairs = [(ref_ind[r[0]], target_ind[r[1]]) for r in SOUNDEX_PAIRS]
        self.assertEqual(len(pairs), len(true_pairs))
        for pair in true_pairs:
            self.assertIn(pair, pairs)


class KeyBlockingTest(unittest2.TestCase):

    def test_keyblocking_blocks(self):
        blocking = KeyBlocking(ref_attr_index=1, target_attr_index=1,
                               callback=partial(soundexcode, language='english'))
        blocking.fit(SOUNDEX_REFSET, SOUNDEX_TARGETSET)
        blocks = list(blocking.iter_id_blocks())
        self.assertEqual(len(blocks), 3)
        self.assertIn((['a1', 'a7'], ['b3', 'b6']), blocks)
        self.assertIn((['a2', 'a5'], ['b4']), blocks)
        self.assertIn((['a3'], ['b1', 'b2']), blocks)

    def test_keyblocking_couples(self):
        blocking = KeyBlocking(ref_attr_index=1, target_attr_index=1,
                               callback=partial(soundexcode, language='english'))
        blocking.fit(SOUNDEX_REFSET, SOUNDEX_TARGETSET)
        pairs = list(blocking.iter_id_pairs())
        self.assertEqual(len(pairs), 8)
        for pair in SOUNDEX_PAIRS:
            self.assertIn(pair, pairs)

    def test_soundex_blocks(self):
        blocking = SoundexBlocking(ref_attr_index=1, target_attr_index=1,
                                   language='english')
        blocking.fit(SOUNDEX_REFSET, SOUNDEX_TARGETSET)
        blocks = list(blocking.iter_id_blocks())
        self.assertEqual(len(blocks), 3)
        self.assertIn((['a1', 'a7'], ['b3', 'b6']), blocks)
        self.assertIn((['a2', 'a5'], ['b4']), blocks)
        self.assertIn((['a3'], ['b1', 'b2']), blocks)

    def test_soundex_couples(self):
        blocking = SoundexBlocking(ref_attr_index=1, target_attr_index=1,
                                   language='english')
        blocking.fit(SOUNDEX_REFSET, SOUNDEX_TARGETSET)
        pairs = list(blocking.iter_id_pairs())
        self.assertEqual(len(pairs), 8)
        for pair in SOUNDEX_PAIRS:
            self.assertIn(pair, pairs)


class NGramBlockingTest(unittest2.TestCase):

    def test_ngram_blocks(self):
        blocking = NGramBlocking(ref_attr_index=1, target_attr_index=1)
        blocking.fit(SOUNDEX_REFSET, SOUNDEX_TARGETSET)
        blocks = list(blocking.iter_id_blocks())
        self.assertEqual(len(blocks), 3)
        self.assertIn((['a3'], ['b1', 'b2']), blocks)
        self.assertIn((['a5'], ['b4']), blocks)
        self.assertIn((['a1', 'a4'], ['b3']), blocks)

    def test_ngram_blocks_depth(self):
        blocking = NGramBlocking(ref_attr_index=1, target_attr_index=1, depth=1)
        blocking.fit(SOUNDEX_REFSET, SOUNDEX_TARGETSET)
        blocks = list(blocking.iter_id_blocks())
        self.assertEqual(len(blocks), 5)
        self.assertIn((['a3'], ['b1', 'b2']), blocks)
        self.assertIn((['a5'], ['b4']), blocks)
        self.assertIn((['a6'], ['b5']), blocks)
        self.assertIn((['a7'], ['b6']), blocks)
        self.assertIn((['a1', 'a4'], ['b3']), blocks)

    def test_ngram_blocks_2(self):
        refset = [['3', 'ccdd', 'aabb'],
                  ['4', 'ccdd', 'bbaa']]
        targetset = [['c', 'ccdd', 'aabb'],
                     ['d', 'ccdd', 'bbaa']]
        true_pairs = [('3', 'c'), ('4', 'd')]
        blocking = NGramBlocking(ref_attr_index=2, target_attr_index=2,
                                   ngram_size=2, depth=1)
        blocking.fit(refset, targetset)
        pairs = list(blocking.iter_id_pairs())
        self.assertEqual(len(pairs), len(true_pairs))


class SortedNeighborhoodBlockingTest(unittest2.TestCase):

    def test_sorted_neighborhood_blocks(self):
        blocking = SortedNeighborhoodBlocking(ref_attr_index=1, target_attr_index=1,
                                              window_width=1)
        blocking.fit(SOUNDEX_REFSET, SOUNDEX_TARGETSET)
        blocks = list(blocking.iter_id_blocks())
        true_blocks = [(['a6'], ['b7', 'b5']), (['a3'], ['b5', 'b1']),
                       (['a2'], ['b2']), (['a5'], ['b4']), (['a7'], ['b4', 'b6']),
                       (['a1'], ['b6', 'b3']), (['a4'], ['b3'])]
        self.assertEqual(len(blocks), len(true_blocks))
        for block in true_blocks:
            self.assertIn(block, blocks)

    def test_sorted_neighborhood_keyfunc(self):
        """ Test sort reversing values
        """
        blocking = SortedNeighborhoodBlocking(ref_attr_index=1, target_attr_index=1,
                                              key_func=lambda x:x[::-1], window_width=1)
        blocking.fit(SOUNDEX_REFSET, SOUNDEX_TARGETSET)
        blocks = list(blocking.iter_id_blocks())
        true_blocks = [(['a1'], ['b3']), (['a2'], ['b6']), (['a5'], ['b4']), (['a3'], ['b7', 'b1']),
                       (['a6'], ['b2', 'b5']), (['a4'], ['b5'])]
        self.assertEqual(len(blocks), len(true_blocks))
        for block in true_blocks:
            self.assertIn(block, blocks)


class KmeansBlockingTest(unittest2.TestCase):

    def test_clustering_blocking_kmeans(self):
        refset = [['V1', 'label1', (6.14194444444, 48.67)],
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
            self.skiptTest('Scikit learn does not seem to be installed')
        if int(skl.__version__.split('-')[0].split('.')[1])<=11:
            self.skipTest('Scikit learn version is too old - Skipping test')
        blocking = KmeansBlocking(ref_attr_index=2, target_attr_index=2)
        blocking.fit(refset, targetset)
        # Blocks
        blocks = list(blocking.iter_indice_blocks())
        self.assertEqual(len(blocks), 2)
        self.assertIn(([0, 1], [0, 2]), blocks)
        self.assertIn(([2, 3], [1]), blocks)
        # Pairs
        pairs = list(blocking.iter_indice_pairs())
        self.assertEqual(len(pairs), 6)
        for pair in ((0, 0), (0, 2), (1, 0), (1, 2), (2, 1), (3, 1)):
            self.assertIn(pair, pairs)


class MinHashingBlockingTest(unittest2.TestCase):

    def test_minhashing(self):
        refset = [['V1', 'label1', u"Un nuage flotta dans le grand ciel bleu."],
                  ['V2', 'label2', u"Pour quelle occasion vous êtes-vous apprêtée ?"],
                  ['V3', 'label3', u"Je les vis ensemble à plusieurs occasions."],
                  ['V4', 'label4', u"Je n'aime pas ce genre de bandes dessinées tristes."],
                  ['V5', 'label5', u"Ensemble et à plusieurs occasions, je les vis."],
                  ]
        targetset = [['T1', 'labelt1', u"Des grands nuages noirs flottent dans le ciel."],
                     ['T2', 'labelt2', u"Je les ai vus ensemble à plusieurs occasions."],
                     ['T3', 'labelt3', u"J'aime les bandes dessinées de genre comiques."],
                     ]
        lemmas = loadlemmas(path.join(TESTDIR, 'data', 'french_lemmas.txt'))
        normalizer = SimplifyNormalizer(attr_index=2, lemmas=lemmas)
        refset = normalizer.normalize_dataset(refset)
        targetset = normalizer.normalize_dataset(targetset)
        blocking = MinHashingBlocking(threshold=0.4, ref_attr_index=2, target_attr_index=2)
        blocking.fit(refset, targetset)
        blocks = list(blocking.iter_indice_blocks())
        for align in (([2, 4], [1]), ([0], [0]), ([3], [2])):
            self.assertIn(align, blocks)


class KdTreeBlockingTest(unittest2.TestCase):

    def test_kdtree(self):
        refset = [['V1', 'label1', (6.14194444444, 48.67)],
                  ['V2', 'label2', (6.2, 49)],
                  ['V3', 'label3', (5.1, 48)],
                  ['V4', 'label4', (5.2, 48.1)],
                  ]
        targetset = [['T1', 'labelt1', (6.2, 48.9)],
                     ['T2', 'labelt2', (5.3, 48.2)],
                     ['T3', 'labelt3', (6.25, 48.91)],
                     ]
        blocking = KdTreeBlocking(threshold=0.3, ref_attr_index=2, target_attr_index=2)
        blocking.fit(refset, targetset)
        blocks = list(blocking.iter_id_blocks())
        self.assertEqual([(['V1'], ['T1', 'T3']),
                          (['V2'], ['T1', 'T3']),
                          (['V3'], ['T2']),
                          (['V4'], ['T2'])], blocks)


class PipelineBlockingTest(unittest2.TestCase):

    def test_pipeline_blocking(self):
        refset = [['1', 'aabb', 'ccdd'],
                  ['2', 'aabb', 'ddcc'],
                  ['3', 'ccdd', 'aabb'],
                  ['4', 'ccdd', 'bbaa']]
        targetset = [['a', 'aabb', 'ccdd'],
                     ['b', 'aabb', 'ddcc'],
                     ['c', 'ccdd', 'aabb'],
                     ['d', 'ccdd', 'bbaa']]
        true_pairs = [((0, '1'), (0, 'a')), ((1, '2'), (1, 'b')), ((2, '3'), (2, 'c')), ((3, '4'), (3, 'd'))]
        blocking_1 = NGramBlocking(ref_attr_index=1, target_attr_index=1,
                                   ngram_size=2, depth=1)
        blocking_2 = NGramBlocking(ref_attr_index=2, target_attr_index=2,
                                   ngram_size=2, depth=1)
        blocking = PipelineBlocking((blocking_1, blocking_2))
        blocking.fit(refset, targetset)
        pairs = list(blocking.iter_pairs())
        self.assertEqual(len(pairs), len(true_pairs))
        for pair in true_pairs:
            self.assertIn(pair, pairs)

    def test_pipeline_id_blocking(self):
        refset = [['1', 'aabb', 'ccdd'],
                  ['2', 'aabb', 'ddcc'],
                  ['3', 'ccdd', 'aabb'],
                  ['4', 'ccdd', 'bbaa']]
        targetset = [['a', 'aabb', 'ccdd'],
                     ['b', 'aabb', 'ddcc'],
                     ['c', 'ccdd', 'aabb'],
                     ['d', 'ccdd', 'bbaa']]
        true_pairs = [('1', 'a'), ('2', 'b'), ('3', 'c'), ('4', 'd')]
        blocking_1 = NGramBlocking(ref_attr_index=1, target_attr_index=1,
                                   ngram_size=2, depth=1)
        blocking_2 = NGramBlocking(ref_attr_index=2, target_attr_index=2,
                                   ngram_size=2, depth=1)
        blocking = PipelineBlocking((blocking_1, blocking_2))
        blocking.fit(refset, targetset)
        pairs = list(blocking.iter_id_pairs())
        self.assertEqual(len(pairs), len(true_pairs))
        for pair in true_pairs:
            self.assertIn(pair, pairs)





if __name__ == '__main__':
    unittest2.main()
