
Walkthrough
===========

Eager to get started? This page gives a good introduction in how to get started with bigger.

First, make sure that:

    - bigger is installed
    - bigger is up-to-date

Let's get started with some simple examples.

Getting a mapping class group
-----------------------------

Begin by importing bigger::

    >>> import bigger

Now, let's use the :meth:`~bigger.load.flute` method to load a big mapping class group::

    >>> S = bigger.load.flute()

This builds the :class:`mapping class group <bigger.mappingclassgroup.MappingClassGroup>` of the two-ended, infinitely-punctured surface of genus zero.
This group has been built with Lickorish generating set, consisting of 3 Dehn twists and 2 half-twists.

We can build a :class:`mapping class <bigger.encoding.Encoding>` using these generators::

    >>> h = S('a0.a0')

Laminations
--------------------

We can make a :class:`~bigger.lamination.Lamination` by using :meth:`S.lamination() <bigger.mappingclassgroupMappingClassGroup.lamination>`.
For example::

    >>> a = S.lamination(lambda e: -1 if e == 1 else 0)
    >>> a(0)
    0
    >>> a(1)
    1

The lamination is specified by a function that returns the number of times that it intersects each edge of the underlying triangulation.
As usual, if a lamination has :math:`k` components that are parallel to an edge then their intersection is :math:`-k`.
We can also create a lamination from a dictionary taking edges to their weights::

    >>> c = S.lamination({1: -1})
    >>> print(c)
    1: -1

These are actually created as :class:`~bigger.lamination.FinitelySupportedLamination`::

    >>> type(c)
    <class 'bigger.lamination.FinitelySupportedLamination'>

We can compute the image of a lamination under a mapping class::

    >>> print(h(c))
    1: 1, 2: 2
    >>> S('a1')(c) == c
    True

Visualisations
--------------

It's often hard to visualise or keep track of what is going on on these surfaces.
Eventually bigger will be able to show such laminations::

    >>> bigger.show(c, {1, 2, 3, 4})  # Start the GUI (see the installation warning).

Operations on mapping classes
-----------------------------

Bigger also allows us to compose together or take powers of existing mapping classes::

    >>> g = h * S('b1')
    >>> print(g(c))
    ???
    >>> (g**2)(c)
    ???

Building new mapping classes
----------------------------

Since  it can manipulate curves, bigger can create the Dehn twist about a curve automatically::

    >>> twist = S.lamination({1: 1, 2: 1}).encode_twist()
    >>> twist(c)(0)
    0
    >>> twist(c)(1)
    1

