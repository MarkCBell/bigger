""" Bigger is a program for studying mapping classes and laminations on infinite type surfaces. """

import sys
import importlib.metadata

from . import load  # noqa: F401
from .encoding import Move, Encoding  # noqa: F401
from .lamination import Lamination  # noqa: F401
from .triangulation import Side, Triangulation  # noqa: F401
from .mappingclassgroup import MappingClassGroup  # noqa: F401
from .structures import UnionFind  # noqa: F401
from .utilities import half  # noqa: F401
from .draw import draw, DrawStructure  # noqa: F401

# Aliases.
MCG = MappingClassGroup

__version__ = importlib.metadata.version("bigger")
sys.setrecursionlimit(10000)  # We may need a large call stack.
