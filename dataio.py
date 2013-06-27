# -*- coding: utf-8 -*-
""" IO for Named Entities Recognition.
"""
import json
import urllib
import lxml.etree as ET


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

    def pprint_text(self, text, named_entities, **kwargs):
        newtext = u''
        indice = 0
        tindices = dict([(t.start, (uri, t)) for uri, p, t in named_entities])
        while indice < len(text):
            if indice in tindices:
                uri, t = tindices[indice]
                words = text[t.start:t.end]
                fragment = self.pprint_entity(uri, words, **kwargs)
                if not self.is_valid(newtext+fragment+text[t.end:]):
                    fragment = words
                newtext += fragment
                indice = t.end
            else:
                newtext += text[indice]
                indice += 1
        return newtext

    def pprint_entity(self, uri, word, **kwargs):
        """ Pretty print an entity """
        raise NotImplementedError

    def is_valid(self, newtext):
        """Override to check the validity of the prettified content at each
        enrichement step"""
        return True


class NerdyHTMLPrettyPrint(AbstractNerdyPrettyPrint):
    """ Pretty print the output of a Nerdy process
    """

    def pprint_entity(self, uri, word, **kwargs):
        """ Pretty print an entity """
        return u'<a href="%s">%s</a>' % (uri, word)


class NerdyValidXHTMLPrettyPrint(NerdyHTMLPrettyPrint):

    XHTML_DOC_TEMPLATE = '''\
<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="content-type" content="text/html; charset=UTF-8"/>
<title>nerdy</title>
</head>
<body><div>%s</div></body>
</html>'''

    def is_valid(self, html):
        try:
            ET.fromstring(self.XHTML_DOC_TEMPLATE % html.encode('utf-8'),
                          parser=ET.XMLParser(dtd_validation=True))
        except ET.XMLSyntaxError:
            return False
        return True
