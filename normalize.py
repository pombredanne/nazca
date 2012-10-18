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

import re
from logilab.common.textutils import unormalize
from nltk.tokenize import WordPunctTokenizer 

class Normalizer(object):
    """ Use an object of this class to normalize your data """

    def __init__(self, lemmasfilename = 'data/french_lemmas.txt'):
        self.lemmas = None
        self.lemmasfilename = lemmasfilename

    def unormalize(self, sentence):
        """ Normalize a sentence (ie remove accents, set to lower, etc) """
        return unormalize(sentence).lower()

    def tokenize(self, sentence, tokenizer = None):
        """ Tokenize a sentence.
            Use ``tokenizer`` if given, else 
            nltk.tokenize.regexp.WordPunctTokenizer

            Anyway, tokenizer must have a ``tokenize()`` method
        """
        tokenizer = tokenizer or WordPunctTokenizer
        return [w for w in tokenizer().tokenize(sentence)]

    def _deflemmas(self):
        """ Return the default lemmas dictionnary
        """
        return dict([line.strip().split('\t') 
                     for line in open(self.lemmasfilename)
                         if len(line.strip().split('\t'))==2])

    def lemmatized(self, sentence, tokenizer = None, lemmas = None):
        """ Return the lemmatized sentence
        """
        self.lemmas = lemmas or self.lemmas or self._deflemmas()
        return [self.lemmatized_word(w, self.lemmas)
                for w in self.tokenize(sentence, tokenizer)]

    def lemmatized_word(self, word, lemmas = None):
        """ Return the lemmatized word
        """
        self.lemmas = lemmas or self.lemmas or self._deflemmas()
        lemma = lemmas.get(word.lower(), word)
        if '|' in lemma:
            _words = lemma.split('|')
            if word.lower() in _words:
                lemma = word.lower()
            else:
                lemma = _words[0]
        return lemma

    def round(self, number, ndigits = 0):
        """Return an unicode string of ``number`` rounded to a given precision
            in decimal digits (default 0 digits)

            If ``number`` is not a float, this method casts it to a float. (An
            exception can be raised if it's not possible)
        """

        return format(round(float(number), ndigits), '0.%df' % ndigits)

    def format(self, string, regexp, output):
        """ Apply the regexp to the ``string`` and return a formatted string
        according to ``output``

        eg :
         normalizer.format(u'[Victor Hugo - 26 fev 1802 / 22 mai 1885]',
                           r'\[(?P<firstname>\w+) (?p<lastname>\w+) - '
                           r'(?P<birthdate>.*?) / (?<deathdate>.*?)\]',
                           u'%(lastname)s, %(firstname)s (%(birthdate)s -'
                           u'%(deathdate)s)')

         would return u'Hugo, Victor (26 fev 1802 - 22 mai 1885)'
         """

        match = re.match(regexp, string)
        return output % match.groupdict()
