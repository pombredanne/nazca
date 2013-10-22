
===========================================================
 NAZCA - Python library for practical semantics datamining
===========================================================

Nazca is a Python library to help you enhance and mine your data,
with a strong focus on semantics information.

In particular, it helps you:

 * interact with SPARQL endpoints and reference databases.

 * align your data (`record linkage`), i.e. link data from
   your database to data in other databases.


Record linkage
==============

Record linkage (or alignment) is the task that constists in linking together data from two different
sets, based on some distances between attributes.

For instance, you have a list of cities, described by their name
and their country and you would like to
find their URI on dbpedia to have more information about them, as the longitude and
the latitude for example. If you have two or three cities, it can be done with
bare hands, but it could not if there are hundreds or thousands cities.
This library provides you all the stuff we need to do it.



Introduction
~~~~~~~~~~~~

The record linkage process is divided into three main steps:

1. Gather and format the data we want to align.
   In this step, we define two sets called the `referenceset` and the
   `targetset`. The `referenceset` contains our data, and the
   `targetset` contains the data on which we would like to make the links.

2. Compute the similarity between the items gathered.  We compute a distance
   matrix between the two sets according to a given distance.

3. Find the items having a high similarity thanks to the distance matrix.



Simple case
~~~~~~~~~~~

1. Let's define `referenceset` and `targetset` as simple python lists.

.. sourcecode:: python

    referenceset = ['Victor Hugo', 'Albert Camus']
    targetset = ['Albert Camus', 'Guillaume Apollinaire', 'Victor Hugo']

2. Now, we have to compute the similarity between each items. For that purpose, the
   `Levenshtein distance <http://en.wikipedia.org/wiki/Levenshtein_distance>`_
   [#]_, which is well accurate to compute the distance between few words, is used.
   Such a function is provided in the `nazca.distances` module.

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

    >>> referenceset = [['Paul Dupont', '14-08-1991', 'Paris'],
		['Jacques Dupuis', '06-01-1999', 'Bressuire'],
		['Michel Edouard', '18-04-1881', 'Nantes']]
    >>> targetset = [['Dupond Paul', '14/08/1991', 'Paris'],
		['Edouard Michel', '18/04/1881', 'Nantes'],
                ['Dupuis Jacques ', '06/01/1999', 'Bressuire'],
                ['Dupont Paul', '01-12-2012', 'Paris']]


In such a case, two distance functions are used, the Levenshtein one for the
name and the city and a temporal one for the birth date [#]_.

.. [#] Provided in the `nazca.distances` module.


The :func:`cdist` function of `nazca.distances` enables us to compute those
matrices :

.. sourcecode:: python

    >>> from nazca.distances import levenshtein, cdist
    >>> cdist(levenshtein,[a[0] for a in referenceset],
    >>>       [t[0] for t in targetset], matrix_normalized=False)
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

    >>> from nazca.distances import temporal
    >>> cdist(temporal, [a[1] for a in referenceset], [t[1] for t in targetset],
    >>>       matrix_normalized=False)
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

    >>> cdist(levenshtein, [a[2] for a in referenceset], [t[2] for t in targetset],
    >>>       matrix_normalized=False)
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
item 0 in our `referenceset` is the same that the item 0 in the `targetset`, the
1 in the `referenceset` and the 2 of the `targetset` too : the links can be
done !

It's important to notice that even if the item 0 of the `referenceset` and the 3
of the `targetset` have the same name and the same birthplace they are
unlikely identical because of their very different birth date.


You may have noticed that working with matrices as I did for the example is a
little bit boring. The good news is that this module makes all this job for you. You
just have to give the sets and distance functions and that's all. An other good
news is this module comes with the needed functions to build the sets !


Real applications
~~~~~~~~~~~~~~~~~


The Goncourt prize
------------------

On wikipedia, we can find the `Goncourt prize winners
<http://fr.wikipedia.org/wiki/Prix_Goncourt#Liste_des_laur.C3.A9ats>`_, and we
would like to establish a link between the winners and their URI on dbpedia
[#]_.

.. [#] Let's imagine the *Goncourt prize winners* category does not exist in
       dbpedia

We simply copy/paste the winners list of wikipedia into a file and cleanup
it a bit. So, the beginning of our file is :

..

    | 1903	John-Antoine Nau
    | 1904	Léon Frapié
    | 1905	Claude Farrère


When using the high-level functions of this library, each item must have at
least two elements: an *identifier* (the name, or the URI) and the *attribute* to
compare.
For now, the *identifier*

 With the previous file, we will use the name (so the column number 1)
as *identifier* (we don't have an *URI* here as identifier) and *attribute* to align.
This is told to python thanks to the following code:

.. sourcecode:: python

   >>> import os.path as osp
   >>> from nazca import examples
   >>> filename = osp.join(osp.split(examples.__file__)[0], 'goncourt.csv')
   >>> referenceset = parsefile(filename, delimiter='\t')

So, the beginning of our `referenceset` is:

.. sourcecode:: python

    >>> referenceset[:3]
    [[1903, u'John-Antoine Nau'],
    [1904, u'L\xe9on Frapi\xe9'],
    [1905, u'Claude Farr\xe8re']]


Now, let's build the `targetset` thanks to a *sparql query* and the dbpedia
end-point:

.. sourcecode:: python

   >>> from nazca.dataio import sparqlquery
   >>> query = """SELECT ?writer, ?name WHERE {
   ?writer  <http://purl.org/dc/terms/subject> <http://dbpedia.org/resource/Category:French_novelists>.
   ?writer rdfs:label ?name.
   FILTER(lang(?name) = 'fr')
   } """
   >>> targetset = sparqlquery('http://dbpedia.org/sparql', query, autocaste_data=False)

Both functions return nested lists as presented before.


Now, we have to define the distance function to be used for the alignment.
This is done thanks to a the `BaseProcessing` class::

.. sourcecode:: python

   >>> from nazca.distances import BaseProcessing, levenshtein
   >>> processing = BaseProcessing(ref_attr_index=1, target_attr_index=1, distance_callback=levenshtein)

or (equivalent way)::

.. sourcecode:: python

   >>> from nazca.distances import LevenshteinProcessing
   >>> processing = LevenshteinProcessing(ref_attr_index=1, target_attr_index=1)

Now, we create an aligner (using the `BaseAligner` class):

.. sourcecode:: python

   >>> from nazca.aligner import BaseAligner
   >>> aligner = BaseAligner(threshold=0, processings=(processing,))


To limit the number of comparisons we may add a blocking technic:

.. sourcecode:: python

   >>> from nazca.blocking import SortedNeighborhoodBlocking
   >>> aligner.register_blocking(SortedNeighborhoodBlocking(1, 1, window_width=4))



We have the aligned pairs using the `get_aligned_pairs` method of the `BaseAligner`:

.. sourcecode:: python

   >>> for (r, ri), (t, ti), d in aligner.get_aligned_pairs(referenceset, targetset):
   >>>    print 'Alignment of %s to %s (distance %s)' % (referenceset[ri], targetset[ti], d)



It may be important to apply some pre-processing on the data to align. For
instance, names can be written with lower or upper characters, with extra
characters as punctuation or unwanted information in parenthesis and so on. That
is why we provide some functions to ``normalize`` your data. The most useful may
be the :func:`simplify` function (see the docstring for more information).

.. sourcecode:: python


   >>> from nazca.normalize import SimplifyNormalizer
   >>> aligner.register_ref_normalizer(SimplifyNormalizer(attr_index=1))



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

   >>> from nazca.dataio import sparqlquery, rqlquery
   >>> referenceset = sparqlquery('http://dbpedia.inria.fr/sparql',
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
   >>> targetset = rqlquery('http://demo.cubicweb.org/geonames',
		'Any U, N, LONG, LAT WHERE X is Location, X name'
		' N, X country C, C name "France", X longitude'
		' LONG, X latitude LAT, X population > 1000, X'
		' feature_class "P", X cwuri U',
		indexes=[0, 1, (2, 3)])

   >>> from nazca.distances import BaseProcessing, levenshtein
   >>> processing = BaseProcessing(ref_attr_index=1, target_attr_index=1, distance_callback=levenshtein)

   >>> from nazca.aligner import BaseAligner
   >>> aligner = BaseAligner(threshold=0, processings=(processing,))

   >>> from nazca.blocking import KdTreeBlocking
   >>> aligner.register_blocking(KdTreeBlocking(2, 2))

   >>> results = list(aligner.get_aligned_pairs(referenceset, targetset, unique=True))



Let's explain the code. We have two files, containing a list of cities we want
to align, the first column is the identifier, and the second is the name of the
city and the last one is the location of the city (longitude and latitude), gathered
into a single tuple.

In this example, we want to build a *kdtree* on the couple (latitude, longitude)
to divide our data into a few candidates. This clustering is coarse, and is only
used to reduce the potential candidates without loosing any more refined
possible matches.

So, in the next step, we define the processings to apply, and we add a specific
 kdtree_ blocking.

Finally, `uniqe` ask to the function to return the best
candidate (i.e.: the one having the shortest distance below the given threshold)

The function output a generator yielding tuples where the first element is the
identifier of the `referenceset` item and the second is the `targetset` one (It
may take some time before yielding the first tuples, because all the computation
must be done…)

.. _kdtree: http://en.wikipedia.org/wiki/K-d_tree


`Try <http://demo.cubicweb.org/nazca/view?vid=nazca>`_ it online !
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

We have also made a little application of Nazca, using `CubicWeb
<http://www.cubicweb.org/>`_. This application provides a user interface for
Nazca, helping you to choose what you want to align. You can use sparql or rql
queries, as in the previous example, or import your own cvs file [#]_. Once you
have choosen what you want to align, you can click the *Next step* button to
customize the processings you want to apply, just as you did before in python !
Once done, by clicking the *Next step*, you start the alignment process. Wait a
little bit, and you can either download the results in a *csv* or *rdf* file, or
directly see the results online choosing the *html* output.

.. [#] Your csv file must be tab-separated for the moment…
