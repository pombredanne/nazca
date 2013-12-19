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
import shutil
from contextlib import contextmanager
from os import path
from tempfile import mkdtemp

from nazca.utils.dataio import (HTMLPrettyPrint, ValidXHTMLPrettyPrint,
                                sparqlquery, rqlquery, parsefile,
                                autocast, split_file)
from nazca.named_entities import NerProcess
from nazca.named_entities.sources import NerSourceLexicon

TESTDIR = path.dirname(__file__)

@contextmanager
def tempdir():
    try:
        temp = mkdtemp()
        yield temp
    finally:
        try:
            shutil.rmtree(temp)
        except:
            pass


class ValidXHTMLPrettyPrintTest(unittest2.TestCase):

    def test_valid(self):
        from lxml import etree
        if int(etree.__version__< '3.2.0'):
            # https://bugs.launchpad.net/lxml/+bug/673205
            self.skipTest('Lxml version to old for ValidXHTMLPrettyPrint')
        self.assertTrue(ValidXHTMLPrettyPrint().is_valid(u'<p>coucou</p>'))

    def test_valid_unicode(self):
        from lxml import etree
        if int(etree.__version__< '3.2.0'):
            # https://bugs.launchpad.net/lxml/+bug/673205
            self.skipTest('Lxml version to old for ValidXHTMLPrettyPrint')
        self.assertTrue(ValidXHTMLPrettyPrint().is_valid(u'<p>hé</p>'))

    def test_invalid(self):
        from lxml import etree
        if int(etree.__version__< '3.2.0'):
            # https://bugs.launchpad.net/lxml/+bug/673205
            self.skipTest('Lxml version to old for ValidXHTMLPrettyPrint')
        self.assertFalse(ValidXHTMLPrettyPrint().is_valid(u'<p><div>coucou</div></p>'))

    def test_prettyprint(self):
        text = 'Hello everyone, this is   me speaking. And me.'
        source = NerSourceLexicon({'everyone': 'http://example.com/everyone',
                                   'me': 'http://example.com/me'})
        ner = NerProcess((source,))
        named_entities = ner.process_text(text)
        html = HTMLPrettyPrint().pprint_text(text, named_entities)
        self.assertEqual(html, (u'Hello <a href="http://example.com/everyone">everyone</a>, '
                                u'this is   <a href="http://example.com/me">me</a> speaking. '
                                u'And <a href="http://example.com/me">me</a>.'))

    def test_prettyprint_class(self):
        text = 'Hello everyone, this is   me speaking. And me.'
        source = NerSourceLexicon({'everyone': 'http://example.com/everyone',
                                   'me': 'http://example.com/me'})
        ner = NerProcess((source,))
        named_entities = ner.process_text(text)
        html = HTMLPrettyPrint().pprint_text(text, named_entities, html_class='ner')
        self.assertEqual(html, (u'Hello <a href="http://example.com/everyone" class="ner">everyone</a>, '
                                u'this is   <a href="http://example.com/me" class="ner">me</a> speaking. '
                                u'And <a href="http://example.com/me" class="ner">me</a>.'))


class DataIOTestCase(unittest2.TestCase):

    def test_parser(self):
        data = parsefile(path.join(TESTDIR, 'data', 'file2parse'),
                         [0, (2, 3), 4, 1], delimiter=',')
        self.assertEqual([[1, (12, 19), u'apple', u'house'],
                          [2, (21.9, 19), u'stramberry', u'horse'],
                          [3, (23, 2.17), u'cherry', u'flower']], data)

        data = parsefile(path.join(TESTDIR, 'data', 'file2parse'),
                         [0, (2, 3), 4, 1], delimiter=',', formatopt={2:str})
        self.assertEqual([[1, ('12', 19), u'apple', u'house'],
                          [2, ('21.9', 19), u'stramberry', u'horse'],
                          [3, ('23', 2.17), u'cherry', u'flower']], data)

    def test_autocast(self):
        self.assertEqual(autocast('1'), 1)
        self.assertEqual(autocast('1.'), 1.)
        self.assertEqual(autocast('1,'), 1.)
        self.assertEqual(autocast('1,2'), 1.2)
        self.assertEqual(autocast('1,2X'), '1,2X')
        self.assertEqual(autocast(u'tété'), u'tété')
        self.assertEqual(autocast('tété', encoding='utf-8'), u'tété')

    def test_split_file(self):
        NBLINES = 190
        with tempdir() as outputdir:
            file2split = path.join(TESTDIR, 'data', 'file2split')
            files = split_file(file2split, outputdir, nblines=NBLINES)

            alllines = []
            nbfiles = len(files)
            for num, localpath in enumerate(sorted(files)):
                fullpath = path.join(outputdir, localpath)
                with open(fullpath) as fobj:
                    lines = fobj.readlines()
                # All files, except the last one, must be NBLINES-length.
                if num < nbfiles - 1:
                    self.assertEqual(len(lines), NBLINES)
                alllines.extend(lines)

            with open(file2split) as fobj:
                self.assertEqual(alllines, fobj.readlines())

    def test_sparql_query(self):
        results = sparqlquery(u'http://dbpedia.org/sparql',
                              u'''SELECT DISTINCT ?uri
                                  WHERE{
                                  ?uri rdfs:label "Python"@en .
                                  ?uri rdf:type ?type}''')
        self.assertEqual(results, [['http://dbpedia.org/resource/Python'],
                                   ['http://sw.opencyc.org/2008/06/10/concept/en/Python_ProgrammingLanguage'],
                                   ['http://sw.opencyc.org/2008/06/10/concept/Mx4r74UIARqkEdac2QACs0uFOQ']])

    def test_sparql_autocast(self):
        alignset = sparqlquery('http://dbpedia.inria.fr/sparql',
                                 'prefix db-owl: <http://dbpedia.org/ontology/>'
                                 'prefix db-prop: <http://fr.dbpedia.org/property/>'
                                 'select ?ville, ?name, ?long, ?lat where {'
                                 ' ?ville db-owl:country <http://fr.dbpedia.org/resource/France> .'
                                 ' ?ville rdf:type db-owl:PopulatedPlace .'
                                 ' ?ville db-owl:populationTotal ?population .'
                                 ' ?ville foaf:name ?name .'
                                 ' ?ville db-prop:longitude ?long .'
                                 ' ?ville db-prop:latitude ?lat .'
                                 ' FILTER (?population > 1000)'
                                 '} LIMIT 100', indexes=[0, 1, (2, 3)])
        self.assertEqual(len(alignset), 100)
        self.assertTrue(isinstance(alignset[0][2][0], float))

    def test_sparql_no_autocast(self):
        alignset = sparqlquery('http://dbpedia.inria.fr/sparql',
                                 'prefix db-owl: <http://dbpedia.org/ontology/>'
                                 'prefix db-prop: <http://fr.dbpedia.org/property/>'
                                 'select ?ville, ?name, ?long, ?lat where {'
                                 ' ?ville db-owl:country <http://fr.dbpedia.org/resource/France> .'
                                 ' ?ville rdf:type db-owl:PopulatedPlace .'
                                 ' ?ville db-owl:populationTotal ?population .'
                                 ' ?ville foaf:name ?name .'
                                 ' ?ville db-prop:longitude ?long .'
                                 ' ?ville db-prop:latitude ?lat .'
                                 ' FILTER (?population > 1000)'
                                 '} LIMIT 100', indexes=[0, 1, (2, 3)], autocaste_data=False)
        self.assertEqual(len(alignset), 100)
        self.assertFalse(isinstance(alignset[0][2][0], float))

    def test_rqlquery(self):
        results = rqlquery('http://www.cubicweb.org',
                           'Any U LIMIT 1 WHERE X cwuri U, X name "apycot"')
        self.assertEqual(results, [[u'http://www.cubicweb.org/1310453']])


if __name__ == '__main__':
    unittest2.main()

