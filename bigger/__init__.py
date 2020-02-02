
from typing import TYPE_CHECKING

from . import load  # noqa: F401
from .encoding import Encoding  # noqa: F401
from .lamination import FinitelySupportedLamination, Lamination  # noqa: F401
from .moves import Move, EdgeFlip, Isometry  # noqa: F401
from .triangulation import OrientedEdge, Edge, Triangulation, oedger, edger  # noqa: F401
from .mappingclassgroup import MappingClassGroup  # noqa: F401
from .utilities import half  # noqa: F401

# Aliases.
MCG = MappingClassGroup

if TYPE_CHECKING:
    from .types import *  # noqa: F401, F403

