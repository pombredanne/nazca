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

import cubes.alignment.distances as d
import cubes.alignment.normalize as n
import cubes.alignment.matrix as m


def align(alignquery, targetquery, treatments, threshold, resultfile):
    """ Try to align the results of alignquery onto targetquery's ones

        queries are two rql queries were the first column is the identifier of
        the items, and the others are the attributs to align. (Note that the
        order is important !) Both must have the same number of columns

        `treatments` is a list of dictionnary. Each dictionnary contains the
        treatments to do on the different attributs. The first dictionnary is
        for the first attribut (not the identifier !), the second for the
        second, etc. Each dictionnary is built as the following:

            treatment = { 'normalization': [f1, f2, f3],
                          'norm_args': { 'arg1': arg01, 'arg2': arg02},
                          'distance': d1,
                          'distance_args': { 'arg1': arg11 },
                          'weighting': w,
                          'defvalue': dv,
                          'matrix_normalize': True
                        }

            `normalization` is the list of functions called to normalize the
            given attribut (in order). Each functions is called with the
            `norm_args`

            Idem for `distance` and `distance_args`

            `weighting` is the weighting of the current attribut in regard to
            the others

            `defvalue` is the default value to use, in case of the value is None
            `matrix_normalize`, True means the values will be between 0 and 1,
                else the raw value is kept

        `resultfile` is the name of the output csv.
    """

    def normalizerset(rset):
        """ Apply all the normalization functions to the given rset """
        for row in rset:
            for ind, attribut in enumerate(row[1:]):
                treat = treatments[ind]
                if not attribut:
                    continue
                for f in treat['normalization']:
                    farg = f.func_code.co_varnames #List of the arguments of f
                    # A kind of union between the arguments need by f, and the
                    # provided ones
                    givenargs = dict((arg, treat['norm_args'][arg])
                                 for arg in farg if arg in treat['norm_args'])
                    attribut = f(attribut, **givenargs)
                row[ind + 1] = attribut
        return rset

    ## Just to be certain we have all the keys
    for t in treatments:
        t.setdefault('norm_args', {})
        t.setdefault('distance_args', {})
        t.setdefault('weighting', 1)
        t.setdefault('defvalue', 100)
        t.setdefault('matrix_normalize', True)

    ralignset = normalizerset(session.execute(alignquery))
    rtargetset = normalizerset(session.execute(targetquery))

    items = []
    for ind, tr in enumerate(treatments):
        item = (tr['weighting'],
                [ralignset[i][ind + 1] for i in xrange(len(ralignset))],
                [rtargetset[i][ind + 1] for i in xrange(len(rtargetset))],
                tr['distance'],
                tr['defvalue'],
                tr['matrix_normalize'],
                tr['distance_args'])
        items.append(item)

    mat = m.globalalignmentmatrix(items)
    matched = mat.matched(threshold)

    if not matched:
        print "Nothing matched"
        return

    with open(resultfile, 'w') as fobj:
        for cible in matched:
            fobj.write('%s, %s\n' % (ralignset[cible][0],
                                   ', '.join((str(rtargetset[target][0])
                                              for target, _ in matched[cible]))))
if __name__ == '__main__':
    alignquery = 'Any P, BP ORDERBY(RANDOM()) LIMIT 100 WHERE P is Person, ' \
                 'P birthplace BP, NOT BP is NULL'
    targetquery = 'Any GID, N ORDERBY(RANDOM()) LIMIT 1000 WHERE L is Location, ' \
                  'L name N, L geoid GID'

    lemmas = n.loadlemmas('data/french_lemmas.txt')
    tr = { 'normalization': [n.simplify],
           'norm_args': { 'lemmas' : lemmas, 'removeStopWords': False },
           'distance':  d.levenshtein,
         }

    align(alignquery, targetquery, [tr], 0.3, 'toto')

