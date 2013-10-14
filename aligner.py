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

from collections import defaultdict

from scipy import zeros
from scipy.sparse import lil_matrix


###############################################################################
### ALIGNER OBJECTS ###########################################################
###############################################################################
class BaseAligner(object):

    def __init__(self, threshold, processings):
        self.threshold = threshold
        self.processings = processings
        self.normalizers = None
        self.blocking = None

    def register_normalizers(self, normalizers):
        """ Register normalizers to be applied
        before alignment """
        self.normalizers = normalizers

    def apply_normalization(self, dataset):
        if self.normalizers:
            norm_pipeline = NormalizerPipeline(self.normalizers)
            return norm_pipeline.normalize_dataset(dataset)
        return dataset

    def register_blocking(self, blocking):
        self.blocking = blocking

    def compute_distance_matrix(self, refset, targetset,
                                ref_indexes, target_indexes):
        """ Compute and return the global alignment matrix.
        For each `processing` a `Distancematrix` is built, then all the
        matrices are summed with their own weighting and the result is the global
        alignment matrix, which is returned.
        """
        distmatrix = zeros((len(ref_indexes), len(target_indexes)), dtype='float32')
        for processing in self.processings:
            distmatrix += processing.cdist(refset, targetset,
                                          ref_indexes, target_indexes)
        return distmatrix

    def threshold_matched(self, distmatrix):
        """ Return the matched elements within a dictionnary,
        each key being the indice from X, and the corresponding
        values being a list of couple (indice from Y, distance)
        """
        match = defaultdict(list)
        # if normalized:
        #     distmatrix /= distmatrix.max()
        ind = (distmatrix <= self.threshold).nonzero()
        indrow = ind[0].tolist()
        indcol = ind[1].tolist()
        for (i, j) in zip(indrow, indcol):
            match[i].append((j, distmatrix[i, j]))
        return match

    def _get_match(self, refset, targetset, ref_indexes=None, target_indexes=None):
        # Build items
        items = []
        ref_indexes = ref_indexes or xrange(len(refset))
        target_indexes = target_indexes or xrange(len(targetset))
        # Apply alignments
        mat = self.compute_distance_matrix(refset, targetset,
                                           ref_indexes=ref_indexes,
                                           target_indexes=target_indexes)
        matched = self.threshold_matched(mat)
        # Reapply matched to global indexes
        new_matched = {}
        for k, values in matched.iteritems():
            new_matched[ref_indexes[k]] = [(target_indexes[i], d) for i, d in values]
        return mat, new_matched

    def align(self, refset, targetset, get_matrix=True):
        """ Perform the alignment on the referenceset
        and the targetset
        """
        refset = self.apply_normalization(refset)
        targetset = self.apply_normalization(targetset)
        # If no blocking
        if not self.blocking:
            return self._get_match(refset, targetset)
        # Blocking == conquer_and_divide
        global_matched = {}
        global_mat = lil_matrix((len(refset), len(targetset)))
        self.blocking.fit(refset, targetset)
        for refblock, targetblock in self.blocking.iter_blocks():
            _, matched = self._get_match(refset, targetset, refblock, targetblock)
            for k, values in matched.iteritems():
                subdict = global_matched.setdefault(k, set())
                for v, d in values:
                    subdict.add((v, d))
                    # XXX avoid issue in sparse matrix
                    if get_matrix:
                        global_mat[k, v] = d or 10**(-10)
        return global_mat, global_matched

    def get_aligned_pairs(self, refset, targetset, unique=True):
        """ Get the pairs of aligned elements
        """
        global_mat, global_matched = self.align(refset, targetset, False)
        if unique:
            for refid in global_matched:
                bestid, _ = sorted(global_matched[refid], key=lambda x:x[1])[0]
                yield refset[refid][0], targetset[bestid][0]
        else:
            for refid in global_matched:
                for targetid, _ in global_matched[refid]:
                    yield refset[refid][0], targetset[targetid][0]
