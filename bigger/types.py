""" A module describing common custom types used within bigger. """

from typing import TypeVar, Tuple  # noqa: F401
from typing_extensions import Protocol

Edge = TypeVar("Edge")
Triangle = Tuple[Edge, Edge, Edge]
Coord = Tuple[float, float]
FlatTriangle = Tuple[Coord, Coord, Coord]


class SupportsLayout(Protocol):  # pylint: disable=too-few-public-methods
    """ A class that has a layout method for converting Triangles to FlatTriangles. """

    def layout(self, triangle: Triangle) -> FlatTriangle:
        """ Return a FlatTriangle representation of this Triangle. """

        ...
