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

from nazca.named_entities.sources import (NerSourceLexicon,
                                          NerSourceSparql,
                                          NerSourceRql)
from nazca.named_entities import named_entities as core
from nazca.utils.tokenizer import Token, Sentence


class CoreTest(unittest2.TestCase):
    """ Test of core """

    def test_lexicon_source(self):
        """ Test lexicon source """
        lexicon = {'everyone': 'http://example.com/everyone',
                   'me': 'http://example.com/me'}
        source = NerSourceLexicon(lexicon)
        self.assertEqual(source.query_word('me'), ['http://example.com/me',])
        self.assertEqual(source.query_word('everyone'), ['http://example.com/everyone',])
        self.assertEqual(source.query_word('me everyone'), [])
        self.assertEqual(source.query_word('toto'), [])
        # Token
        token = Token('me', 0, 2, None)
        self.assertEqual(source.recognize_token(token), ['http://example.com/me',])
        token = Token('ma', 0, 2, None)
        self.assertEqual(source.recognize_token(token), [])

    def test_rql_source(self):
        """ Test rql source """
        source = NerSourceRql('http://www.cubicweb.org',
                              'Any U LIMIT 1 WHERE X cwuri U, X name "%(word)s"')
        self.assertEqual(source.query_word('apycot'), [u'http://www.cubicweb.org/1310453',])

    def test_sparql_source(self):
        """ Test sparql source """
        source = NerSourceSparql(u'http://dbpedia.org/sparql',
                                 u'''SELECT ?uri
                                     WHERE{
                                     ?uri rdfs:label "Python"@en .
                                     ?uri rdf:type ?type}''')
        self.assertEqual(source.query_word('cubicweb'),
                         [u'http://sw.opencyc.org/2008/06/10/concept/en/Python_ProgrammingLanguage',
                          u'http://sw.opencyc.org/2008/06/10/concept/Mx4r74UIARqkEdac2QACs0uFOQ'])

    def test_nerdy_process(self):
        """ Test nerdy process """
        text = 'Hello everyone, this is   me speaking. And me.'
        source = NerSourceLexicon({'everyone': 'http://example.com/everyone',
                                   'me': 'http://example.com/me'})
        nerdy = core.NerdyProcess((source,))
        named_entities = nerdy.process_text(text)
        self.assertEqual(named_entities,
                         [('http://example.com/everyone', None,
                           Token(word='everyone', start=6, end=14,
                                           sentence=Sentence(indice=0, start=0, end=38))),
                          ('http://example.com/me', None,
                           Token(word='me', start=26, end=28,
                                           sentence=Sentence(indice=0, start=0, end=38))),
                          ('http://example.com/me', None,
                           Token(word='me', start=43, end=45,
                                           sentence=Sentence(indice=1, start=38, end=46)))])

    def test_nerdy_process_multisources(self):
        """ Test nerdy process """
        text = 'Hello everyone, this is   me speaking. And me.'
        source1 = NerSourceLexicon({'everyone': 'http://example.com/everyone',
                                    'me': 'http://example.com/me'})
        source2 = NerSourceLexicon({'me': 'http://example2.com/me'})
        # Two sources, not unique
        nerdy = core.NerdyProcess((source1, source2))
        named_entities = nerdy.process_text(text)
        self.assertEqual(named_entities,
                         [('http://example.com/everyone', None,
                           Token(word='everyone', start=6, end=14,
                                           sentence=Sentence(indice=0, start=0, end=38))),
                          ('http://example.com/me', None,
                           Token(word='me', start=26, end=28,
                                           sentence=Sentence(indice=0, start=0, end=38))),
                          ('http://example2.com/me', None,
                           Token(word='me', start=26, end=28,
                                           sentence=Sentence(indice=0, start=0, end=38))),
                          ('http://example.com/me', None,
                           Token(word='me', start=43, end=45,
                                           sentence=Sentence(indice=1, start=38, end=46))),
                          ('http://example2.com/me', None,
                           Token(word='me', start=43, end=45,
                                           sentence=Sentence(indice=1, start=38, end=46)))])
        # Two sources, unique
        nerdy = core.NerdyProcess((source1, source2), unique=True)
        named_entities = nerdy.process_text(text)
        self.assertEqual(named_entities,
                         [('http://example.com/everyone', None,
                           Token(word='everyone', start=6, end=14,
                                           sentence=Sentence(indice=0, start=0, end=38))),
                          ('http://example.com/me', None,
                           Token(word='me', start=26, end=28,
                                           sentence=Sentence(indice=0, start=0, end=38))),
                          ('http://example.com/me', None,
                           Token(word='me', start=43, end=45,
                                           sentence=Sentence(indice=1, start=38, end=46)))])
        # Two sources inversed, unique
        nerdy = core.NerdyProcess((source2, source1), unique=True)
        named_entities = nerdy.process_text(text)
        self.assertEqual(named_entities,
                         [('http://example.com/everyone', None,
                           Token(word='everyone', start=6, end=14,
                                           sentence=Sentence(indice=0, start=0, end=38))),
                          ('http://example2.com/me', None,
                           Token(word='me', start=26, end=28,
                                           sentence=Sentence(indice=0, start=0, end=38))),
                          ('http://example2.com/me', None,
                           Token(word='me', start=43, end=45,
                                           sentence=Sentence(indice=1, start=38, end=46)))])

    def test_nerdy_process_add_sources(self):
        """ Test nerdy process """
        text = 'Hello everyone, this is   me speaking. And me.'
        source1 = NerSourceLexicon({'everyone': 'http://example.com/everyone',
                                    'me': 'http://example.com/me'})
        source2 = NerSourceLexicon({'me': 'http://example2.com/me'})
        nerdy = core.NerdyProcess((source1,))
        named_entities = nerdy.process_text(text)
        self.assertEqual(named_entities,
                         [('http://example.com/everyone', None,
                           Token(word='everyone', start=6, end=14,
                                           sentence=Sentence(indice=0, start=0, end=38))),
                          ('http://example.com/me', None,
                           Token(word='me', start=26, end=28,
                                           sentence=Sentence(indice=0, start=0, end=38))),
                          ('http://example.com/me', None,
                           Token(word='me', start=43, end=45,
                                           sentence=Sentence(indice=1, start=38, end=46))),])
        # Two sources, not unique
        nerdy.add_ner_source(source2)
        named_entities = nerdy.process_text(text)
        self.assertEqual(named_entities,
                         [('http://example.com/everyone', None,
                           Token(word='everyone', start=6, end=14,
                                           sentence=Sentence(indice=0, start=0, end=38))),
                          ('http://example.com/me', None,
                           Token(word='me', start=26, end=28,
                                           sentence=Sentence(indice=0, start=0, end=38))),
                          ('http://example2.com/me', None,
                           Token(word='me', start=26, end=28,
                                           sentence=Sentence(indice=0, start=0, end=38))),
                          ('http://example.com/me', None,
                           Token(word='me', start=43, end=45,
                                           sentence=Sentence(indice=1, start=38, end=46))),
                          ('http://example2.com/me', None,
                           Token(word='me', start=43, end=45,
                                           sentence=Sentence(indice=1, start=38, end=46)))])

    def test_nerdy_process_preprocess(self):
        """ Test nerdy process """
        text = 'Hello Toto, this is   me speaking. And me.'
        source = NerSourceLexicon({'Toto': 'http://example.com/toto',
                                   'me': 'http://example.com/me'})
        preprocessor = core.NerdyStopwordsFilterPreprocessor()
        nerdy = core.NerdyProcess((source,),
                                  preprocessors=(preprocessor,))
        named_entities = nerdy.process_text(text)
        self.assertEqual(named_entities, [('http://example.com/toto', None,
                                           Token(word='Toto', start=6, end=10,
                                                 sentence=Sentence(indice=0, start=0, end=34)))])

    def test_nerdy_process_add_preprocess(self):
        """ Test nerdy process """
        text = 'Hello Toto, this is   me speaking. And me.'
        source = NerSourceLexicon({'Toto': 'http://example.com/toto',
                                   'me': 'http://example.com/me'})
        preprocessor = core.NerdyStopwordsFilterPreprocessor()
        nerdy = core.NerdyProcess((source,),)
        named_entities = nerdy.process_text(text)
        self.assertEqual(named_entities,
                         [('http://example.com/toto', None,
                           Token(word='Toto', start=6, end=10,
                                 sentence=Sentence(indice=0, start=0, end=34))),
                          ('http://example.com/me', None,
                           Token(word='me', start=22, end=24,
                                 sentence=Sentence(indice=0, start=0, end=34))),
                          ('http://example.com/me', None,
                           Token(word='me', start=39, end=41,
                                 sentence=Sentence(indice=1, start=34, end=42)))])
        nerdy.add_preprocessors(preprocessor)
        named_entities = nerdy.process_text(text)
        self.assertEqual(named_entities, [('http://example.com/toto', None,
                                           Token(word='Toto', start=6, end=10,
                                                 sentence=Sentence(indice=0, start=0, end=34)))])

    def test_nerdy_process_chained_word(self):
        """ Test nerdy process """
        text = 'Hello everyone me, this is   me speaking. And me.'
        source = NerSourceLexicon({'everyone': 'http://example.com/everyone',
                                   'everyone me': 'http://example.com/everyone_me',
                                   'me': 'http://example.com/me'})
        nerdy = core.NerdyProcess((source,))
        named_entities = nerdy.process_text(text)
        self.assertEqual(named_entities,
                         [('http://example.com/everyone_me', None,
                           Token(word='everyone me', start=6, end=17,
                                 sentence=Sentence(indice=0, start=0, end=41))),
                          ('http://example.com/me', None,
                           Token(word='me', start=29, end=31,
                                 sentence=Sentence(indice=0, start=0, end=41))),
                          ('http://example.com/me', None,
                           Token(word='me', start=46, end=48, sentence=Sentence(indice=1, start=41, end=49)))])


if __name__ == '__main__':
    unittest2.main()

