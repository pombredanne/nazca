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


""" Blocking techniques.

This module implements a set of blocking techniques used to split
datasets in smaller subsets that will be aligned in more details.

Additional information:

   P. Christen, Data Matching, Data-Centric Systems and Applications,


"""
from functools import partial
import warnings

from scipy.spatial import KDTree

from nazca.minhashing import Minlsh
from nazca.distances import soundexcode


###############################################################################
### GENERAL BLOCKING ##########################################################
###############################################################################
class BaseBlocking(object):
    """ An abstract general blocking object that exposes
    the API that should be common to all blockings object
    """
    def __init__(self, ref_attr_index, target_attr_index):
        """ Build the blocking object

        Parameters
        ----------

        ref_attr_index: index of the attribute of interest in a record
                        for the reference dataset
                        (i.e. attribute to be used for key computation)

        target_attr_index: index of the attribute of interest in a record
                           for the target dataset
                           (i.e. attribute to be used for key computation)
        """
        self.ref_attr_index = ref_attr_index
        self.target_attr_index = target_attr_index
        self.refids = None
        self.targetids = None
        self.is_fitted = False

    def fit(self, refset, targetset):
        """ Fit the blocking technique on the reference and target datasets

        Parameters
        ----------
        refset: a dataset (list of records)

        targetset: a dataset (list of records)
        """
        self._fit(refset, targetset)
        # Keep ids for blocks building
        self.refids = [(i, r[0]) for i, r in enumerate(refset)]
        self.targetids = [(i, r[0]) for i, r in enumerate(targetset)]
        self.is_fitted = True

    def _fit(self, refset, targetset):
        raise NotImplementedError

    def iter_blocks(self):
        """ Iterator over the different possible blocks.

        Returns
        -------

        (block1, block2): The blocks are always (reference_block, target_block)
                          and contains the pair (index, id) of the record in the
                          corresponding dataset.
        """
        assert self.is_fitted
        return self._iter_blocks()

    def iter_indice_blocks(self):
        """ Iterator over the different possible blocks.

        Returns
        -------

        (block1, block2): The blocks are always (reference_block, target_block)
                          and contains the indexes of the record in the
                          corresponding dataset.
        """
        assert self.is_fitted
        for block1, block2 in self._iter_blocks():
            yield [r[0] for r in block1], [r[0] for r in block2]

    def iter_id_blocks(self):
        """ Iterator over the different possible blocks.

        Returns
        -------

        (block1, block2): The blocks are always (reference_block, target_block)
                          and contains the ids of the record in the
                          corresponding dataset.
        """
        assert self.is_fitted
        for block1, block2 in self._iter_blocks():
            yield [r[1] for r in block1], [r[1] for r in block2]


    def _iter_blocks(self):
        """ Internal iteration function over blocks
        """
        raise NotImplementedError

    def iter_pairs(self):
        """ Iterator over the different possible pairs.

        Returns
        -------

        (pair1, pari2): The pairs are always ((ind_reference, id_reference),
                                              (ind_target, id_target))
                        and are the ids of the record in the corresponding dataset.
        """
        assert self.is_fitted
        for block1, block2 in self.iter_blocks():
            for val1 in block1:
                for val2 in block2:
                    yield val1, val2

    def iter_indice_pairs(self):
        """ Iterator over the different possible pairs.

        Returns
        -------

        (pair1, pari2): The pairs are always (ind_reference, ind_target)
                        and are the ids of the record in the corresponding dataset.
        """
        assert self.is_fitted
        for block1, block2 in self.iter_indice_blocks():
            for val1 in block1:
                for val2 in block2:
                    yield val1, val2

    def iter_id_pairs(self):
        """ Iterator over the different possible pairs.

        Returns
        -------

        (pair1, pari2): The pairs are always (id_reference, id_target)
                        and are the ids of the record in the corresponding dataset.
        """
        assert self.is_fitted
        for block1, block2 in self.iter_id_blocks():
            for val1 in block1:
                for val2 in block2:
                    yield val1, val2


###############################################################################
### KEY BLOCKING ##############################################################
###############################################################################
class KeyBlocking(BaseBlocking):
    """ This blocking technique is based on a a blocking criteria
    (or blocking key), that will be used to divide the datasets.

    The main idea here is:

    1 - to create an index of f(x) for each x in the reference set.

    2 - to create an index of f(y) for each y in the target set.

    3 - to iterate on each distinct value of f(x) and to return
        the identifiers of the records of the both sets for this value.
    """

    def __init__(self, ref_attr_index, target_attr_index, callback):
        super(KeyBlocking, self).__init__(ref_attr_index, target_attr_index)
        self.callback = callback
        self.reference_index = {}
        self.target_index = {}

    def _fit(self, refset, targetset):
        """ Fit a dataset in an index using the callback
        """
        for ind, rec in enumerate(refset):
            key = self.callback(rec[self.ref_attr_index])
            self.reference_index.setdefault(key, []).append((ind, rec[0]))
        for ind, rec in enumerate(targetset):
            key = self.callback(rec[self.target_attr_index])
            self.target_index.setdefault(key, []).append((ind, rec[0]))

    def _iter_blocks(self):
        """ Iterator over the different possible blocks.

        Returns
        -------

        (block1, block2): The blocks are always (reference_block, target_block)
                          and containts the indexes of the record in the
                          corresponding dataset.
        """
        for key, block1 in self.reference_index.iteritems():
            block2 = self.target_index.get(key)
            if block1 and block2:
                yield (block1, block2)


class SoundexBlocking(KeyBlocking):

    def __init__(self, ref_attr_index, target_attr_index, language='french',):
        super(SoundexBlocking, self).__init__(ref_attr_index, target_attr_index,
                                              partial(soundexcode, language=language))


###############################################################################
### BIGRAM BLOCKING ###########################################################
###############################################################################
class NGramBlocking(BaseBlocking):
    """ This blocking technique is based on a a n-gram key.
    """

    def __init__(self, ref_attr_index, target_attr_index, ngram_size=2, depth=2):
        super(NGramBlocking, self).__init__(ref_attr_index, target_attr_index)
        self.ngram_size = ngram_size
        self.depth = depth
        self.reference_index = {}
        self.target_index = {}

    def _fit_dataset(self, dataset, cur_index, attr_index):
        """ Fit a dataset
        """
        for ind, r in enumerate(dataset):
            cur_dict = cur_index
            text = r[attr_index]
            for i in range(self.depth):
                ngram = text[i*self.ngram_size:(i+1)*self.ngram_size]
                if i < self.depth - 1:
                    cur_dict = cur_dict.setdefault(ngram, {})
            cur_dict.setdefault(ngram, []).append((ind, r[0]))

    def _fit(self, refset, targetset):
        """ Fit the two sets (reference set and target set)
        """
        self._fit_dataset(refset, self.reference_index, self.ref_attr_index)
        self._fit_dataset(targetset, self.target_index, self.target_attr_index)

    def _iter_dict(self, ref_cur_dict, target_cur_dict):
        """ Iterative function used to create blocks from dicts
        """
        for key, sub_dict in ref_cur_dict.iteritems():
            if key in target_cur_dict:
                if isinstance(sub_dict, dict):
                    # There is another dict layer
                    for block1, block2 in self._iter_dict(sub_dict, target_cur_dict[key]):
                        yield block1, block2
                else:
                    # This is a list
                    yield sub_dict, target_cur_dict[key]

    def _iter_blocks(self):
        """ Iterator over the different possible blocks.

        Returns
        -------

        (block1, block2): The blocks are always (reference_block, target_block)
                          and containts the indexes of the record in the
                          corresponding dataset.
        """
        for block1, block2 in self._iter_dict(self.reference_index, self.target_index):
            if block1 and block2:
                yield block1, block2


###############################################################################
### SORTKEY BLOCKING ##########################################################
###############################################################################
class SortedNeighborhoodBlocking(BaseBlocking):
    """ This blocking technique is based on a a sorting blocking criteria
    (or blocking key), that will be used to divide the datasets.
    """

    def __init__(self, ref_attr_index, target_attr_index, key_func=lambda x: x, window_width=20):
        super(SortedNeighborhoodBlocking, self).__init__(ref_attr_index, target_attr_index)
        self.key_func = key_func
        self.window_width = window_width
        self.sorted_dataset = None

    def _fit(self, refset, targetset):
        """ Fit a dataset in an index using the callback
        """
        self.sorted_dataset = [((ind, r[0]), r[self.ref_attr_index], 0)
                               for ind, r in enumerate(refset)]
        self.sorted_dataset.extend([((ind, r[0]), r[self.target_attr_index], 1)
                                    for ind, r in enumerate(targetset)])
        self.sorted_dataset.sort(key=lambda x: self.key_func(x[1]))

    def _iter_blocks(self):
        """ Iterator over the different possible blocks.
        """
        for ind, (rid, record, dset) in enumerate(self.sorted_dataset):
            # Only keep reference set record
            if dset == 1:
                continue
            block1 = [rid,]
            minind = (ind - self.window_width)
            minind = minind if minind >=0 else 0
            maxind = (ind + self.window_width + 1)
            block2 = [ri for ri, re, d in self.sorted_dataset[minind:maxind]
                      if d == 1]
            if block1 and block2:
                yield (block1, block2)


###############################################################################
### CLUSTERING-BASED BLOCKINGS ################################################
###############################################################################
class KmeansBlocking(BaseBlocking):
    """ A blocking technique based on Kmeans
    """

    def __init__(self, ref_attr_index, target_attr_index, n_clusters=None):
        super(KmeansBlocking, self).__init__(ref_attr_index, target_attr_index)
        self.n_clusters = n_clusters
        self.kmeans = None
        self.predicted = None
        from sklearn import cluster
        self.cluster_class = cluster.KMeans

    def _fit(self, refset, targetset):
        """ Fit the reference dataset.
        """
        # If an element is None (missing), use instead the identity element.
        # The identity element is defined as the 0-vector
        idelement = tuple([0 for _ in xrange(len(refset[0][self.ref_attr_index]))])
        # We assume here that there are at least 2 elements in the refset
        n_clusters = self.n_clusters or (len(refset)/10 or len(refset)/2)
        kmeans =  self.cluster_class(n_clusters=n_clusters)
        kmeans.fit([elt[self.ref_attr_index] or idelement for elt in refset])
        self.kmeans = kmeans
        # Predict on targetset
        self.predicted = self.kmeans.predict([elt[self.target_attr_index]
                                              or idelement for elt in targetset])

    def _iter_blocks(self):
        """ Iterator over the different possible blocks.

        Returns
        -------

        (block1, block2): The blocks are always (reference_block, target_block)
                          and containts the indexes of the record in the
                          corresponding dataset.
        """
        neighbours = [[[], []] for _ in xrange(self.kmeans.n_clusters)]
        for ind, li in enumerate(self.predicted):
            neighbours[li][1].append(self.targetids[ind])
        for ind, li in enumerate(self.kmeans.labels_):
            neighbours[li][0].append(self.refids[ind])
        for block1, block2 in neighbours:
            if len(block1) and len(block2):
                yield block1, block2


###############################################################################
### KDTREE BLOCKINGS ##########################################################
###############################################################################
class KdTreeBlocking(BaseBlocking):
    """ A blocking technique based on KdTree
    """
    def __init__(self, ref_attr_index, target_attr_index, threshold=0.1):
        super(KdTreeBlocking, self).__init__(ref_attr_index, target_attr_index)
        self.threshold = threshold
        self.reftree = None
        self.targettree = None
        self.nb_elements = None

    def _fit(self, refset, targetset):
        """ Fit the blocking
        """
        firstelement = refset[0][self.ref_attr_index]
        self.nb_elements = len(refset)
        idsize = len(firstelement) if isinstance(firstelement, (tuple, list)) else 1
        idelement = (0,) * idsize
        # KDTree is expecting a two-dimensional array
        if idsize == 1:
            self.reftree  = KDTree([(elt[self.ref_attr_index],) or idelement for elt in refset])
            self.targettree = KDTree([(elt[self.target_attr_index],) or idelement for elt in targetset])
        else:
            self.reftree = KDTree([elt[self.ref_attr_index] or idelement for elt in refset])
            self.targettree = KDTree([elt[self.target_attr_index] or idelement for elt in targetset])

    def _iter_blocks(self):
        """ Iterator over the different possible blocks.

        Returns
        -------

        (block1, block2): The blocks are always (reference_block, target_block)
                          and containts the indexes of the record in the
                          corresponding dataset.
        """
        extraneighbours = self.reftree.query_ball_tree(self.targettree, self.threshold)
        neighbours = []
        for ind in xrange(self.nb_elements):
            if not extraneighbours[ind]:
                continue
            _ref = [self.refids[ind],]
            _target = [self.targetids[v] for v in extraneighbours[ind]]
            neighbours.append((_ref, _target))
        for block1, block2 in neighbours:
            if len(block1) and len(block2):
                yield block1, block2


###############################################################################
### MINHASHING BLOCKINGS ######################################################
###############################################################################
class MinHashingBlocking(BaseBlocking):
    """ A blocking technique based on MinHashing
    """
    def __init__(self, ref_attr_index, target_attr_index,
                 threshold=0.1, kwordsgram=1, siglen=200):
        super(MinHashingBlocking, self).__init__(ref_attr_index, target_attr_index)
        self.threshold = threshold
        self.kwordsgram = kwordsgram
        self.siglen = siglen
        self.minhasher = Minlsh()
        self.nb_elements = None

    def _fit(self, refset, targetset):
        """ Find the blocking using minhashing
        """
        # If an element is None (missing), use instead the identity element.
        idelement = ''
        self.minhasher.train([elt[self.ref_attr_index] or idelement for elt in refset] +
                        [elt[self.target_attr_index] or idelement for elt in targetset],
                        self.kwordsgram, self.siglen)
        self.nb_elements = len(refset)

    def _iter_blocks(self):
        """ Iterator over the different possible blocks.

        Returns
        -------

        (block1, block2): The blocks are always (reference_block, target_block)
                          and containts the indexes of the record in the
                          corresponding dataset.
        """
        rawneighbours = self.minhasher.predict(self.threshold)
        neighbours = []
        for data in rawneighbours:
            neighbours.append([[], []])
            for i in data:
                if i >= self.nb_elements:
                    neighbours[-1][1].append(self.targetids[i - self.nb_elements])
                else:
                    neighbours[-1][0].append(self.refids[i])
            if len(neighbours[-1][0]) == 0 or len(neighbours[-1][1]) == 0:
                neighbours.pop()
        for block1, block2 in neighbours:
            if len(block1) and len(block2):
                yield block1, block2
