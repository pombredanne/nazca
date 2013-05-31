# -*- coding: utf-8 -*-
""" IO for Named Entities Recognition.
"""
import json
import urllib


###############################################################################
### SPARQL UTILITIES ##########################################################
###############################################################################
def sparql_query(query, endpoint):
    """ Execute a query on an endpoint:

    sparql_query(query=u'''SELECT ?uri ?type
                           WHERE{
                           ?uri rdfs:label "Python"@en .
                           ?uri rdf:type ?type}''',
                           endpoint=u'http://dbpedia.org/sparql')
    """
    from SPARQLWrapper import SPARQLWrapper, JSON
    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    try:
        rawresults = sparql.query().convert()
        labels = rawresults['head']['vars']
        return rawresults["results"]["bindings"]
    except:
        print 'Error in sparql query'
        return []


###############################################################################
### RQL UTILITIES #############################################################
###############################################################################
def get_cw_cnx(endpoint):
    """ Get a cnx on a CubicWeb database
    """
    from cubicweb import dbapi
    from cubicweb.cwconfig import CubicWebConfiguration
    from cubicweb.entities import AnyEntity
    CubicWebConfiguration.load_cwctl_plugins()
    config = CubicWebConfiguration.config_for(endpoint)
    sourceinfo = config.sources()['admin']
    login = sourceinfo['login']
    password = sourceinfo['password']
    _, cnx = dbapi.in_memory_repo_cnx(config, login, password=password)
    req = cnx.request()
    return req

def rql_appid_query(query, endpoint, _cache_cnx={}, **kwargs):
    """ Execute a query on an appid endpoint:

    rql_query('Any X WHERE X label "Python"', 'localhost')

    Additional arguments can be passed to be properly substitued
    in the execute() function.
    """
    if endpoint in _cache_cnx:
        cnx = _cache_cnx[endpoint]
    else:
        cnx = get_cw_cnx(endpoint)
        _cache_cnx[endpoint] = cnx
    return cnx.execute(query, kwargs)

def rql_url_query(query, endpoint):
    """ Execute a query on an url endpoint:

    rql_query('Any X WHERE X label "Python"', 'localhost')
    """
    url = urllib.basejoin(endpoint, '?rql=%s&vid=jsonexport' % query)
    return json.loads(urllib.urlopen(url).read())


###############################################################################
### OUTPUT UTILITIES ##########################################################
###############################################################################
class AbstractNerdyPrettyPrint(object):
    """ Pretty print the output of a Nerdy process
    """

    def pprint_text(self, text, named_entities):
        newtext = u''
        indice = 0
        tindices = dict([(t.start, (uri, t)) for uri, p, t in named_entities])
        while indice < len(text):
            if indice in tindices:
                uri, t = tindices[indice]
                newtext += self.pprint_entity(uri, text[t.start:t.end])
                indice = t.end
            else:
                newtext += text[indice]
                indice += 1
        return newtext

    def pprint_entity(self, uri, word):
        """ Pretty print an entity """
        raise NotImplementedError


class NerdyHTMLPrettyPrint(AbstractNerdyPrettyPrint):
    """ Pretty print the output of a Nerdy process
    """

    def pprint_entity(self, uri, word):
        """ Pretty print an entity """
        return u'<a href="%s">%s</a>' % (uri, word)



