# -*- coding: utf-8 -*-
""" Core functions for Named Entities Recognition.
"""
from nazca.utils.tokenizer import RichStringTokenizer, Token
from nazca.utils.dataio import sparqlquery
from nazca.reference_data.stopwords import FRENCH_STOPWORDS, ENGLISH_STOPWORDS

STOPWORDS = {'fr': FRENCH_STOPWORDS,
             'en': ENGLISH_STOPWORDS}


###############################################################################
### NER PREPROCESSORS #########################################################
###############################################################################
class AbstractNerdyPreprocessor(object):
    """ Preprocessor
    """

    def __call__(self, token):
        raise NotImplementedError


class NerdyWordSizeFilterPreprocessor(AbstractNerdyPreprocessor):
    """ Remove token based on the size of the word
    """
    def __init__(self, min_size=None, max_size=None):
        self.min_size = min_size
        self.max_size = max_size

    def __call__(self, token):
        if ((self.min_size and len(token.word)<self.min_size)
            or (self.max_size and len(token.word)>self.max_size)):
            return None
        return token


class NerdyLowerCaseFilterPreprocessor(AbstractNerdyPreprocessor):
    """ Remove token with word in lower case
    """

    def __call__(self, token):
        return None if token.word.islower() else token


class NerdyLowerFirstWordPreprocessor(AbstractNerdyPreprocessor):
    """ Lower the first word of each sentence if it is a stopword.
    """
    def __init__(self, lang='en'):
        self.lang = lang

    def __call__(self, token):
        if (token.start == token.sentence.start and
            token.word.split()[0].lower() in STOPWORDS.get(self.lang, ENGLISH_STOPWORDS)):
            word = token.word[0].lower() + token.word[1:]
            return Token(word, token.start, token.end, token.sentence)
        return token


class NerdyStopwordsFilterPreprocessor(AbstractNerdyPreprocessor):
    """ Remove stopwords
    """
    def __init__(self, split_words=False, lang='en'):
        self.split_words = split_words
        self.lang = lang

    def __call__(self, token):
        stopwords = STOPWORDS.get(self.lang, ENGLISH_STOPWORDS)
        if self.split_words and not [w for w in token.word.split() if w.lower() not in stopwords]:
            return None
        if not self.split_words and token.word.lower() in stopwords:
            return None
        return token


class NerdyHashTagPreprocessor(AbstractNerdyPreprocessor):
    """ Cleanup hashtag
    """
    def __call__(self, token):
        if token.word.startswith('@'):
            # XXX Split capitalize letter ?
            # @BarackObama -> Barack Obama
            word = token.word[1:].replace('_', ' ')
            return Token(word, token.start, token.end, token.sentence)
        return token


###############################################################################
### NER FILTERS ###############################################################
###############################################################################
class AbstractNerdyFilter(object):
    """ A filter used for cleaning named entities results
    """

    def __call__(self, named_entities):
        raise NotImplementedError


class NerdyOccurenceFilter(object):
    """ A filter based on the number of occurence of
    named entities in the results.
    """
    def __init__(self, min_occ=None, max_occ=None):
        self.min_occ = min_occ
        self.max_occ = max_occ

    def __call__(self, named_entities):
        uris = [u for u, p, t in named_entities]
        counts = dict([(u, uris.count(u)) for u in set(uris)])
        return [n for n in named_entities if not ((self.min_occ and counts[n[0]]<self.min_occ)
                                              or (self.max_occ and counts[n[0]]>self.max_occ))]


class NerdyRDFTypeFilter(object):
    """ A filter based on the RDF type on entity
    E.g.

    filter = NerdyRDFTypeFilter('http://dbpedia.org/sparql',
                                ('http://schema.org/Place',
                                'http://dbpedia.org/ontology/Agent',
                                'http://dbpedia.org/ontology/Place'))

    """
    def __init__(self, endpoint, accepted_types):
        self.endpoint = endpoint
        self.accepted_types = accepted_types
        self.query = 'SELECT ?type WHERE{<%(uri)s> rdf:type ?type}'

    def __call__(self, named_entities):
        filtered_named_entities = []
        seen_uris = {}
        for uri, p, t in named_entities:
            if uri in seen_uris:
                if seen_uris[uri]:
                    filtered_named_entities.append((uri, p, t))
            else:
                results = sparqlquery(self.endpoint, self.query % {'uri': uri})
                types = set([r['type']['value'] for r in results])
                if not len(types.intersection(self.accepted_types)):
                    seen_uris[uri] = False
                else:
                    seen_uris[uri] = True
                    filtered_named_entities.append((uri, p, t))
        return filtered_named_entities


class NerdyDisambiguationWordParts(object):
    """ Disambiguate named entities based on the words parts.
    E.g.:
          'toto tutu': 'http://example.com/toto_tutu',
          'toto': 'http://example.com/toto'

          Then if 'toto' is found in the text, replace the URI 'http://example.com/toto'
          by 'http://example.com/toto_tutu'
    """
    def __call__(self, named_entities):
        # Create parts dictionnary
        parts = {}
        for uri, peid, token in named_entities:
            if ' ' in token.word:
                for part in token.word.split(' '):
                    parts[part.lower()] = uri
        # Replace named entities
        filtered_named_entities = []
        for uri, peid, token in named_entities:
            if token.word in parts:
                # Change URI
                uri = parts[token.word]
            filtered_named_entities.append((uri, peid, token))
        return filtered_named_entities


class NerdyReplacementRulesFilter(object):
    """ Allow to define replacement rules for Named Entities
    """
    def __init__(self,rules):
        self.rules = rules

    def __call__(self, named_entities):
        filtered_named_entities = []
        for uri, peid, token in named_entities:
            uri = self.rules.get(uri, uri)
            filtered_named_entities.append((uri, peid, token))
        return filtered_named_entities


###############################################################################
### NER PROCESS ###############################################################
###############################################################################
class NerdyProcess(object):
    """ High-level process for Named Entities Recognition
    """

    def __init__(self, ner_sources, preprocessors=None, filters=None, unique=False):
        """ Initialise the class.

        :tokenizer: an instance of tokenizer
        """
        self.ner_sources = list(ner_sources)
        self.preprocessors = preprocessors or []
        self.filters = filters or []
        self.unique = unique

    def add_ner_source(self, process):
        """ Add a ner process
        """
        self.ner_sources.append(process)

    def add_preprocessors(self, preprocessor):
        """ Add a preprocessor
        """
        self.preprocessors.append(preprocessor)

    def add_filters(self, filter):
        """ Add a filter
        """
        self.filters.append(filter)

    def process_text(self, text):
        """ High level function for analyzing a text
        """
        tokenizer = RichStringTokenizer(text)
        return self.recognize_tokens(tokenizer)

    def recognize_tokens(self, tokens):
        """ Recognize Named Entities from a tokenizer or
        an iterator yielding tokens.
        """
        last_stop = 0
        named_entities = []
        for token in tokens:
            if token.start < last_stop:
                continue # this token overlaps with a previous match
            word = token.word
            # Applies preprocessors
            # XXX Preprocessors may be sources dependant
            for preprocessor in self.preprocessors:
                token = preprocessor(token)
                if not token:
                    break
            if not token:
                continue
            recognized = False
            for process in self.ner_sources:
                for uri in process.recognize_token(token):
                    named_entities.append((uri, process.name, token))
                    recognized = True
                    last_stop = token.end
                    if self.unique:
                        break
                if recognized and self.unique:
                    break
        # XXX Postprocess/filters may be sources dependant
        return self.postprocess(named_entities)

    def postprocess(self, named_entities):
        """ Postprocess the results by applying filters """
        for filter in self.filters:
            named_entities = filter(named_entities)
        return named_entities


###############################################################################
### NER RELATIONS PROCESS #####################################################
###############################################################################
class NerdyRelationsProcess(object):
    """ Process for building simple relation from named entities results
    """
    pass
