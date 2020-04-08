
Bigger
======

Bigger is a program for computing big mapping classes and their actions on non-compact laminations via ideal triangulation coordinates.

Bigger officially supports Python 3.5 -- 3.8 and PyPy3.

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
    >>> S = bigger.load.ladder()  # The infinite-genus two-ended surface
    >>> a = S.triangulation({(0, 5): -1})  # An arc
    >>> a
    Lamination (0, 5): -1

    >>> b = S.triangulation(lambda e: 2 if e[1] in {2, 3, 4, 6} else 0)  # An infinite arc
    >>> b
    Infinitely supported lamination (0, 0): 0, (0, 1): 0, (0, 2): 2, (0, 3): 2, (0, 4): 2, (0, 5): 0, (0, 6): 2, (0, 7): 0, (0, 8): 0, (-1, 0): 0 ...

    >>> c = S('b{n >= 0}.a[2].a.a')(b)  # Apply some mapping classes
    >>> # Let's make the picture at the top
    >>> edges = [(i, j) for i in range(-1, 2) for j in range(2, 9)] + [(i, 0) for i in range(2)]
    >>> c.draw(edges, layout=S, w=800)

External Links
--------------

* `PyPI`_
* `ReadTheDocs`_
* `GitHub`_
* `Travis`_
* `AppVeyor`_
* `Azure`_

.. _AppVeyor: https://ci.appveyor.com/project/MarkCBell/bigger
.. _Azure: https://dev.azure.com/MarkCBell/bigger
.. _GitHub: https://github.com/MarkCBell/bigger
.. _PyPI: https://pypi.org/project/bigger
.. _ReadTheDocs: http://biggermcg.readthedocs.io
.. _Travis: https://travis-ci.com/MarkCBell/bigger

