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

from os import listdir
import os.path as osp
from shutil import rmtree
from tempfile import mkdtemp
import sys

from scipy.spatial import KDTree
from scipy.sparse import lil_matrix

from nazca.minhashing import Minlsh
from nazca.dataio import write_results, split_file, parsefile
import nazca.matrix as m


def normalize_set(rset, treatments):
    """ Apply all the normalization functions to the given rset """
    for row in rset:
        for ind, attribut in enumerate(row):
            treat = treatments.get(ind)
            if not attribut or not treat:
                continue
            for f in treat.get('normalization', []):
                farg = f.func_code.co_varnames #List of the arguments of f
                # A kind of union between the arguments needed by f, and the
                # provided ones
                givenargs = dict((arg, treat['norm_params'][arg])
                                 for arg in farg if arg in treat.get('norm_params', []))
                attribut = f(attribut, **givenargs)
            row[ind] = attribut
    return rset

def findneighbours_kdtree(alignset, targetset, indexes=(1, 1), threshold=0.1):
    """ Find the neigbhours using kdree
    """
    #If an element is None (missing), use instead the identity element.
    #The identity element is defined as the 0-vector
    firstelement = alignset[0][indexes[0]]
    idsize = len(firstelement) if isinstance(firstelement, (tuple, list)) else 1
    idelement = (0,) * idsize
    # KDTree is expecting a two-dimensional array
    if idsize == 1:
        aligntree  = KDTree([(elt[indexes[0]],) or idelement for elt in alignset])
        targettree = KDTree([(elt[indexes[1]],) or idelement for elt in targetset])
    else:
        aligntree  = KDTree([elt[indexes[0]] or idelement for elt in alignset])
        targettree = KDTree([elt[indexes[1]] or idelement for elt in targetset])
    extraneighbours = aligntree.query_ball_tree(targettree, threshold)
    neighbours = []
    for ind in xrange(len(alignset)):
        if not extraneighbours[ind]:
            continue
        neighbours.append([[ind], extraneighbours[ind]])
    return neighbours

def findneighbours_minhashing(alignset, targetset, indexes=(1, 1), threshold=0.1,
                              kwordsgram=1, siglen=200):
    """ Find the neigbhours using minhashing
    """
    #If an element is None (missing), use instead the identity element.
    idelement = ''
    minhasher = Minlsh()
    minhasher.train([elt[indexes[0]] or idelement for elt in alignset] +
                    [elt[indexes[1]] or idelement for elt in targetset],
                    kwordsgram, siglen)
    rawneighbours = minhasher.predict(threshold)
    neighbours = []
    for data in rawneighbours:
        neighbours.append([[], []])
        for i in data:
            if i >= len(alignset):
                neighbours[-1][1].append(i - len(alignset))
            else:
                neighbours[-1][0].append(i)
        if len(neighbours[-1][0]) == 0 or len(neighbours[-1][1]) == 0:
            neighbours.pop()
    return neighbours

def findneighbours_clustering(alignset, targetset, indexes=(1, 1),
                              mode='kmeans', n_clusters=None):
    """ Find the neigbhours using clustering (kmeans or minibatchkmeans)
    """
    from sklearn import cluster
    #If an element is None (missing), use instead the identity element.
    #The identity element is defined as the 0-vector
    idelement = tuple([0 for _ in xrange(len(alignset[0][indexes[0]]))])
    # We assume here that there are at least 2 elements in the alignset
    n_clusters = n_clusters or (len(alignset)/10 or len(alignset)/2)

    if mode == 'kmeans':
        kmeans = cluster.KMeans(n_clusters=n_clusters)
    else:
        kmeans = cluster.MiniBatchKMeans(n_clusters=n_clusters)

    kmeans.fit([elt[indexes[0]] or idelement for elt in alignset])
    predicted = kmeans.predict([elt[indexes[1]] or idelement for elt in targetset])

    neighbours = [[[], []] for _ in xrange(kmeans.n_clusters)]
    for ind, i in enumerate(predicted):
        neighbours[i][1].append(ind)
    for ind, i in enumerate(kmeans.labels_):
        neighbours[i][0].append(ind)
    #XXX: Check all lists have one element at least ?
    return neighbours

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

def align(alignset, targetset, threshold, treatments=None, resultfile=None,
          _applyNormalization=True):
    """ Try to align the items of alignset onto targetset's ones

        `alignset` and `targetset` are the sets to align. Each set contains
        lists where the first column is the identifier of the item, and the others are
        the attributs to align. (Note that the order is important !) Both must
        have the same number of columns.

        `treatments` is a dictionary of dictionaries.
        Each key is the indice of the row, and each value is a dictionary
        that contains the treatments to do on the different attributs.
        Each dictionary is built as the following:

            treatment = {'normalization': [f1, f2, f3],
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
    treatments = treatments or {}

    if _applyNormalization:
        ralignset = normalize_set(alignset, treatments)
        rtargetset = normalize_set(targetset, treatments)
    else:
        ralignset = alignset
        rtargetset = targetset

    items = []
    for ind, tr in treatments.iteritems():
        items.append((tr.get('weighting', 1),
                      [ralignset[i][ind] for i in xrange(len(ralignset))],
                      [rtargetset[i][ind] for i in xrange(len(rtargetset))],
                      tr['metric'],
                      tr.get('matrix_normalized', True),
                      tr.get('metric_params', {})))

    mat = m.globalalignmentmatrix(items)
    matched = m.matched(mat, threshold)

    # Write file if asked
    if resultfile:
        write_results(matched, alignset, targetset, resultfile)

    return mat, matched

def subalign(alignset, targetset, alignind, targetind, threshold,
             treatments=None, _applyNormalization=True):
    """ Compute a subalignment for a list of indices of the alignset and
    a list of indices for the targetset """
    mat, matched = align([alignset[i] for i in alignind],
                         [targetset[i] for i in targetind], threshold,
                         treatments, _applyNormalization=_applyNormalization)
    new_matched = {}
    for k, values in matched.iteritems():
        new_matched[alignind[k]] = [(targetind[i], d) for i, d in values]
    return mat, new_matched


def conquer_and_divide_alignment(alignset, targetset, threshold, treatments=None,
                                 indexes=(1,1), mode='kdtree', neighbours_threshold=0.1,
                                 n_clusters=None, kwordsgram=1, siglen=200,
                                 get_global_mat=True):
    """ Full conquer and divide method for alignment.
    Compute neighbours and merge the different subalignments.
    """
    global_matched = {}
    if get_global_mat:
        global_mat = lil_matrix((len(alignset), len(targetset)))

    treatments = treatments or {}
    ralignset = normalize_set(alignset, treatments)
    rtargetset = normalize_set(targetset, treatments)

    for alignind, targetind in findneighbours(ralignset, rtargetset, indexes, mode,
                                              neighbours_threshold, n_clusters,
                                              kwordsgram, siglen):
        _, matched = subalign(alignset, targetset, alignind, targetind,
                                threshold, treatments, _applyNormalization=False)
        for k, values in matched.iteritems():
            subdict = global_matched.setdefault(k, set())
            for v, d in values:
                subdict.add((v, d))
                # XXX avoid issue in sparse matrix
                if get_global_mat:
                    global_mat[k, v] = d or 10**(-10)
    if get_global_mat:
        return global_mat, global_matched
    return global_matched

def alignall(alignset, targetset, threshold, treatments=None,
             indexes=(1,1), mode='kdtree', neighbours_threshold=0.1,
             n_clusters=None, kwordsgram=1, siglen=200, uniq=False):

    if not mode:
        _, matched = align(alignset, targetset, threshold, treatments,
                           resultfile=None, _applyNormalization=True)
    else:
        matched = conquer_and_divide_alignment(alignset, targetset, threshold,
                                               treatments, indexes, mode,
                                               neighbours_threshold, n_clusters,
                                               kwordsgram, siglen,
                                               get_global_mat=False)

    if not uniq:
        for alignid in matched:
            for targetid, _ in matched[alignid]:
                yield alignset[alignid][0], targetset[targetid][0]
    else:
        for alignid in matched:
            bestid, _ = sorted(matched[alignid], key=lambda x:x[1])[0]
            yield alignset[alignid][0], targetset[bestid][0]

def alignall_iterative(alignfile, targetfile, alignformat, targetformat,
                       threshold, size=10000, equality_threshold=0.01,
                       treatments=None, indexes=(1,1), mode='kdtree',
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

    #Split the huge files into smaller ones
    aligndir = mkdtemp()
    targetdir = mkdtemp()
    alignfiles = split_file(alignfile, aligndir, size)
    targetfiles = split_file(targetfile, targetdir, size)

    #Compute the number of iterations that must be done to achieve the alignement
    nb_iterations = len(alignfiles) * len(targetfiles)
    current_it = 0

    doneids = set([]) #Contains the id of perfectly aligned data
    cache = cache or {} #Contains the better known alignments

    try:
        for alignfile in alignfiles:
            alignset = parsefile(osp.join(aligndir, alignfile), **alignformat)
            for targetfile in targetfiles:
                if doneids: #If some alignements are already perfect,
                            #don't redo them !
                    tmp_align = []
                    for a in alignset:
                        if a[0] not in doneids:
                            tmp_align.append(a)
                    alignset = tmp_align

                targetset = parsefile(osp.join(targetdir, targetfile), **targetformat)
                matched = conquer_and_divide_alignment(alignset, targetset,
                                                       threshold,
                                                       treatments=treatments,
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
                    _, current_dist = cache.get(alignset[alignid][0], (None, None))
                    if not current_dist or current_dist > dist:
                        #If it's better, update the cache
                        cache[alignset[alignid][0]] = (targetset[bestid][0], dist)
                        if dist <= equality_threshold:
                            #If perfect, stop trying to align this one
                            doneids.add(alignset[alignid][0])

                current_it += 1
                sys.stdout.write('\r%0.2f%%' % (current_it * 100. /
                                                nb_iterations))
                sys.stdout.flush()
    finally:
        rmtree(aligndir)
        rmtree(targetdir)

    return cache
