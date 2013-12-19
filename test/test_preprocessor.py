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

from nerdy import core, tokenizer


class PreprocessorTest(unittest2.TestCase):
    """ Test of preprocessors """

    def test_lowercasefilter(self):
        preprocessor = core.NerdyLowerCaseFilterPreprocessor()
        token = tokenizer.Token('toto', 0, 4, None)
        self.assertEqual(preprocessor(token), None)
        token = tokenizer.Token('toto Tata', 0, 4, None)
        self.assertEqual(preprocessor(token), token)
        token = tokenizer.Token('toto tata', 0, 4, None)
        self.assertEqual(preprocessor(token), None)

    def test_wordsizefilter(self):
        preprocessor = core.NerdyWordSizeFilterPreprocessor()
        token = tokenizer.Token('toto', 0, 4, None)
        self.assertEqual(preprocessor(token), token)
        preprocessor = core.NerdyWordSizeFilterPreprocessor(min_size=3)
        token = tokenizer.Token('toto', 0, 4, None)
        self.assertEqual(preprocessor(token), token)
        token = tokenizer.Token('to', 0, 4, None)
        self.assertEqual(preprocessor(token), None)
        preprocessor = core.NerdyWordSizeFilterPreprocessor(max_size=3)
        token = tokenizer.Token('toto', 0, 4, None)
        self.assertEqual(preprocessor(token), None)
        token = tokenizer.Token('to', 0, 4, None)
        self.assertEqual(preprocessor(token), token)

    def test_lowerfirstword(self):
        preprocessor = core.NerdyLowerFirstWordPreprocessor()
        sentence = tokenizer.Sentence(0, 0, 20)
        # Start of the sentence
        token1 = tokenizer.Token('Toto tata', 0, 4, sentence)
        token2 = tokenizer.Token('Toto tata', 0, 4, sentence)
        self.assertEqual(preprocessor(token1), token2)
        token1 = tokenizer.Token('Us tata', 0, 4, sentence)
        token2 = tokenizer.Token('us tata', 0, 4, sentence)
        self.assertEqual(preprocessor(token1), token2)
        # Not start of the sentence
        token1 = tokenizer.Token('Toto tata', 12, 16, sentence)
        token2 = tokenizer.Token('Toto tata', 12, 16, sentence)
        self.assertEqual(preprocessor(token1), token2)
        token1 = tokenizer.Token('Us tata', 12, 16, sentence)
        token2 = tokenizer.Token('Us tata', 12, 16, sentence)
        self.assertEqual(preprocessor(token1), token2)

    def test_stopwordsfilter(self):
        preprocessor = core.NerdyStopwordsFilterPreprocessor()
        token = tokenizer.Token('Toto', 0, 4, None)
        self.assertEqual(preprocessor(token), token)
        token = tokenizer.Token('Us', 0, 4, None)
        self.assertEqual(preprocessor(token), None)
        token = tokenizer.Token('Us there', 0, 4, None)
        self.assertEqual(preprocessor(token), token)
        # Split words
        preprocessor = core.NerdyStopwordsFilterPreprocessor(split_words=True)
        token = tokenizer.Token('Us there', 0, 4, None)
        self.assertEqual(preprocessor(token), None)
        token = tokenizer.Token('Us there toto', 0, 4, None)
        self.assertEqual(preprocessor(token), token)

    def test_hashtag(self):
        preprocessor = core.NerdyHashTagPreprocessor()
        token = tokenizer.Token('Toto', 0, 4, None)
        self.assertEqual(preprocessor(token), token)
        token1 = tokenizer.Token('@BarackObama', 0, 4, None)
        token2 = tokenizer.Token('BarackObama', 0, 4, None)
        self.assertEqual(preprocessor(token1), token2)
        token1 = tokenizer.Token('@Barack_Obama', 0, 4, None)
        token2 = tokenizer.Token('Barack Obama', 0, 4, None)
        self.assertEqual(preprocessor(token1), token2)


if __name__ == '__main__':
    unittest2.main()

