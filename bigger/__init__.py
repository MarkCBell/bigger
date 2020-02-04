
import sys
from typing import TYPE_CHECKING

import pkg_resources

from . import load  # noqa: F401
from .encoding import Move, Encoding  # noqa: F401
from .lamination import FinitelySupportedLamination, Lamination  # noqa: F401
from .triangulation import Triangulation  # noqa: F401
from .mappingclassgroup import MappingClassGroup  # noqa: F401
from .utilities import half  # noqa: F401

# Aliases.
MCG = MappingClassGroup

if TYPE_CHECKING:
    from .types import *  # noqa: F401, F403

__version__ = pkg_resources.get_distribution('bigger').version
sys.setrecursionlimit(10000)  # We may need a large stack.
