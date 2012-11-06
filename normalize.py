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

from string import punctuation
from warnings import warn
from unicodedata import normalize as _uninormalize

from nltk.tokenize import WordPunctTokenizer


STOPWORDS = set([u'alors', u'au', u'aucuns', u'aussi', u'autre', u'avant',
u'avec', u'avoir', u'bon', u'car', u'ce', u'cela', u'ces', u'ceux', u'chaque',
u'ci', u'comme', u'comment', u'dans', u'des', u'du', u'dedans', u'dehors',
u'depuis', u'deux', u'devrait', u'doit', u'donc', u'dos', u'droite', u'début',
u'elle', u'elles', u'en', u'encore', u'essai', u'est', u'et', u'eu', u'fait',
u'faites', u'fois', u'font', u'force', u'haut', u'hors', u'ici', u'il', u'ils',
u'je', u'juste', u'la', u'le', u'les', u'leur', u'là', u'ma', u'maintenant',
u'mais', u'mes', u'mine', u'moins', u'mon', u'mot', u'même', u'ni', u'nommés',
u'notre', u'nous', u'nouveaux', u'ou', u'où', u'par', u'parce', u'parole',
u'pas', u'personnes', u'peut', u'peu', u'pièce', u'plupart', u'pour',
u'pourquoi', u'quand', u'que', u'quel', u'quelle', u'quelles', u'quels', u'qui',
u'sa', u'sans', u'ses', u'seulement', u'si', u'sien', u'son', u'sont', u'sous',
u'soyez', u'sujet', u'sur', u'ta', u'tandis', u'tellement', u'tels', u'tes',
u'ton', u'tous', u'tout', u'trop', u'très', u'tu', u'valeur', u'voie',
u'voient', u'vont', u'votre', u'vous', u'vu', u'ça', u'étaient', u'état',
u'étions', u'été', u'être'])

MANUAL_UNICODE_MAP = {
    u'\xa1': u'!',    # INVERTED EXCLAMATION MARK
    u'\u0142': u'l',  # LATIN SMALL LETTER L WITH STROKE
    u'\u2044': u'/',  # FRACTION SLASH
    u'\xc6': u'AE',   # LATIN CAPITAL LETTER AE
    u'\xa9': u'(c)',  # COPYRIGHT SIGN
    u'\xab': u'"',    # LEFT-POINTING DOUBLE ANGLE QUOTATION MARK
    u'\xe6': u'ae',   # LATIN SMALL LETTER AE
    u'\xae': u'(r)',  # REGISTERED SIGN
    u'\u0153': u'oe', # LATIN SMALL LIGATURE OE
    u'\u0152': u'OE', # LATIN CAPITAL LIGATURE OE
    u'\xd8': u'O',    # LATIN CAPITAL LETTER O WITH STROKE
    u'\xf8': u'o',    # LATIN SMALL LETTER O WITH STROKE
    u'\xbb': u'"',    # RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK
    u'\xdf': u'ss',   # LATIN SMALL LETTER SHARP S
    }

def unormalize(ustring, ignorenonascii=None, substitute=None):
    """replace diacritical characters with their corresponding ascii characters

    Convert the unicode string to its long normalized form (unicode character
    will be transform into several characters) and keep the first one only.
    The normal form KD (NFKD) will apply the compatibility decomposition, i.e.
    replace all compatibility characters with their equivalents.

    :type substitute: str
    :param substitute: replacement character to use if decomposition fails

    :see: Another project about ASCII transliterations of Unicode text
          http://pypi.python.org/pypi/Unidecode
    """
    # backward compatibility, ignorenonascii was a boolean
    if ignorenonascii is not None:
        warn("ignorenonascii is deprecated, use substitute named parameter instead",
             DeprecationWarning, stacklevel=2)
        if ignorenonascii:
            substitute = ''
    res = []
    for letter in ustring[:]:
        try:
            replacement = MANUAL_UNICODE_MAP[letter]
        except KeyError:
            replacement = _uninormalize('NFKD', letter)[0]
            if ord(replacement) >= 2 ** 7:
                if substitute is None:
                    raise ValueError("can't deal with non-ascii based characters")
                replacement = substitute
        res.append(replacement)
    return u''.join(res)

def lunormalize(sentence):
    """ Normalize a sentence (ie remove accents, set to lower, etc) """
    return unormalize(sentence).lower()

def simplify(sentence, lemmas = None, removeStopWords = True):
    """ Simply the given sentence
        0) If removeStopWords, then remove the stop word
        1) If lemmas are given, the sentence is lemmatized
        2) Set the sentence to lower case
        3) Remove punctuation
    """
    if lemmas:
        sentence = lemmatized(sentence, lemmas)
    sentence = sentence.lower()
    cleansent = ''
    for s in sentence:
        if s not in punctuation:
            cleansent += s

    if not removeStopWords:
        return cleansent
    else:
        return ' '.join([w for w in cleansent.split(' ') if w not in STOPWORDS])


def tokenize(sentence, tokenizer = None):
    """ Tokenize a sentence.
        Use ``tokenizer`` if given, else
        nltk.tokenize.regexp.WordPunctTokenizer

        Anyway, tokenizer must have a ``tokenize()`` method
    """
    tokenizer = tokenizer or WordPunctTokenizer
    return [w for w in tokenizer().tokenize(sentence)]

def wordgrams(sentence, k):
    """ Generator of k-wordgrams on the given sentence
    """
    words = sentence.split(' ')
    for r in xrange(len(words)):
        yield ' '.join(words[r:r + k])

def loadlemmas(filename):
    """ Return the default lemmas dictionnary
    """
    return dict([line.strip().split('\t')
                 for line in open(filename)
                     if len(line.strip().split('\t'))==2])

def lemmatized(sentence, lemmas, tokenizer = None):
    """ Return the lemmatized sentence
    """
    tokenized_sent = tokenize(sentence, tokenizer)
    tokenized_sentformated = []
    for w in tokenized_sent:
        if w in ".,'" and len(tokenized_sentformated) > 0:
            tokenized_sentformated[-1] += w
        elif w not in punctuation:
            tokenized_sentformated.append(w)

    return ' '.join([lemmatized_word(w, lemmas)
                     for w in tokenized_sentformated])

def lemmatized_word(word, lemmas):
    """ Return the lemmatized word
    """
    lemma = lemmas.get(word.lower(), word)
    if '|' in lemma:
        _words = lemma.split('|')
        if word.lower() in _words:
            lemma = word.lower()
        else:
            lemma = _words[0]
    return lemma

def roundstr(number, ndigits = 0):
    """Return an unicode string of ``number`` rounded to a given precision
        in decimal digits (default 0 digits)

        If ``number`` is not a float, this method casts it to a float. (An
        exception may be raised if it's not possible)
    """

    return format(round(float(number), ndigits), '0.%df' % ndigits)

def rgxformat(string, regexp, output):
    """ Apply the regexp to the ``string`` and return a formatted string
    according to ``output``

    eg :
        format(u'[Victor Hugo - 26 fev 1802 / 22 mai 1885]',
               r'\[(?P<firstname>\w+) (?p<lastname>\w+) - '
               r'(?P<birthdate>.*?) / (?<deathdate>.*?)\]',
               u'%(lastname)s, %(firstname)s (%(birthdate)s -'
               u'%(deathdate)s)')

     would return u'Hugo, Victor (26 fev 1802 - 22 mai 1885)'
     """

    match = re.match(regexp, string)
    return output % match.groupdict()
