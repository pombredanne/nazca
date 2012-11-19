Alignment project
==================

What is it for ?
----------------

This python library aims to help you to *align data*. For instance, you have a
list of cities, described by their name and their country and you would like to
find their URI on dbpedia to have more information about, as the longitude and
the latitude for example. If you have two or three cities, you can do it with
your bare hands, but you could not if you have hundreds or thousands cities.
This library provides you all the stuff we need to do it.


Introduction
------------

The alignment process is divided into three main steps:

1. Gather and format the data we want to align.
   In this step, we define two sets that we call the ``alignset`` and the
   ``targetset``. The ``alignset`` is the set containing our data (in this case, the
   Goncourt prize winners), and the ``targetset`` contains the data on which we would
   like to make the links (dbpedia in this case)
2. Compute the similarity between the items gathered
   We compute a distance matrix between the two sets according a given distance.
3. Find the items having a high similarity thank to the distance matrix


Simple case
^^^^^^^^^^^

Let's defining our ``alignset`` and our ``targetset`` as simple python
lists.

.. code-block:: python

    alignset = ['Victor Hugo', 'Albert Camus']
    targetset = ['Albert Camus', 'Guillaume Apollinaire', 'Victor Hugo']

Now, we have to compute the similarity between each items. For that purpose, the
`Levehshtein's distance <http://en.wikipedia.org/wiki/Levenshtein_distance>`_
[#]_, which is well accurate to compute the distance between few words, is used.

.. [#] Also called the *edit distance*, because the distance between two words
       is equal to the number of single-character edits required to change one 
       word into the other.

Such a function is provided in ``alignment.distance`` module. The next step
is to compute the distance matrix according to the Levenshtein distance. The
result is given in the following tables.


+--------------+--------------+-----------------------+-------------+
|              | Albert Camus | Guillaume Apollinaire | Victor Hugo |
+==============+==============+=======================+=============+
| Victor Hugo  | 6            | 9                     | 0           |
+--------------+--------------+-----------------------+-------------+
| Albert Camus | 0            | 8                     | 6           |
+--------------+--------------+-----------------------+-------------+

The alignment process is ended by reading the matrix and saying items having a
value inferior to a given threshold are identical.

A more complex one
^^^^^^^^^^^^^^^^^^

The previous case was simple, because we had only one *thing* to align (the
name), but it is frequent to have a lot of *thing* to align, such as the name
and the birth date and the birth city. The steps remains the same, except that
three distance matrices will be computed, and *items* will be represented as
nested lists. See the following example:

.. code-block:: python

    alignset = [['Paul Dupont', '14-08-1991', 'Paris'],
                ['Jacques Dupuis', '06-01-1999', 'Bressuire'],
                ['Michel Edouard', '18-04-1881', 'Nantes']]
    targets = [['Dupond Paul', '14/08/1991', 'Paris'],
                ['Edouard Michel', '18/04/1881', 'Nantes'],
                ['Dupuis Jacques ', '06/01/1999', 'Bressuire'],
                ['Dupont Paul', '01-12-2012', 'Paris']]


In such a case, two distance functions are used, the Levenshtein one for the
name and the city and a temporal one [#]_.

.. [#] Provided in the ``alignment.distance`` module.


We obtain the three following matrices

For the name
    +----------------+-------------+----------------+----------------+-------------+
    |                | Dupond Paul | Edouard Michel | Dupuis Jacques | Dupont Paul |
    +================+=============+================+================+=============+
    | Paul Dupont    | 1           | 6              | 5              | 0           |
    +----------------+-------------+----------------+----------------+-------------+
    | Jacques Dupuis | 5           | 6              | 0              | 5           |
    +----------------+-------------+----------------+----------------+-------------+
    | Edouard Michel | 6           | 0              | 6              | 6           |
    +----------------+-------------+----------------+----------------+-------------+
For the birth date
    +------------+------------+------------+------------+------------+
    |            | 14/08/1991 | 18/04/1881 | 06/01/1999 | 01-12-2012 |
    +============+============+============+============+============+
    | 14-08-1991 | 0          | 40294      | 2702       | 7780       |
    +------------+------------+------------+------------+------------+
    | 06-01-1999 | 2702       | 42996      | 0          | 5078       |
    +------------+------------+------------+------------+------------+
    | 18-04-1881 | 40294      | 0          | 42996      | 48074      |
    +------------+------------+------------+------------+------------+
For the city
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
item 0 in our ``alignset`` is the same that the item 0 in the ``targetset``, the
1 in the ``alignset`` and the 2 of the ``targetset`` too.
It's important to notice that even if the item 0 of the ``alignset`` and the 3
of the ``targetset`` have the same name and the same birthplace they are not
likely identical because of their very different birth date.


You may have noticed that working with matrice as I did for the example is a
little bit boring. The good news is this project makes all this job for you. You
just have to give the sets and distance functions and that's all. An other good
news is the project comes with the needed functions to build the sets !


Real applications
-----------------

The Goncourt prize
^^^^^^^^^^^^^^^^^^

On wikipedia, we can find the `Goncourt prize winners
<https://fr.wikipedia.org/wiki/Prix_Goncourt#Liste_des_laur.C3.A9ats>`_, and we
would like to establish a link between the winners and their URI on dbpedia
[#]_.

.. [#] Let's imagine the *Goncourt prize winners* category does not exist in
       dbpedia

We simply copy/paste the winners list of wikipedia into a file and replace all
the separators (``-`` and ``,``) by ``#``. So, the beginning of our file is :

..

    | 1903#John-Antoine Nau#Force ennemie (Plume)
    | 1904#Léon Frapié#La Maternelle (Albin Michel)
    | 1905#Claude Farrère#Les Civilisés (Paul Ollendorff)
    | 1906#Jérôme et Jean Tharaud#Dingley, l'illustre écrivain (Cahiers de la Quinzaine)

When using the high-level functions of this library, each item must have at
least two elements : an *identifier* (the name, or the URI) and the *thing* to
compare. With the previous file, we will use the name (so the column number 1)
as *identifier* and *thing* to align. This is told to python thanks to the
following code:

.. code-block:: python

    from alignment import dataio as aldio #Functions for input and output data
    from alignment import distance as ald #Functions to compute the distances
    from alignment import aligner as ala  #Functions to align data
    from alignment import normalize as aln#Functions to normalize data

    alignset = adio.parsefile('prixgoncourt', indexes=[1, 1], delimiter='#')

Now, let's building the ``targetset`` thanks to a *sparql query* and the dbpedia
end-point:

.. code-block:: python

   query = """
        SELECT ?writer, ?name WHERE {
          ?writer  <http://purl.org/dc/terms/subject> <http://dbpedia.org/resource/Category:French_novelists>.
          ?writer rdfs:label ?name.
          FILTER(lang(?name) = 'fr')
       }
    """
    targetset = adio.sparqlquery('http://dbpedia.org/sparql', query)

Both functions return nested lists as presented before. Now, we have to define
the distance function to be used for the alignment. This is done thanks to a
python dictionary where the keys are the columns to work on, and the values are
the treatments to apply.

.. code-block:: python

    treatments = {1: {'metric': ald.levenshtein}}

Finally, the last thing we have to do, is to call the ``align`` function:

.. code-block:: python

    global_matrix, hasmathed = ala.align(alignset,
                                        targset,
                                        0.4,   #This is the matching threshold
                                        treatments,
                                        'goncourtprize_alignment')

The alignment results will be written into the `goncourtprize_alignment` file.
The `align` function returns the global alignment matrix and a boolean set to
``True`` if at least one matching has been done, ``False`` otherwise.

It may be important to apply some pre-treatment on the data to align. For
instance, names can be written with extra characters as punctuation or
unwanted information in parenthesis and so on. That is why we provide some
functions to `normalize` your data. The most useful may be the `simplify()` one
(see the docstring for more information). So the treatments list can be given as
follow:


.. code-block:: python

    def remove_after(string, sub):
        """ Remove the text after ``sub`` in ``string``
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
^^^^^^^^^^^^^^^^

The previous case with the `Goncourt prize winners` was pretty simply because
the number of items was small, and the computation fast. But in a more real use
case, the number of items to align may be huge (some thousands or millions…). Is
such a case it's unthinkable to build the global alignment matrix because it
would be to big and it would take fews days to achieve the computation. So the
idea is to make small groups of possible similar data. For this purpose, we
provide some functions to group data. We have functions to group text and
numerical data.


This is done by the following python code:

.. code-block:: python

    targetset = aldio.parsefile('FR.txt', indexes=[0, 1, (4, 5)])
    alignset = aldio.parsefile('frenchbnf', indexes=[0, 2, (14, 12)])


    treatments = {1: {'normalization': [aln.simply],
                      'metric': ald.levenshtein
                      'matrix_normalized': False
                     }
                 }
    results = ala.alignall(alignset, targetset, 3, treatments=treatments, #As before
                           indexes=(2, 2), #On which data build the kdtree
                           mode='kdtree',  #The mode to use
                           uniq=True) #Return only the best results


Let's explain the code. We have two files, containing a list of cities we want
to align, the first column is the identifier, and the second is the name of the city
and the last one is location of the city (longitude and latitude), gathered into
a single tuple.

Next, we define the treatments to apply. It is the same as before, but we ask
for a non-normalized matrix (ie: the real output of the levenshtein distance).
Finally, we call the ``alignall`` function. ``indexes`` is a tuple saying the
position of the point on which build the kdtree, ``mode`` is the mode used to
find neighbours [#]_, ``uniq`` ask to the function to return the best candidate
(ie: the one having the shortest distance above the given threshold)

.. [#] The available modes are ``kdtree``, ``kmeans`` and ``minibatch`` for
       numerical data and ``minhashing`` for text one.
