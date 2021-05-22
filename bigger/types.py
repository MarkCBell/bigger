""" A module describing common custom types used within bigger. """

from typing import Tuple, TypeVar

Edge = TypeVar("Edge")

Coord = Tuple[float, float]
FlatTriangle = Tuple[Coord, Coord, Coord]
