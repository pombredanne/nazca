# -*- coding:utf-8 -*-
#
# copyright 2013 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
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

from nerdy import dataio, core


class DataioTest(unittest2.TestCase):
    """ Test of dataio """

    def test_sparql_query(self):
        results = dataio.sparql_query(query=u'''SELECT ?uri
                                                WHERE{
                                                ?uri rdfs:label "Python"@en .
                                                ?uri rdf:type ?type}''',
                                      endpoint=u'http://dbpedia.org/sparql')
        truth = [{u'uri':
                  {u'type': u'uri',
                   u'value': u'http://sw.opencyc.org/2008/06/10/concept/en/Python_ProgrammingLanguage'}},
                 {u'uri':
                  {u'type': u'uri',
                   u'value': u'http://sw.opencyc.org/2008/06/10/concept/Mx4r74UIARqkEdac2QACs0uFOQ'}}]
        self.assertEqual(results, truth)

    def test_rql_url_query(self):
        results = dataio.rql_url_query('Any U LIMIT 1 WHERE X cwuri U, X name "apycot"',
                                       'http://www.cubicweb.org')
        self.assertEqual(results, [[u'http://www.cubicweb.org/1310453']])

    def test_prerryprint(self):
        text = 'Hello everyone, this is   me speaking. And me.'
        source = core.NerdySourceLexical({'everyone': 'http://example.com/everyone',
                                          'me': 'http://example.com/me'})
        nerdy = core.NerdyProcess((source,))
        named_entities = nerdy.process_text(text)
        html = dataio.NerdyHTMLPrettyPrint().pprint_text(text, named_entities)
        self.assertEqual(html, (u'Hello <a href="http://example.com/everyone">everyone</a>, '
                                u'this is   <a href="http://example.com/me">me</a> speaking. '
                                u'And <a href="http://example.com/me">me</a>.'))



if __name__ == '__main__':
    unittest2.main()

