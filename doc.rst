==================
Alignment project
==================

What is it for ?
================

This python library aims to help you to *align data*. For instance, you have a
list of cities, described by their name and their country and you would like to
find their URI on dbpedia to have more information about them, as the longitude and
the latitude for example. If you have two or three cities, it can be done with
bare hands, but it could not if there are hundreds or thousands cities.
This library provides you all the stuff we need to do it.


Introduction
============

The alignment process is divided into three main steps:

1. Gather and format the data we want to align.
   In this step, we define two sets called the `alignset` and the
   `targetset`. The `alignset` contains our data, and the
   `targetset` contains the data on which we would like to make the links.
2. Compute the similarity between the items gathered.  We compute a distance
   matrix between the two sets according to a given distance.
3. Find the items having a high similarity thanks to the distance matrix.

Simple case
-----------

1. Let's define `alignset` and `targetset` as simple python lists.

.. sourcecode:: python

    alignset = ['Victor Hugo', 'Albert Camus']
    targetset = ['Albert Camus', 'Guillaume Apollinaire', 'Victor Hugo']

2. Now, we have to compute the similarity between each items. For that purpose, the
   `Levenshtein distance <http://en.wikipedia.org/wiki/Levenshtein_distance>`_
   [#]_, which is well accurate to compute the distance between few words, is used.
   Such a function is provided in the `nazca.distance` module.

   The next step is to compute the distance matrix according to the Levenshtein
   distance. The result is given in the following tables.


   +--------------+--------------+-----------------------+-------------+
   |              | Albert Camus | Guillaume Apollinaire | Victor Hugo |
   +==============+==============+=======================+=============+
   | Victor Hugo  | 6            | 9                     | 0           |
   +--------------+--------------+-----------------------+-------------+
   | Albert Camus | 0            | 8                     | 6           |
   +--------------+--------------+-----------------------+-------------+

.. [#] Also called the *edit distance*, because the distance between two words
       is equal to the number of single-character edits required to change one
       word into the other.


3. The alignment process is ended by reading the matrix and saying items having a
   value inferior to a given threshold are identical.

A more complex one
------------------

The previous case was simple, because we had only one *attribute* to align (the
name), but it is frequent to have a lot of *attributes* to align, such as the name
and the birth date and the birth city. The steps remains the same, except that
three distance matrices will be computed, and *items* will be represented as
nested lists. See the following example:

.. sourcecode:: python

    alignset = [['Paul Dupont', '14-08-1991', 'Paris'],
                ['Jacques Dupuis', '06-01-1999', 'Bressuire'],
                ['Michel Edouard', '18-04-1881', 'Nantes']]
    targetset = [['Dupond Paul', '14/08/1991', 'Paris'],
                 ['Edouard Michel', '18/04/1881', 'Nantes'],
                 ['Dupuis Jacques ', '06/01/1999', 'Bressuire'],
                 ['Dupont Paul', '01-12-2012', 'Paris']]


In such a case, two distance functions are used, the Levenshtein one for the
name and the city and a temporal one for the birth date [#]_.

.. [#] Provided in the `nazca.distances` module.


The :func:`cdist` function of `nazca.distances` enables us to compute those
matrices :

.. sourcecode:: python

    >>> nazca.matrix.cdist([a[0] for a in alignset], [t[0] for t in targetset],
    >>>                    'levenshtein', matrix_normalized=False)
    array([[ 1.,  6.,  5.,  0.],
           [ 5.,  6.,  0.,  5.],
           [ 6.,  0.,  6.,  6.]], dtype=float32)

+----------------+-------------+----------------+----------------+-------------+
|                | Dupond Paul | Edouard Michel | Dupuis Jacques | Dupont Paul |
+================+=============+================+================+=============+
| Paul Dupont    | 1           | 6              | 5              | 0           |
+----------------+-------------+----------------+----------------+-------------+
| Jacques Dupuis | 5           | 6              | 0              | 5           |
+----------------+-------------+----------------+----------------+-------------+
| Edouard Michel | 6           | 0              | 6              | 6           |
+----------------+-------------+----------------+----------------+-------------+

.. sourcecode:: python

    >>> nazca.matrix.cdist([a[1] for a in alignset], [t[1] for t in targetset],
    >>>                    'temporal', matrix_normalized=False)
    array([[     0.,  40294.,   2702.,   7780.],
           [  2702.,  42996.,      0.,   5078.],
           [ 40294.,      0.,  42996.,  48074.]], dtype=float32)

+------------+------------+------------+------------+------------+
|            | 14/08/1991 | 18/04/1881 | 06/01/1999 | 01-12-2012 |
+============+============+============+============+============+
| 14-08-1991 | 0          | 40294      | 2702       | 7780       |
+------------+------------+------------+------------+------------+
| 06-01-1999 | 2702       | 42996      | 0          | 5078       |
+------------+------------+------------+------------+------------+
| 18-04-1881 | 40294      | 0          | 42996      | 48074      |
+------------+------------+------------+------------+------------+

.. sourcecode:: python

    >>> nazca.matrix.cdist([a[2] for a in alignset], [t[2] for t in targetset],
    >>>                    'levenshtein', matrix_normalized=False)
    array([[ 0.,  4.,  8.,  0.],
           [ 8.,  9.,  0.,  8.],
           [ 4.,  0.,  9.,  4.]], dtype=float32)

+-----------+-------+--------+-----------+-------+
|           | Paris | Nantes | Bressuire | Paris |
+===========+=======+========+===========+=======+
| Paris     | 0     | 4      | 8         | 0     |
+-----------+-------+--------+-----------+-------+
| Bressuire | 8     | 9      | 0         | 8     |
+-----------+-------+--------+-----------+-------+
| Nantes    | 4     | 0      | 9         | 4     |
+-----------+-------+--------+-----------+-------+


The next step is gathering those three matrices into a global one, called the
`global alignment matrix`. Thus we have :

+---+-------+-------+-------+-------+
|   | 0     | 1     | 2     | 3     |
+===+=======+=======+=======+=======+
| 0 | 1     | 40304 | 2715  | 7780  |
+---+-------+-------+-------+-------+
| 1 | 2715  | 43011 | 0     | 5091  |
+---+-------+-------+-------+-------+
| 2 | 40304 | 0     | 43011 | 48084 |
+---+-------+-------+-------+-------+

Allowing some misspelling mistakes (for example *Dupont* and *Dupond* are very
close), the matching threshold can be set to 1 or 2. Thus we can see that the
item 0 in our `alignset` is the same that the item 0 in the `targetset`, the
1 in the `alignset` and the 2 of the `targetset` too : the links can be
done !

It's important to notice that even if the item 0 of the `alignset` and the 3
of the `targetset` have the same name and the same birthplace they are
unlikely identical because of their very different birth date.


You may have noticed that working with matrices as I did for the example is a
little bit boring. The good news is that this project makes all this job for you. You
just have to give the sets and distance functions and that's all. An other good
news is the project comes with the needed functions to build the sets !


Real applications
=================

Just before we start, we will assume the following imports have been done:

.. sourcecode:: python

    from nazca import dataio as aldio #Functions for input and output data
    from nazca import distances as ald #Functions to compute the distances
    from nazca import normalize as aln#Functions to normalize data
    from nazca import aligner as ala  #Functions to align data

The Goncourt prize
------------------

On wikipedia, we can find the `Goncourt prize winners
<https://fr.wikipedia.org/wiki/Prix_Goncourt#Liste_des_laur.C3.A9ats>`_, and we
would like to establish a link between the winners and their URI on dbpedia
[#]_.

.. [#] Let's imagine the *Goncourt prize winners* category does not exist in
       dbpedia

We simply copy/paste the winners list of wikipedia into a file and replace all
the separators (`-` and `,`) by `#`. So, the beginning of our file is :

..

    | 1903#John-Antoine Nau#Force ennemie (Plume)
    | 1904#Léon Frapié#La Maternelle (Albin Michel)
    | 1905#Claude Farrère#Les Civilisés (Paul Ollendorff)
    | 1906#Jérôme et Jean Tharaud#Dingley, l'illustre écrivain (Cahiers de la Quinzaine)

When using the high-level functions of this library, each item must have at
least two elements: an *identifier* (the name, or the URI) and the *attribute* to
compare. With the previous file, we will use the name (so the column number 1)
as *identifier* (we don't have an *URI* here as identifier) and *attribute* to align.
This is told to python thanks to the following code:

.. sourcecode:: python

    alignset = aldio.parsefile('prixgoncourt', indexes=[1, 1], delimiter='#')

So, the beginning of our `alignset` is:

.. sourcecode:: python

    >>> alignset[:3]
    [[u'John-Antoine Nau', u'John-Antoine Nau'],
     [u'Léon Frapié', u'Léon, Frapié'],
     [u'Claude Farrère', u'Claude Farrère']]


Now, let's build the `targetset` thanks to a *sparql query* and the dbpedia
end-point:

.. sourcecode:: python

   query = """
        SELECT ?writer, ?name WHERE {
          ?writer  <http://purl.org/dc/terms/subject> <http://dbpedia.org/resource/Category:French_novelists>.
          ?writer rdfs:label ?name.
          FILTER(lang(?name) = 'fr')
       }
    """
    targetset = aldio.sparqlquery('http://dbpedia.org/sparql', query)

Both functions return nested lists as presented before. Now, we have to define
the distance function to be used for the alignment. This is done thanks to a
python dictionary where the keys are the columns to work on, and the values are
the treatments to apply.

.. sourcecode:: python

    treatments = {1: {'metric': ald.levenshtein}} #Use a levenshtein on the name

Finally, the last thing we have to do, is to call the :func:`alignall` function:

.. sourcecode:: python

    alignments = ala.alignall(alignset, targetset,
                           0.4, #This is the matching threshold
                           treatments,
                           mode=None,#We'll discuss about that later
                           uniq=True #Get the best results only
                          )

This function returns an iterator over the (different) carried out alignments.

.. sourcecode:: python

    for a, t in alignments:
        print '%s has been aligned onto %s' % (a, t)

It may be important to apply some pre-treatment on the data to align. For
instance, names can be written with lower or upper characters, with extra
characters as punctuation or unwanted information in parenthesis and so on. That
is why we provide some functions to ``normalize`` your data. The most useful may
be the :func:`simplify` function (see the docstring for more information). So the
treatments list can be given as follow:


.. sourcecode:: python

    def remove_after(string, sub):
        """ Remove the text after `sub` in `string`
            >>> remove_after('I like cats and dogs', 'and')
            'I like cats'
            >>> remove_after('I like cats and dogs', '(')
            'I like cats and dogs'
        """
        try:
            return string[:string.lower().index(sub)].strip()
        except ValueError:
            return string


    treatments = {1: {'normalization': [lambda x:remove_after(x, '('),
                                        aln.simply],
                      'metric': ald.levenshtein
                     }
                 }


Cities alignment
----------------

The previous case with the ``Goncourt prize winners`` was pretty simply because
the number of items was small, and the computation fast. But in a more real use
case, the number of items to align may be huge (some thousands or millions…). Is
such a case it's unthinkable to build the global alignment matrix because it
would be too big and it would take (at least...) fews days to achieve the computation.
So the idea is to make small groups of possible similar data to compute smaller
matrices (i.e. a *divide and conquer* approach).
For this purpose, we provide some functions to group/cluster data. We have
functions to group text and numerical data.


This is done by the following python code:

.. sourcecode:: python

    targetset = aldio.rqlquery('http://demo.cubicweb.org/geonames',
                               'Any U, N, LONG, LAT WHERE X is Location, X name'
                               ' N, X country C, C name "France", X longitude'
                               ' LONG, X latitude LAT, X population > 1000, X'
                               ' feature_class "P", X cwuri U',
                               indexes=[0, 1, (2, 3)])
    alignset = aldio.sparqlquery('http://dbpedia.inria.fr/sparql',
                                 'prefix db-owl: <http://dbpedia.org/ontology/>'
                                 'prefix db-prop: <http://fr.dbpedia.org/property/>'
                                 'select ?ville, ?name, ?long, ?lat where {'
                                 ' ?ville db-owl:country <http://fr.dbpedia.org/resource/France> .'
                                 ' ?ville rdf:type db-owl:PopulatedPlace .'
                                 ' ?ville db-owl:populationTotal ?population .'
                                 ' ?ville foaf:name ?name .'
                                 ' ?ville db-prop:longitude ?long .'
                                 ' ?ville db-prop:latitude ?lat .'
                                 ' FILTER (?population > 1000)'
                                 '}',
                                 indexes=[0, 1, (2, 3)])


    treatments = {1: {'normalization': [aln.simply],
                      'metric': ald.levenshtein,
                      'matrix_normalized': False
                     }
                 }
    results = ala.alignall(alignset, targetset, 3, treatments=treatments, #As before
                           indexes=(2, 2), #On which data build the kdtree
                           mode='kdtree',  #The mode to use
                           uniq=True) #Return only the best results


Let's explain the code. We have two files, containing a list of cities we want
to align, the first column is the identifier, and the second is the name of the
city and the last one is the location of the city (longitude and latitude), gathered
into a single tuple.

In this example, we want to build a *kdtree* on the couple (latitude, longitude)
to divide our data into a few candidates. This clustering is coarse, and is only
used to reduce the potential candidates without loosing any more refined
possible matches.

So, in the next step, we define the treatments to apply.
It is the same as before, but we ask for a non-normalized matrix
(i.e.: the real output of the levenshtein distance).
Thus, we call the :func:`alignall` function. `indexes` is a tuple saying the
position of the point on which the kdtree_ must be built, `mode` is the mode
used to find neighbours [#]_.

Finally, `uniq` ask to the function to return the best
candidate (i.e.: the one having the shortest distance below the given threshold)

.. [#] The available modes are `kdtree`, `kmeans` and `minibatch` for
       numerical data and `minhashing` for text one.

The function output a generator yielding tuples where the first element is the
identifier of the `alignset` item and the second is the `targetset` one (It
may take some time before yielding the first tuples, because all the computation
must be done…)

.. _kdtree: http://en.wikipedia.org/wiki/K-d_tree

The :func:`alignall_iterative` and `cache` usage
==========================================

Even when using methods such as `kdtree` or `minhashing` or `clustering`,
the alignment process might be long. That’s why we provide you a function,
called :func:`alignall_iterative` which works directly with your files. The idea
behind this function is simple, it splits your files (the `alignfile` and the
`targetfile`) into smallers ones and tries to align each item of each subsets.
When processing, if an alignment is estimated almost perfect
then the item aligned is _removed_ from the `alignset` to faster the process − so
Nazca doesn’t retry to align it.

Moreover, this function uses a cache system. When a alignment is done, it is
stored into the cache and if in the future a *better* alignment is found, the
cached is updated. At the end, you get only the better alignment found.

.. sourcecode:: python

    from difflib import SequenceMatcher

    from nazca import normalize as aln#Functions to normalize data
    from nazca import aligner as ala  #Functions to align data

    def approxMatch(x, y):
        return 1.0 - SequenceMatcher(None, x, y).ratio()

    alignformat = {'indexes': [0, 3, 2],
                   'formatopt': {0: lambda x:x.decode('utf-8'),
                                 1: lambda x:x.decode('utf-8'),
                                 2: lambda x:x.decode('utf-8'),
                                },
                  }

    targetformat = {'indexes': [0, 1, 3],
                   'formatopt': {0: lambda x:x.decode('utf-8'),
                                 1: lambda x:x.decode('utf-8'),
                                 3: lambda x:x.decode('utf-8'),
                                },
                  }

    tr_name = {'normalization': [aln.simplify],
               'metric': approxMatch,
               'matrix_normalized': False,
              }
    tr_info = {'normalization': [aln.simplify],
               'metric': approxMatch,
               'matrix_normalized': False,
               'weighting': 0.3,
              }

    alignments = ala.alignall_iterative('align_csvfile', 'target_csvfile',
                                        alignformat, targetformat, 0.20,
                                        treatments={1:tr_name,
                                                    2:tr_info,
                                                   },
                                        equality_threshold=0.05,
                                        size=25000,
                                        mode='minhashing',
                                        indexes=(1,1),
                                        neighbours_threshold=0.2,
                                       )

    with open('results.csv', 'w') as fobj:
        for aligned, (targeted, distance) in alignments.iteritems():
            fobj.write('%s\t%s\t%s\n' % (aligned, targeted, distance))

Roughly, this function expects the same arguments than the previously shown
:func:`alignall` function, excepting the `equality_threshold` and the `size`.

 - `size` is the number items to have in each subsets
 - `equality_threshold` is the threshold above which two items are said as
   equal.

`Try <http://demo.cubicweb.org/nazca/view?vid=nazca>`_ it online !
==================================================================

We have also made a little application of Nazca, using `CubicWeb
<http://www.cubicweb.org/>`_. This application provides a user interface for
Nazca, helping you to choose what you want to align. You can use sparql or rql
queries, as in the previous example, or import your own cvs file [#]_. Once you
have choosen what you want to align, you can click the *Next step* button to
customize the treatments you want to apply, just as you did before in python !
Once done, by clicking the *Next step*, you start the alignment process. Wait a
little bit, and you can either download the results in a *csv* or *rdf* file, or
directly see the results online choosing the *html* output.

.. [#] Your csv file must be tab-separated for the moment…
