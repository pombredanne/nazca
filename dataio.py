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
import urllib

try:
    from SPARQLWrapper import SPARQLWrapper, JSON
    SPARQL_ENABLED = True
except ImportError:
    SPARQL_ENABLED = False


def autocasted(data, encoding=None):
    """ Try to convert data into a specific type
    in (int, float, str)
    """
    try:
        return int(data)
    except ValueError:
        try:
            return float(data.replace(',', '.'))
        except ValueError:
            data = data.strip()
            if encoding:
                return data.decode(encoding)
            return data

def rqlquery(host, rql, indexes=None):
    """ Run the rql query on the given cubicweb host
    """

    if host.endswith('/'):
        host = host[:-1]

    indexes = indexes or []
    filehandle = urllib.urlopen('%(host)s/view?'
                                'rql=%(rql)s&vid=csvexport'
                                % {'rql': rql, 'host': host})
    filehandle.readline()#Skip the first line
    return parsefile(filehandle, delimiter=';', indexes=indexes);

def sparqlquery(endpoint, query, indexes=None):
    """ Run the sparql query on the given endpoint, and wrap the items in the
    indexes form. If indexes is empty, keep raw output"""

    if not SPARQL_ENABLED:
        raise ImportError("You have to install SPARQLWrapper and JSON modules to"
                          "used this function")

    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    rawresults = sparql.query().convert()
    labels = rawresults['head']['vars']
    results = []
    indexes = indexes or []

    for raw in rawresults["results"]["bindings"]:
        data = []
        if not indexes:
            data = [autocasted(raw[label]['value']) for label in labels]
        else:
            for il, ind in enumerate(indexes):
                if isinstance(ind, tuple):
                    data.append(tuple([autocasted(raw[labels[i]]['value']) for i in ind]))
                else:
                    data.append(autocasted(raw[labels[il]]['value']))
        results.append(data)
    return results

def parsefile(filename, indexes=None, nbmax=None, delimiter='\t',
              encoding='utf-8', field_size_limit=None, formatopt=None):
    """ Parse the file (read ``nbmax`` line at maximum if given). Each
        line is splitted according ``delimiter`` and only ``indexes`` are kept

        eg : The file is :
                1, house, 12, 19, apple
                2, horse, 21.9, 19, stramberry
                3, flower, 23, 2.17, cherry

            >>> data = parsefile('myfile', [0, (2, 3), 4, 1], delimiter=',')
            data = [[1, (12, 19), u'apple', u'house'],
                    [2, (21.9, 19), u'stramberry', u'horse'],
                    [3, (23, 2.17), u'cherry', u'flower']]

            By default, all cells are "autocasted" (thanks to the
            ``autocasted()`` function), but you can overpass it thanks to the
            ``formatopt`` dictionnary. Each key is the index to work on, and the
            value is the function to call. See the following example:

            >>> data = parsefile('myfile', [0, (2, 3), 4, 1], delimiter=',',
            >>>                  formatopt={2:lambda x:x.decode('utf-8')})
            data = [[1, (u'12', 19), u'apple', u'house'],
                    [2, (u'21.9', 19), u'stramberry', u'horse'],
                    [3, (u'23', 2.17), u'cherry', u'flower']]

    """
    def formatedoutput(filename):
        if field_size_limit:
            csv.field_size_limit(field_size_limit)

        if isinstance(filename, basestring):
            csvfile = open(filename, 'r')
        else:
            csvfile = filename
        reader = csv.reader(csvfile, delimiter=delimiter)
        for row in reader:
            yield [cell.strip() for cell in row]
        csvfile.close()



    result = []
    indexes = indexes or []
    formatopt = formatopt or {}
    for ind, row in enumerate(formatedoutput(filename)):
        row = [formatopt.get(i, lambda x: autocasted(x, encoding))(cell)
               for i, cell in enumerate(row)]
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
