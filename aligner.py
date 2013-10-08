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

from nazca.dataio import parsefile


###############################################################################
### BASE ALIGNER OBJECT #######################################################
###############################################################################
class BaseAligner(object):

    def __init__(self, threshold, processings, verbose=False):
        self.threshold = threshold
        self.processings = processings
        self.verbose = verbose
        self.ref_normalizer = None
        self.target_normalizer = None
        self.blocking = None
        self.nb_comparisons = 0

    def register_ref_normalizer(self, normalizer):
        """ Register normalizers to be applied
        before alignment """
        self.ref_normalizer = normalizer

    def register_target_normalizer(self, normalizer):
        """ Register normalizers to be applied
        before alignment """
        self.target_normalizer = normalizer

    def apply_normalization(self, dataset, normalizer):
        if normalizer:
            return normalizer.normalize_dataset(dataset)
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
        refset = self.apply_normalization(refset, self.ref_normalizer)
        targetset = self.apply_normalization(targetset, self.target_normalizer)
        # If no blocking
        if not self.blocking:
            return self._get_match(refset, targetset)
        # Blocking == conquer_and_divide
        global_matched = {}
        global_mat = lil_matrix((len(refset), len(targetset)))
        self.blocking.fit(refset, targetset)
        for refblock, targetblock in self.blocking.iter_blocks():
            ref_index = [r[0] for r in refblock]
            target_index = [r[0] for r in targetblock]
            self.nb_comparisons += len(ref_index)*len(target_index)
            if self.verbose:
                print 'Blocking: %s reference ids, %s target ids' % (len(ref_index),
                                                                     len(target_index))
                print 'Reference records :'
                for ind in ref_index:
                    print '\t--->', refset[ind]
                print 'Target records :'
                for ind in target_index:
                    print '\t--->', targetset[ind]
            _, matched = self._get_match(refset, targetset, ref_index, target_index)
            if self.verbose:
                print 'Matched: %s / Total comparisons %s' % (len(matched), self.nb_comparisons)
            for k, values in matched.iteritems():
                subdict = global_matched.setdefault(k, set())
                for v, d in values:
                    subdict.add((v, d))
                    if get_matrix:
                        # XXX avoid issue in sparse matrix
                        global_mat[k, v] = d or 10**(-10)
        return global_mat, global_matched

    def _iter_aligned_pairs(self, refset, targetset, global_mat, global_matched, unique=True):
        """ Return the aligned pairs
        """
        if unique:
            for refid in global_matched:
                bestid, _ = sorted(global_matched[refid], key=lambda x:x[1])[0]
                ref_record = refset[refid]
                target_record = targetset[bestid]
                if self.verbose:
                    print '\t\t', ref_record, ' <--> ', target_record
                yield (ref_record[0], refid), (target_record[0], bestid)
        else:
            for refid in global_matched:
                for targetid, _ in global_matched[refid]:
                    ref_record = refset[refid]
                    target_record = targetset[targetid]
                    if self.verbose:
                        print '\t\t', ref_record, ' <--> ', target_record
                    yield (ref_record[0], refid), (target_record[0], targetid)
        print 'Total comparisons : ', self.nb_comparisons

    def get_aligned_pairs(self, refset, targetset, unique=True):
        """ Get the pairs of aligned elements
        """
        global_mat, global_matched = self.align(refset, targetset, get_matrix=False)
        for pair in self._iter_aligned_pairs(refset, targetset, global_mat, global_matched, unique):
            yield pair

    def align_from_files(self, reffile, targetfile,
                         ref_indexes=None, target_indexes=None,
                         ref_encoding=None, target_encoding=None,
                         ref_separator='\t', target_separator='\t',
                         get_matrix=True):
        """ Align data from files

        Parameters
        ----------

        reffile: name of the reference file

        targetfile: name of the target file

        ref_encoding: if given (e.g. 'utf-8' or 'latin-1'), it will
                      be used to read the files.

        target_encoding: if given (e.g. 'utf-8' or 'latin-1'), it will
                         be used to read the files.

        ref_separator: separator of the reference file

        target_separator: separator of the target file
        """
        refset = parsefile(reffile, indexes=ref_indexes,
                           encoding=ref_encoding, delimiter=ref_separator)
        targetset = parsefile(targetfile, indexes=target_indexes,
                              encoding=target_encoding, delimiter=target_separator)
        return self.align(refset, targetset, get_matrix=get_matrix)

    def get_aligned_pairs_from_files(self, reffile, targetfile,
                         ref_indexes=None, target_indexes=None,
                         ref_encoding=None, target_encoding=None,
                         ref_separator='\t', target_separator='\t',
                         unique=True):
        """ Get the pairs of aligned elements
        """
        refset = parsefile(reffile, indexes=ref_indexes,
                           encoding=ref_encoding, delimiter=ref_separator)
        targetset = parsefile(targetfile, indexes=target_indexes,
                              encoding=target_encoding, delimiter=target_separator)
        global_mat, global_matched = self.align(refset, targetset, get_matrix=False)
        for pair in self._iter_aligned_pairs(refset, targetset, global_mat, global_matched, unique):
            yield pair


###############################################################################
### ITERATIVE ALIGNER OBJECT ##################################################
###############################################################################
class IterativePassAligner(object):
    """ This aligner may be used to perform multi pass of alignements.

        It takes your csv files as arguments and split them into smaller ones
        (files of `size` lines), and runs the alignment on those files.

        If the distance of an alignment is below `equality_threshold`, the
        alignment is considered as perfect, and the corresponding item is
        removed from the alignset (to speed up the computation).
    """

    def __init__(self, threshold, treatments, equality_threshold):
        self.threshold = threshold
        self.treatments = treatments
        self.equality_threshold = equality_threshold
        self.ref_normalizer = None
        self.target_normalizer = None
        self.blocking = None
