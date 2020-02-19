
Bigger
======

Bigger is a program for computing big mapping classes and their actions on laminations via ideal triangulation coordinates.

Bigger officially supports Python 3.5 -- 3.8.

Quickstart
----------

Bigger is available on `PyPI`_, so it can be installed via::

    $ pip install bigger --user --upgrade

Once installed, try it inside of Python::

    >>> import bigger
    >>> S = bigger.load.biflute()  # The two-ended infinitely punctured sphere.
    >>> a = S.triangulation({1: -1})  # An arc.
    >>> a
    1: -1
    >>> a == a
    True
    >>> b = S('shift.shift')(a)  # Shift everthing down twice.
    >>> a == b
    False
    >>> b
    7: -1
    >>> S('SHIFT.shift')(a) == a  # Shift and then shift back.
    True
    >>> m = S.triangulation({0: -1, 1: -1, 2: -1})  # A multiarc.
    >>> m
    0: -1, 1: -1, 2: -1
    >>> S('shift.a0.a0')(m)  # Twist then shift.
    3: -1, 4: 1, 5: 3

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

