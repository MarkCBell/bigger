
Bigger
======

.. image:: https://img.shields.io/pypi/v/bigger.svg
    :target: https://pypi.org/project/bigger/
    :alt: PyPI version

.. image:: https://img.shields.io/pypi/l/bigger.svg
    :target: https://pypi.org/project/bigger/
    :alt: PyPI license

.. image:: https://img.shields.io/github/workflow/status/MarkCBell/bigger/Build/master
    :target: https://github.com/MarkCBell/bigger/actions
    :alt: Github build status

..
    can also use: https://github.com/MarkCBell/bigger/workflows/Build/badge.svg?branch=master

Bigger is a program for computing big mapping classes and their actions on non-compact laminations via ideal triangulation coordinates.
It's like `flipper`_ and `curver`_, but can handle infinite-type surfaces by being lazy about the computations it performs.

Bigger officially supports Python 3.7 -- 3.9.

.. image:: images/ladder.png
   :scale: 75 %
   :alt: An arc on the ladder surface
   :align: center

Quickstart
----------

Bigger is available on `PyPI`_, so it can be installed via::

    $ pip install bigger --user --upgrade

Once installed, try it inside of Python::

    >>> import bigger
    >>> S = bigger.load.spotted_ladder()  # The infinite-genus two-ended surface

    # Let's make a finite curve
    >>> c = S.triangulation({(0, 5): 1, (0, 6): 1})
    >>> c
    Lamination (0, 5): 1, (0, 6): 1

    # Let's make an infinite lamination
    >>> a = S.triangulation(lambda e: 2 if e[1] in {2, 3, 4, 6} else 0)
    >>> a
    Infinitely supported lamination (0, 0): 0, (0, 1): 0, (0, 2): 2, (0, 3): 2, (0, 4): 2, (0, 5): 0, (0, 6): 2, (0, 7): 0, (0, 8): 0, (-1, 0): 0 ...

    # Let's make the picture at the top
    >>> b = S('b{n >= 0}.a[2].a.a')(a)  # Apply some mapping classes
    # The edges that we are interested in
    >>> edges = [(i, j) for i in range(-1, 2) for j in range(2, 9)] + [(i, 0) for i in range(2)]
    >>> b.draw(edges, layout=S, w=800)

External Links
--------------

* `PyPI`_
* `ReadTheDocs`_
* `GitHub`_
* `AppVeyor`_
* `Azure`_

.. _AppVeyor: https://ci.appveyor.com/project/MarkCBell/bigger
.. _Azure: https://dev.azure.com/MarkCBell/bigger
.. _GitHub: https://github.com/MarkCBell/bigger
.. _PyPI: https://pypi.org/project/bigger
.. _ReadTheDocs: http://biggermcg.readthedocs.io
.. _curver: https://curver.readtthedocs.io
.. _flipper: https://flipper.readtthedocs.io

