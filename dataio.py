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

from os.path import exists as fileexists

import csv


def autocasted(data, encoding=None):
    """ Try to convert data into a specific type
    in (int, float, str)
    """
    data = data.strip()
    try:
        return int(data)
    except ValueError:
        try:
            return float(data.replace(',', '.'))
        except ValueError:
            if encoding:
                return data.decode(encoding)
            return data

def sparqlquery(endpoint, query, indexes=[]):
    """ Run the sparql query on the given endpoint, and wrap the items in the
    indexes form. If indexes is empty, keep raw output"""

    from SPARQLWrapper import SPARQLWrapper, JSON

    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    rawresults = sparql.query().convert()
    labels = rawresults['head']['vars']
    results = []

    for raw in rawresults["results"]["bindings"]:
        data = []
        if not indexes:
            data = [autocasted(raw[label]['value']) for label in labels]
        else:
            for ind in indexes:
                if isinstance(ind, tuple):
                    data.append(tuple([autocasted(raw[labels[i]]['value']) for i in ind]))
                else:
                    data.append(autocasted(raw[labels[ind]]['value']))
        results.append(data)
    return results

def parsefile(filename, indexes=[], nbmax=None, delimiter='\t',
              encoding='utf-8', field_size_limit=None):
    """ Parse the file (read ``nbmax`` line at maximum if given). Each
        line is splitted according ``delimiter`` and only ``indexes`` are kept

        eg : The file is :
                1, house, 12, 19, apple
                2, horse, 21.9, 19, stramberry
                3, flower, 23, 2.17, cherry

            data = parsefile('myfile', [0, (2, 3), 4, 1], delimiter=',')

            The result will be :
            data = [[1, (12,   19), 'apple', 'house'],
                    [2, (21.9, 19), 'stramberry', 'horse'],
                    [3, (23,   2.17), 'cherry', 'flower']]

    """
    def formatedoutput(filename):
        if field_size_limit:
            csv.field_size_limit(field_size_limit)

        with open(filename, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=delimiter)
            for row in reader:
                yield [autocasted(cell) for cell in row]


    result = []
    for ind, row in enumerate(formatedoutput(filename)):
        data = []
        if nbmax and ind > nbmax:
            break
        if not indexes:
            data = row
        else:
            for ind in indexes:
                if isinstance(ind, tuple):
                    data.append(tuple([row[i] for i in ind]))
                    if '' in data[-1]:
                        data[-1] = None
                elif row[ind]:
                    data.append(row[ind])
                else:
                    data.append(None)

        result.append(data)
    return result

def write_results(matched, alignset, targetset, resultfile):
    """ Given a matched dictionnay, an alignset and a targetset to the
        resultfile
    """
    openmode = 'a' if fileexists(resultfile) else 'w'
    with open(resultfile, openmode) as fobj:
        if openmode == 'w':
            fobj.write('aligned;targetted;distance\n')
        for aligned in matched:
            for target, dist in matched[aligned]:
                alignid = alignset[aligned][0]
                targetid = targetset[target][0]
                fobj.write('%s;%s;%s\n' %
                    (alignid.encode('utf-8') if isinstance(alignid, basestring)
                                             else alignid,
                     targetid.encode('utf-8') if isinstance(targetid, basestring)
                                              else targetid,
                     dist
                     ))
