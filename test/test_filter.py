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

from nerdy import core
from nerdy.tokenizer import Token, Sentence


class FilterTest(unittest2.TestCase):
    """ Test of filters """

    def test_occurence_filter_min_occ(self):
        """ Test occurence filter """
        text = 'Hello everyone, this is   me speaking. And me.'
        source1 = core.NerdySourceLexical({'everyone': 'http://example.com/everyone',
                                          'me': 'http://example.com/me'})
        source2 = core.NerdySourceLexical({'me': 'http://example2.com/me'})
        _filter = core.NerdyOccurenceFilter(min_occ=2)
        nerdy = core.NerdyProcess((source1, source2), filters=(_filter,))
        named_entities = nerdy.process_text(text)
        self.assertEqual(named_entities,
                         [('http://example.com/me', None,
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

    def test_occurence_filter_max_occ(self):
        """ Test occurence filter """
        text = 'Hello everyone, this is   me speaking. And me.'
        source1 = core.NerdySourceLexical({'everyone': 'http://example.com/everyone',
                                          'me': 'http://example.com/me'})
        source2 = core.NerdySourceLexical({'me': 'http://example2.com/me'})
        _filter = core.NerdyOccurenceFilter(max_occ=1)
        nerdy = core.NerdyProcess((source1, source2), filters=(_filter,))
        named_entities = nerdy.process_text(text)
        self.assertEqual(named_entities,
                         [('http://example.com/everyone', None,
                           Token(word='everyone', start=6, end=14,
                                           sentence=Sentence(indice=0, start=0, end=38))),])

    def test_disambiguation_word_length(self):
        """ Test occurence filter """
        text = 'Hello toto tutu. And toto.'
        source = core.NerdySourceLexical({'toto tutu': 'http://example.com/toto_tutu',
                                          'toto': 'http://example.com/toto'})
        _filter = core.NerdyDisambiguationWordParts()
        nerdy = core.NerdyProcess((source,), filters=(_filter,))
        named_entities = nerdy.process_text(text)
        self.assertEqual(named_entities,
                         [('http://example.com/toto_tutu', None,
                           Token(word='toto tutu', start=6, end=15,
                                 sentence=Sentence(indice=0, start=0, end=16))),
                          ('http://example.com/toto_tutu', None,
                           Token(word='toto', start=21, end=25,
                                 sentence=Sentence(indice=1, start=16, end=26)))])



if __name__ == '__main__':
    unittest2.main()

