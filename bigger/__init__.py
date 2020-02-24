""" Bigger is a program for studying mapping classes and laminations on infinite type surfaces. """

import sys

import pkg_resources

from . import load  # noqa: F401
from .encoding import Move, Encoding  # noqa: F401
from .lamination import Lamination  # noqa: F401
from .triangulation import Triangulation  # noqa: F401
from .mappingclassgroup import MappingClassGroup  # noqa: F401
from .utilities import half  # noqa: F401

# Aliases.
MCG = MappingClassGroup

__version__ = pkg_resources.get_distribution("bigger").version
sys.setrecursionlimit(10000)  # We may need a large stack.
