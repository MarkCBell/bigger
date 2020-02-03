
Installation
============

The first step to using any software package is getting it properly installed.

From PyPI
---------

Bigger is available on the `Python Package Index`_.
The preferred method for installing the latest stable release is to use `pip`_ (included in Python 2.7.9+ and Python 3.4+ by default)::

    $ pip install bigger

If you don't have Python installed, this `Python installation guide`_ can guide you through the process.
Consider using the ``--upgrade`` and ``--user`` flags to ensure that all required packages are upgraded and that bigger is installed into a sensible place.

Since bigger is under active development, you can install the latest development version via::

    $ pip install git+git://github.com/MarkCBell/bigger.git@dev

Again, consider using the ``--upgrade`` and ``--user`` flags.

From source
-----------

Bigger is free open source software and so it can be installed directly from its source code.

Obtaining the source
~~~~~~~~~~~~~~~~~~~~

The official git repository of bigger's source code is available on `GitHub <https://github.com/MarkCBell/bigger>`_.
You can either clone the public repository::

    $ git clone git://github.com/MarkCBell/bigger.git

Or, download the `tarball <https://github.com/MarkCBell/bigger/tarball/master>`_::

    $ curl -OL https://github.com/MarkCBell/bigger/tarball/master
    # optionally, zipball is also available (for Windows users).

Installing from source
~~~~~~~~~~~~~~~~~~~~~~

Once you have a copy of the source, you can embed it in your own Python package, or install it into your site-packages easily::

    $ cd bigger
    $ pip install . --user

.. _Python Package Index: https://pypi.org/project/bigger/
.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/

