""" A module for representing laminations on Triangulations. """

from itertools import islice
from typing import Any, Iterable, Tuple, TypeVar, Generic, Callable

import bigger  # pylint: disable=unused-import
from bigger.decorators import memoize

Edge = TypeVar("Edge")


class Lamination(Generic[Edge]):
    """ A measured lamination on a :class:`~bigger.triangulation.Triangulation`.

    The lamination is defined via a function mapping the edges of its underlying Triangulation to their corresponding measure. """

    def __init__(self, triangulation: "bigger.Triangulation[Edge]", weight: Callable[[Edge], int], support: Iterable[Edge]) -> None:
        self.triangulation = triangulation
        self.weight = weight
        self.support = support

    @memoize
    def __call__(self, edge: Edge) -> int:
        return self.weight(edge)

    def show(self, edges: Iterable[Edge]) -> str:
        """ Return a string describing this Lamination on the given edges. """
        return ", ".join("{}: {}".format(edge, self(edge)) for edge in edges)

    def is_finitely_supported(self) -> bool:
        """ Return whether this lamination is supported on finitely many edges of the underlying Triangulation. """
        return isinstance(self.support, set)

    def __eq__(self, other: Any) -> bool:
        if not self.is_finitely_supported():
            raise ValueError("Can only determine equality between finitely supported laminations")

        if isinstance(other, Lamination):
            if not other.is_finitely_supported():
                raise ValueError("Can only determine equality between finitely supported laminations")

            return self.support == other.support and all(self(edge) == other(edge) for edge in self.support)
        elif isinstance(other, dict):
            return self.support == set(other) and all(self(edge) == other[edge] for edge in self.support)

        return NotImplemented

    def __str__(self) -> str:
        if not self.is_finitely_supported():
            return "Infinitely supported lamination {} ...".format(self.show(islice(self.support, 10)))

        return self.show(self.support)

    def __repr__(self) -> str:
        return str(self)

    def complexity(self) -> int:
        """ Return the number of intersections between this Lamination and its underlying Triangulation. """
        return sum(max(self(edge), 0) for edge in self.support)

    def is_short(self) -> bool:
        """ Return whether this Lamination intersects its underlying Triangulation exactly twice.

        Note that when :meth:`shorten` is upgraded this will need to change to the curver definition of is_short. """
        return self.complexity() == 2  # or all(self(edge) == 2 for edge in self.support)

    def shorten(self) -> Tuple["bigger.Lamination[Edge]", "bigger.Encoding[Edge]"]:
        """ Return an :class:`~bigger.encoding.Encoding` that minimises self.complexity.

        Note that in the future this should do curvers full Lamination shortening algorithm. """

        lamination = self
        complexity = lamination.complexity()
        conjugator = lamination.triangulation.encode_identity()
        time_since_last_progress = 0
        while not lamination.is_short():
            time_since_last_progress += 1
            best_complexity, best_h = complexity, lamination.triangulation.encode_identity()
            for edge in lamination.support:
                h = lamination.triangulation.encode_flip({edge})
                new_complexity = h(lamination).complexity()
                if new_complexity <= best_complexity:
                    best_complexity, best_h = new_complexity, h

            if best_complexity < complexity:
                time_since_last_progress = 0
            conjugator = best_h * conjugator
            lamination = best_h(lamination)
            complexity = best_complexity

            if time_since_last_progress > 3:
                raise ValueError("{} is not a non-isolating curve".format(lamination))

        return lamination, conjugator

    def encode_twist(self) -> "bigger.Encoding[Edge]":
        """ Return an :class:`~bigger.encoding.Encoding` that performs a Dehn twist about this Lamination.

        Note that this currently only works on non-isolating curves. """
        short, conjugator = self.shorten()

        # Use the following for reference:
        # #<--------#     #<--------#
        # |    a   ^^     |\   a    ^
        # |------/--|     |  \      |
        # |b  e/   d| --> |b   \e' d|
        # |  /      |     |      \  |
        # v/   c    |     v    c   V|
        # #-------->#     #-------->#

        # #<--------#     #<--------#
        # |    a|  ^^     |\   a    ^
        # |     |/  |     |  \      |
        # |b  e/|  d| --> |b   \e' d|
        # |  /  |   |     |      \  |
        # v/   c|   |     v    c   V|
        # #-------->#     #-------->#

        assert isinstance(short.support, set)
        assert len(short.support) == 2

        e, _ = short.support
        a, b, c, d = short.triangulation.link(e)
        if short(b) == 1:
            assert b == d
            twist = short.triangulation.encode([{e: b, b: e}, {e}])
        else:  # short(a) == 1:
            assert a == c
            twist = short.triangulation.encode([{e: a, a: e}, {e}])

        return ~conjugator * twist * conjugator
