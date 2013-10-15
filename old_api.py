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

from os import listdir
import os.path as osp
from shutil import rmtree
from tempfile import mkdtemp
import sys
import warnings
from functools import partial

from scipy.sparse import lil_matrix

from nazca.dataio import write_results, split_file, parsefile
from nazca.normalize import BaseNormalizer, NormalizerPipeline
from nazca.blocking import KmeansBlocking, KdTreeBlocking, MinHashingBlocking
from nazca.distances import GeographicalProcessing
from nazca.aligner import BaseAligner


# Backward compatibility. Now, use the BaseAligner inside the functions.
# Perhaps these functions may be removed later...


###############################################################################
### NORMALIZE FUNCTIONS #######################################################
###############################################################################
# Backward compatibility. Now, use the NormalizerPipeline inside the functions.
# Perhaps these functions may be removed later...

def normalize_set(rset, processings):
    """ Apply all the normalization functions to the given rset """
    warnings.warn(DeprecationWarning('This function will be removed '
                                     'in the next release.'
                                     'You should rather use the BaseNormalizer '
                                     'object of the normalize module'))
    normalizers = []
    for ind, processing in processings.iteritems():
        for normalizer in extract_normalization_from_treatment(processing, ind):
            normalizers.append(normalizer)
    # Create pipeline
    pipeline = NormalizerPipeline(normalizers)
    return pipeline.normalize_dataset(rset)

def extract_normalization_from_treatment(processing, ind):
    """ Extract normalization from processing.
    This function is used for backward compatibility with
    the old function-based API """
    warnings.warn(DeprecationWarning('This function will be removed '
                                     'in the next release.'
                                     'You should rather use the BaseNormalizer '
                                     'object of the normalize module'))
    for f in processing.get('normalization', []):
        farg = f.func_code.co_varnames #List of the arguments of f
        # A kind of union between the arguments needed by f, and the
        # provided ones
        givenargs = dict((arg, processing['norm_params'][arg])
                         for arg in farg if arg in processing.get('norm_params', []))
        callback = f
        if givenargs:
            callback = partial(callback, **givenargs)
        yield BaseNormalizer(callback=callback, attr_index=ind)

def extract_treatment_from_treatment(processing, ind):
    """ Extract Treatment object from processing dict.
    This is only for backward compatibility with the old API.
    """
    if processing['metric'] == 'geographical':
        return GeographicalProcessing(ind, ind,
                                     matrix_normalized=processing.get('matrix_normalized', False),
                                     **processing.get('metric_params', {}))


###############################################################################
### ALIGNER ###################################################################
###############################################################################
def align(alignset, targetset, threshold, processings=None, resultfile=None,
          _applyNormalization=True):
    """ Try to align the items of alignset onto targetset's ones

        `alignset` and `targetset` are the sets to align. Each set contains
        lists where the first column is the identifier of the item,
        and the others are
        the attributs to align. (Note that the order is important !) Both must
        have the same number of columns.

        `processings` is a dictionary of dictionaries.
        Each key is the indice of the row, and each value is a dictionary
        that contains the processings to do on the different attributs.
        Each dictionary is built as the following:

            processing = {'normalization': [f1, f2, f3],
                         'norm_params': {'arg1': arg01, 'arg2': arg02},
                         'metric': d1,
                         'metric_params': {'arg1': arg11},
                         'weighting': w,
                         'matrix_normalize': True
                        }

            `normalization` is the list of functions called to normalize the
            given attribut (in order). Each functions is called with `norm_params`
            as arguments

            Idem for `distance` and `distance_args`

            `weighting` is the weighting for the current attribut in regard to
            the others

            `resultfile` (default is None). Write the matched elements in a file.

        Return the distance matrix and the matched list.
    """
    warnings.warn(DeprecationWarning('This function will be removed in the next '
                                     'release.'
                                     ' You should rather use the BaseAligner '
                                     'object of the aligner module'))
    processings = processings or {}
    # Get the normalizers
    normalizers = []
    for ind, processing in processings.iteritems():
        for normalizer in extract_normalization_from_treatment(processing, ind):
            normalizers.append(normalizer)
    # Cleanup processings
    for t in processings.itervalues():
        if 'normalization' in t:
            t.pop('normalization')
        if 'norm_params' in t:
            t.pop('norm_params')
    # Build aligner
    processings = [extract_treatment_from_treatment(t, ind) for ind, t in processings.iteritems()]
    aligner = BaseAligner(threshold, processings)
    aligner.register_ref_normalizer(normalizers)
    aligner.register_target_normalizer(normalizers)
    # Align
    return aligner.align(alignset, targetset)

def subalign(alignset, targetset, alignind, targetind, threshold,
             processings=None, _applyNormalization=True):
    """ Compute a subalignment for a list of indices of the alignset and
    a list of indices for the targetset """
    warnings.warn(DeprecationWarning('This function will be removed in the next '
                                     'release.'
                                     ' You should rather use the BaseAligner '
                                     'object of the aligner module'))
    mat, matched = align([alignset[i[0]] for i in alignind],
                         [targetset[i[0]] for i in targetind], threshold,
                         processings, _applyNormalization=_applyNormalization)
    new_matched = {}
    for k, values in matched.iteritems():
        new_matched[alignind[k]] = [(targetind[i], d) for i, d in values]
    return mat, new_matched

def conquer_and_divide_alignment(alignset, targetset, threshold, processings=None,
                                 indexes=(1,1), mode='kdtree', neighbours_threshold=0.1,
                                 n_clusters=None, kwordsgram=1, siglen=200,
                                 get_global_mat=True):
    """ Full conquer and divide method for alignment.
    Compute neighbours and merge the different subalignments.
    """
    warnings.warn(DeprecationWarning('This function will be removed in the next '
                                     'release.'
                                     ' You should rather use the BaseAligner '
                                     'object of the aligner module'))
    global_matched = {}
    if get_global_mat:
        global_mat = lil_matrix((len(alignset), len(targetset)))

    processings = processings or {}
    ralignset = normalize_set(alignset, processings)
    rtargetset = normalize_set(targetset, processings)

    for alignind, targetind in findneighbours(ralignset, rtargetset, indexes, mode,
                                              neighbours_threshold, n_clusters,
                                              kwordsgram, siglen):
        _, matched = subalign(alignset, targetset, alignind, targetind,
                                threshold, processings, _applyNormalization=False)
        for k, values in matched.iteritems():
            subdict = global_matched.setdefault(k, set())
            for v, d in values:
                subdict.add((v, d))
                # XXX avoid issue in sparse matrix
                if get_global_mat:
                    global_mat[k[0], v[0]] = d or 10**(-10)
    if get_global_mat:
        return global_mat, global_matched
    return global_matched

def alignall(alignset, targetset, threshold, processings=None,
             indexes=(1,1), mode='kdtree', neighbours_threshold=0.1,
             n_clusters=None, kwordsgram=1, siglen=200, uniq=False):
    warnings.warn(DeprecationWarning('This function will be removed in the next '
                                     'release.'
                                     ' You should rather use the BaseAligner '
                                     'object of the aligner module'))
    if not mode:
        _, matched = align(alignset, targetset, threshold, processings,
                           resultfile=None, _applyNormalization=True)
    else:
        matched = conquer_and_divide_alignment(alignset, targetset, threshold,
                                               processings, indexes, mode,
                                               neighbours_threshold, n_clusters,
                                               kwordsgram, siglen,
                                               get_global_mat=False)

    if not uniq:
        for alignid in matched:
            for targetid, _ in matched[alignid]:
                yield alignset[alignid[0]][0], targetset[targetid[0]][0]
    else:
        for alignid in matched:
            bestid, _ = sorted(matched[alignid], key=lambda x:x[1])[0]
            yield alignset[alignid[0]][0], targetset[bestid[0]][0]

def alignall_iterative(alignfile, targetfile, alignformat, targetformat,
                       threshold, size=10000, equality_threshold=0.01,
                       processings=None, indexes=(1,1), mode='kdtree',
                       neighbours_threshold=0.1, n_clusters=None, kwordsgram=1,
                       siglen=200, cache=None):
    """ This function helps you to align *huge* files.
        It takes your csv files as arguments and split them into smaller ones
        (files of `size` lines), and runs the alignment on those files.

        `alignformat` and `targetformat` are keyworded arguments given to the
        nazca.dataio.parsefile function.

        This function returns its own cache. The cache is quite simply a
        dictionary having align items' id as keys and tuples (target item's id,
        distance) as value. This dictionary can be regiven to this function to
        perform another alignment (with different parameters, or just to be
        sure everything has been caught)

        If the distance of an alignment is below `equality_threshold`, the
        alignment is considered as perfect, and the corresponding item is
        removed from the alignset (to speed up the computation).
    """
    warnings.warn(DeprecationWarning('This function will be removed in the next '
                                     'release.'
                                     ' You should rather use the BaseAligner '
                                     'object of the aligner module'))
    #Split the huge files into smaller ones
    aligndir = mkdtemp()
    targetdir = mkdtemp()
    alignfiles = split_file(alignfile, aligndir, size)
    targetfiles = split_file(targetfile, targetdir, size)

    #Compute the number of iterations that must be done to achieve the alignement
    nb_iterations = len(alignfiles) * len(targetfiles)
    current_it = 0

    cache = cache or {} #Contains the better known alignements
    #Contains the id of perfectly aligned data
    doneids = set(_id for _id, (_, dist) in cache.iteritems()
                          if dist < equality_threshold)

    try:
        for alignfile in alignfiles:
            alignset = [a for a in parsefile(osp.join(aligndir, alignfile), **alignformat)
                        if a[0] not in doneids]
            for targetfile in targetfiles:
                targetset = parsefile(osp.join(targetdir, targetfile), **targetformat)
                matched = conquer_and_divide_alignment(alignset, targetset,
                                                       threshold,
                                                       processings=processings,
                                                       indexes=indexes,
                                                       mode=mode,
                                                       neighbours_threshold=neighbours_threshold,
                                                       n_clusters=n_clusters,
                                                       kwordsgram=kwordsgram,
                                                       siglen=siglen,
                                                       get_global_mat=False)
                for alignid in matched:
                    bestid, dist = sorted(matched[alignid], key=lambda x:x[1])[0]
                    #Get the better known distance
                    _, current_dist = cache.get(alignset[alignid[0]][0], (None, None))
                    if current_dist is None or current_dist > dist:
                        #If it's better, update the cache
                        cache[alignset[alignid[0]][0]] = (targetset[bestid[0]][0], dist)
                        if dist <= equality_threshold:
                            #If perfect, stop trying to align this one
                            doneids.add(alignset[alignid][0])

                current_it += 1
                sys.stdout.write('\r%0.2f%%' % (current_it * 100. /
                                                nb_iterations))
                sys.stdout.flush()
                if doneids:
                    alignset = [a for a in alignset if a[0] not in doneids]
                if not alignset: #All items have been aligned
                    #TODO Increment current_it.
                    #The progress of the alignment process is computed with
                    #`current_it`. If all items of `alignset` are aligned, we
                    #stop the alignment process for this `alignset`. If
                    #`current_it` isn’t incremented, the progress shown will be
                    #false.
                    break

    finally:
        rmtree(aligndir)
        rmtree(targetdir)

    return cache







###############################################################################
### CLUSTERING-BASED BLOCKINGS FUNCTIONS ######################################
###############################################################################
# Backward compatibility. Now, use the BlockingObject inside the functions.
# Perhaps these functions may be removed later...
def findneighbours_clustering(alignset, targetset, indexes=(1, 1),
                              mode='kmeans', n_clusters=None):
    """ Find the neigbhours using clustering (kmeans or minibatchkmeans)
    """
    warnings.warn(DeprecationWarning('This function will be removed in the next '
                                     'release.'
                                     ' You should rather use the KmeansBlocking '
                                     'object of the blocking module'))
    if mode == 'kmeans':
        blocking = KmeansBlocking(ref_attr_index=indexes[0],
                                  target_attr_index=indexes[1],
                                  n_clusters=n_clusters)
    elif mode == 'minibatch':
        blocking = MiniBatchKmeansBlocking(ref_attr_index=indexes[0],
                                           target_attr_index=indexes[1],
                                           n_clusters=n_clusters)
    else:
        raise ValueError("Mode should be 'kmeans' or 'minibatch'")
    # Fit blocking object
    blocking.fit(alignset, targetset)
    return list(blocking.iter_blocks())

def findneighbours_kdtree(alignset, targetset, indexes=(1, 1), threshold=0.1):
    """ Find the neigbhours using kdree
    """
    warnings.warn(DeprecationWarning('This function will be removed in the next '
                                     'release.'
                                     ' You should rather use the KdTreeBlocking '
                                     'object of the blocking module'))
    blocking = KdTreeBlocking(ref_attr_index=indexes[0],
                              target_attr_index=indexes[1],
                              threshold=threshold)
    blocking.fit(alignset, targetset)
    return list(blocking.iter_blocks())

def findneighbours_minhashing(alignset, targetset, indexes=(1, 1), threshold=0.1,
                              kwordsgram=1, siglen=200):
    """ Find the neigbhours using minhashing
    """
    warnings.warn(DeprecationWarning('This function will be removed in the next '
                                     'release.'
                                     ' You should rather use the '
                                     'MinHashingBlocking '
                                     'object of the blocking module'))
    blocking = MinHashingBlocking(ref_attr_index=indexes[0],
                                  target_attr_index=indexes[1],
                                  threshold=threshold, kwordsgram=kwordsgram,
                                  siglen=siglen)
    blocking.fit(alignset, targetset)
    return list(blocking.iter_blocks())

def findneighbours(alignset, targetset, indexes=(1, 1), mode='kdtree',
                   neighbours_threshold=0.1, n_clusters=None, kwordsgram=1, siglen=200):
    """ This function helps to find neighbours from items of alignset and
        targetset. “Neighbours” are items that are “not so far”, ie having a
        close label, are located in the same area etc.

        This function handles two types of neighbouring : text and numeric.
        For text value, you have to use the “minhashing” and for numeric, you
        can choose from “kdtree“, “kdmeans“ and “minibatch”

        The arguments to give are :
            - `alignset` and `targetset` are the sets where neighbours have to
              be found.
            - `indexes` are the location of items to compare
            - `mode` is the search type to use
            - `neighbours_threshold` is the `mode` neighbours_threshold

            - `n_clusters` is used for "kmeans" and "minibatch" methods, and it
              is the number of clusters to use.

            - `kwordsgram` and `siglen` are used for "minhashing". `kwordsgram`
              is the length of wordsgrams to use, and `siglen` is the length of
              the minhashing signature matrix.

        return a list of lists, built as the following :
            [
                [[indexes_of_alignset_0], [indexes_of_targetset_0]],
                [[indexes_of_alignset_1], [indexes_of_targetset_1]],
                [[indexes_of_alignset_2], [indexes_of_targetset_2]],
                [[indexes_of_alignset_3], [indexes_of_targetset_3]],
                ...
            ]
    """
    warnings.warn(DeprecationWarning('This function will be removed in the next '
                                     'release.'
                                     ' You should rather use the '
                                     'BaseBlocking '
                                     'objects of the blocking module'))
    SEARCHERS = set(['kdtree', 'minhashing', 'kmeans', 'minibatch'])
    mode = mode.lower()

    if mode not in SEARCHERS:
        raise NotImplementedError('Unknown mode given')
    if mode == 'kdtree':
        return findneighbours_kdtree(alignset, targetset, indexes, neighbours_threshold)
    elif mode == 'minhashing':
        return findneighbours_minhashing(alignset, targetset, indexes, neighbours_threshold,
                                         kwordsgram, siglen)
    elif mode in set(['kmeans', 'minibatch']):
        try:
            return findneighbours_clustering(alignset, targetset, indexes, mode, n_clusters)
        except:
            raise NotImplementedError('Scikit learn does not seem to be installed')
