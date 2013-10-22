=====================================================
 NERDY - A Named Entities Recognition python Library
=====================================================

Examples of NerdySource
=======================


NerdySourceSparql
-----------------

Simple NerdySourceSparql on Dbpedia sparql endpoint::

   .. sourcecode:: python

   >>> from nerdy.core import NerdySourceSparql
   >>> ner_source = NerdySourceSparql('''SELECT distinct ?uri
                                         WHERE{
                                         ?uri rdfs:label "%(word)s"@en}''',
			                 'http://dbpedia.org/sparql')
   >>> print ner_source.query_word('Victor Hugo')
   ...     ['http://dbpedia.org/resource/Category:Victor_Hugo',
	    'http://dbpedia.org/resource/Victor_Hugo',
	    'http://dbpedia.org/class/yago/VictorHugo',
	    'http://dbpedia.org/class/yago/VictorHugo(ParisM%C3%A9tro)',
	    'http://sw.opencyc.org/2008/06/10/concept/en/VictorHugo',
	    'http://sw.opencyc.org/2008/06/10/concept/Mx4rve1ZXJwpEbGdrcN5Y29ycA']


With restriction in the SPARQL query::

   .. sourcecode:: python

   >>> from nerdy.core import NerdySourceSparql
   >>> ner_source = NerdySourceSparql('''SELECT distinct ?uri
                                         WHERE{
                                         ?uri rdfs:label "%(word)s"@en .
                                         ?p foaf:primaryTopic ?uri}''',
			                 'http://dbpedia.org/sparql')
   >>> print ner_source.query_word('Victor Hugo')
   ...    ['http://dbpedia.org/resource/Victor_Hugo']



NerdySourceUrlRql
-----------------

Simple NerdySourceUrlRql on a Rql endpoint::

   .. sourcecode:: python

   >>> from nerdy.core import NerdySourceUrlRql
   >>> ner_source = NerdySourceUrlRql('Any U WHERE X cwuri U, X name "%(word)s"',
		                        'http://www.cubicweb.org')
   >>> print ner_source.query_word('apycot')
   ...     [u'http://www.cubicweb.org/1310453', u'http://www.cubicweb.org/749162']



Examples of full Nerdy process
==============================


1 - Define some text
--------------------

For example, this text comes from Dbpedia (http://dbpedia.org/page/Victor_Hugo)::

    .. sourcecode:: python

   >>> from nerdy import core, dataio

   >>> text = u"""Victor Hugo, né le 26 février 1802 à Besançon et mort le 22 mai 1885 à Paris, est un poète, dramaturge et prosateur romantique considéré comme l'un des plus importants écrivains de langue française. Il est aussi une personnalité politique et un intellectuel engagé qui a compté dans l'Histoire du XIX siècle. Victor Hugo occupe une place marquante dans l'histoire des lettres françaises au XIX siècle, dans des genres et des domaines d'une remarquable variété. Il est poète lyrique avec des recueils comme Odes et Ballades (1826), Les Feuilles d'automne (1831) ou Les Contemplations (1856), mais il est aussi poète engagé contre Napoléon III dans Les Châtiments (1853) ou encore poète épique avec La Légende des siècles (1859 et 1877). Il est également un romancier du peuple qui rencontre un grand succès populaire avec par exemple Notre-Dame de Paris (1831), et plus encore avec Les Misérables (1862). Au théâtre, il expose sa théorie du drame romantique dans sa préface de Cromwell en 1827 et l'illustre principalement avec Hernani en 1830 et Ruy Blas en 1838. Son œuvre multiple comprend aussi des discours politiques à la Chambre des pairs, à l'Assemblée constituante et à l'Assemblée législative, notamment sur la peine de mort, l'école ou l'Europe, des récits de voyages (Le Rhin, 1842, ou Choses vues, posthumes, 1887 et 1890), et une correspondance abondante. Victor Hugo a fortement contribué au renouvellement de la poésie et du théâtre ; il a été admiré par ses contemporains et l'est encore, mais il a été aussi contesté par certains auteurs modernes. Il a aussi permis à de nombreuses générations de développer une réflexion sur l'engagement de l'écrivain dans la vie politique et sociale grâce à ses multiples prises de position qui le condamneront à l'exil pendant les vingt ans du Second Empire. Ses choix, à la fois moraux et politiques, durant la deuxième partie de sa vie, et son œuvre hors du commun ont fait de lui un personnage emblématique que la Troisième République a honoré à sa mort le 22 mai 1885 par des funérailles nationales qui ont accompagné le transfert de sa dépouille au Panthéon de Paris, le 31 mai 1885."""


2 - Define a source
-------------------

Now, define a source for the Named Entities::

    .. sourcecode:: python

    >>> dbpedia_sparql_source = core.NerdySourceSparql('''SELECT distinct ?uri
             		       				 WHERE{
 							 ?uri rdfs:label "%(word)s"@en .
 							 ?p foaf:primaryTopic ?uri}''',
 							 'http://dbpedia.org/sparql',
 							 use_cache=True)
    >>> nerdy_sources = [dbpedia_sparql_source,]


3 - Define some preprocessors
-----------------------------

Define some preprocessors that will cleanup the words before matching::

    .. sourcecode:: python

    >>> preprocessors = [core.NerdyLowerCaseFilterPreprocessor(),
        	         core.NerdyStopwordsFilterPreprocessor()]


4 - Define the Nerdy process
----------------------------

Define the process and process the text::

    .. sourcecode:: python

    >>> nerdy = core.NerdyProcess(nerdy_sources, preprocessors=preprocessors)
    >>> named_entities = nerdy.process_text(text)
    >>> print named_entities


5 - Pretty priint the output
----------------------------

And finally, we can print the output as HTML with links::

    .. sourcecode:: python

    >>> html = dataio.NerdyHTMLPrettyPrint().pprint_text(text, named_entities)
    >>> print html
