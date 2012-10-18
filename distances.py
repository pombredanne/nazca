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

from dateutil import parser as dateparser

def levenshtein(stra, strb):
    """ Compute the Levenshtein distance between stra and strb.

    The Levenshtein distance is defined as the minimal cost to transform stra
    into strb, where 3 operators are allowed :
        - Replace one character of stra into a character of strb
        - Add one character of strb into stra
        - Remove one character of strb
    """

    lena = len(stra)
    lenb = len(strb)
    onerowago = None
    thisrow = range(1, lenb + 1) + [0]
    for x in xrange(lena):
        onerowago, thisrow = thisrow, [0] * lenb + [x+1]
        for y in xrange(lenb):
            delcost = onerowago[y] + 1
            addcost = thisrow[y - 1] + 1
            subcost = onerowago[y - 1] + (stra[x] != strb[y])
            thisrow[y] = min(delcost, addcost, subcost)
    return thisrow[lenb - 1]

def soundexcode(word, language = 'french'):
    """ Return the Soundex code of the word ``word``
        For more information about soundex code see wiki_

        ``language`` can be 'french' or 'english'

        .:: wiki_ : https://en.wikipedia.org/wiki/Soundex
    """

    if ' ' in word:
        words = word.split(' ')
        return ' '.join([soundexcode(w.strip(), language) for w in words])

    vowels = 'AEHIOUWY'
    if language.lower() == 'french' :
        consonnantscode = { 'B' : '1', 'P' : '1',
                            'C' : '2', 'K' : '2', 'Q' : '2',
                            'D' : '3', 'T' : '3',
                            'L' : '4',
                            'M' : '5', 'N' : '5',
                            'R' : '6',
                            'G' : '7', 'J' : '7',
                            'X' : '8', 'Z' : '8', 'S' : '8',
                            'F' : '9', 'V' : '9'
                          }
    elif language.lower() == 'english':
        consonnantscode = { 'B' : '1', 'F' : '1', 'P' : '1', 'V' : '1',
                            'C' : '2', 'G' : '2', 'J' : '2', 'K' : '2',
                            'Q' : '2', 'S' : '2', 'X' : '2', 'Z' : '2',
                            'D' : '3', 'T' : '3',
                            'L' : '4',
                            'M' : '5', 'N' : '5',
                            'R' : '6'
                          }
    else:
        raise NotImplementedError('Soundex code is not supported (yet ?) for'
                                  'this language')
    word = word.strip().upper()
    code = word[0]
    #After this ``for`` code is
    # the first letter of ``word`` followed by all the consonnants of word,
    # where from consecutive consonnants, only the first is kept,
    # and from two identical consonnants separated by a W or a H, only the first
    # is kept too.
    for i in xrange(1, len(word)):
        if word[i] in vowels:
            continue
        if word[i - 1] not in vowels and \
           consonnantscode[word[i]] == consonnantscode.get(code[-1], ''):
            continue
        if i + 2 < len(word) and word[i + 1] in 'WH' and \
           consonnantscode[word[i]] == consonnantscode.get(word[i + 2], ''):
            continue
        code += word[i]
    #Replace according to the codes
    code = code[0] + ''.join([consonnantscode[c] for c in code[1:]])
    ###First four letters, completed by zeros
    return code[:4] + '0' * (4 - len(code))

def soundex(stra, strb, language = 'french'):
    """ Return the 1/0 distance between the soundex code of stra and strb.
        0 means they have the same code, 1 they don't
    """
    return 0 if (soundexcode(stra, language) == soundexcode(strb, language)) \
             else 1

def jaccard(stra, strb):
    """ Return the jaccard distance between stra and strb, condering the letters
    set of stra and strb

    J(A, B) = (A \cap B) / (A \cup B)
    d(A, B) = 1 - J(A, B)
    """

    seta = set(stra)
    setb = set(strb)

    jab = 1.0 * len(seta.intersection(setb)) / len(seta.union(setb))
    return 1.0 - jab

def temporal(stra, strb, granularity = u'days', language = u'french',
             dayfirst = True, yearfirst = False):
    """ Return the distance between two strings (read as dates).

        ``granularity`` can be either ``days`` or ``months`` or ``years``
        (be careful to the plural form !)
        ``language`` can be either french or english

        ``dayfirst`` and ``yearfirst`` are used in case of ambiguity, for
        instance 09/09/09, by default it assumes it's day/month/year
    """
    class customparserinfo(dateparser.parserinfo):
        if language.lower() == u'french':
            HMS      = [(u'h', u'heure', u'heures'),
                        (u'm', u'minute', u'minutes'),
                        (u's', u'seconde', u'seconde'),]
            JUMP     = [u' ', u'.', u',', u';', u'-', u'/', u"'",
                        u'a', u'le', u'et', u'er']
            MONTHS   = [(u'Jan', u'Janvier'), (u'Fev', u'Fevrier'), (u'Mar', u'Mars'),
                       (u'Avr', u'Avril'), (u'Mai', u'Mai'), (u'Jun', u'Juin'),
                       (u'Jui', u'Juillet'), (u'Aou', u'Aout'),
                       (u'Sep', u'Septembre'), (u'Oct', u'Octobre'),
                       (u'Nov', u'Novembre'), (u'Dec', u'Decembre'),]
            PERTAIN  = [u'de']
            WEEKDAYS = [(u'Lun', u'Lundi'),
                        (u'Mar', u'Mardi'),
                        (u'Mer', u'Mercredi'),
                        (u'Jeu', u'Jeudi'),
                        (u'Ven', u'Vendredi'),
                        (u'Sam', u'Samedi'),
                        (u'Dim', u'Dimanche'),]
    datea = dateparser.parse(stra, parserinfo = customparserinfo(dayfirst,
                             yearfirst), fuzzy = True)
    dateb = dateparser.parse(strb, parserinfo = customparserinfo(dayfirst,
                             yearfirst), fuzzy = True)
    diff  = datea - dateb
    if granularity.lower() == 'years':
        return abs(diff.days / 365.25)
    if granularity.lower() == 'months':
        return abs(diff.days / 30.5)
    return abs(diff.days)

def euclidean(a, b):
    try:
        return abs(a - b)
    except TypeError:
        return abs(float(a) - float(b))
