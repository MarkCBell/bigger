
Bigger
======

Bigger is a program for computing big mapping classes and their actions on laminations via ideal triangulation coordinates.

Bigger officially supports Python 3.5 -- 3.8 and PyPy3.

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
    >>> a == a
    True
    >>> b = S('shift.shift')(a)  # Shift everything down twice
    >>> a == b
    False
    >>> b
    Lamination (2, 5): -1
    >>> S('SHIFT.shift')(a) == a  # Shift and then shift back
    True
    >>> S('shift.b.b.b.b')(a)  # Twist then shift
    Lamination (1, 6): 2, (1, 5): 3

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

