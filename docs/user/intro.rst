
Introduction
============

Bigger was designed to investigate big mapping classes of infinite type surfaces.

Framework
---------

The underlying framework of bigger is similar to that of `curver <https://pypy.org/project/curver/>`_ and `flipper <https://pypi.org/project/flipper/>`_.
This means that bigger can do many of the things that curver and flipper can, however, bigger has several advantages including:

    - The ability to handle infinite type surfaces
    - Handle mapping classes and laminations with infinite support

It achieves this by through having laminations (and their underlying triangulations) that are lazily evaluated.
Of course this comes at variety of costs including:

    - Not being able to solve the word and conjugacy problems
    - Not being able to determine veering triangulations or mapping tori
    - Efficiency

If you are looking for a basic framework for manipulating curves, arcs and mapping classes and are not interested in infinite surfaces then you should probably base your code on curver.

Bigger License
--------------

    .. include:: ../../LICENSE
