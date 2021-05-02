""" A module for representing laminations on Triangulations. """

from __future__ import annotations

from collections import defaultdict
from itertools import chain, islice
from typing import Any, Callable, Dict, Generic, Iterable, Union
from PIL import Image  # type: ignore

import bigger
from bigger.types import Edge
from bigger.decorators import memoize


class Lamination(Generic[Edge]):
    """A measured lamination on a :class:`~bigger.triangulation.Triangulation`.

    The lamination is defined via a function mapping the edges of its underlying Triangulation to their corresponding measure."""

    def __init__(self, triangulation: bigger.Triangulation[Edge], weight: Callable[[Edge], int], support: Callable[[], Iterable[Edge]]) -> None:
        self.triangulation = triangulation
        self.weight = weight
        self.support = support

    def supporting_sides(self) -> Iterable[bigger.Side[Edge]]:
        """Return the sides supporting this lamination."""
        for edge in self.support():
            for b in [True, False]:
                yield bigger.Side(edge, b)

    @memoize
    def __call__(self, edge: Union[Edge, bigger.Side[Edge]]) -> int:
        if isinstance(edge, bigger.Side):
            return self(edge.edge)

        return self.weight(edge)

    def __hash__(self) -> int:
        if self.is_finitely_supported():
            return hash(frozenset((edge, self(edge)) for edge in self.support()))

        return NotImplemented

    def __bool__(self) -> bool:
        if not self.is_finitely_supported():
            raise ValueError("Cannot determine truthiness of non-finitely supported laminations")

        return not any(self(edge) for edge in self.support())

    @memoize
    def dual(self, side: bigger.Side[Edge]) -> int:
        """Return the weight of this lamination dual to the given side."""

        corner = self.triangulation.corner(side)
        a, b, c = self(corner[0].edge), self(corner[1].edge), self(corner[2].edge)
        af, bf, cf = max(a, 0), max(b, 0), max(c, 0)  # Correct for negatives.
        correction = min(af + bf - cf, bf + cf - af, cf + af - bf, 0)
        return bigger.utilities.half(bf + cf - af + correction)

    def left(self, side: bigger.Side[Edge]) -> int:
        """Return the dual weight to the left of this side."""

        return self.dual(self.triangulation.right(side))

    def right(self, side: bigger.Side[Edge]) -> int:
        """Return the dual weight to the right of this side."""

        return self.dual(self.triangulation.left(side))

    def describe(self, edges: Iterable[Edge]) -> str:
        """Return a string describing this Lamination on the given edges."""
        return ", ".join("{}: {}".format(edge, self(edge)) for edge in edges)

    def is_finitely_supported(self) -> bool:
        """Return whether this lamination is supported on finitely many edges of the underlying Triangulation."""
        return isinstance(self.support(), set)

    def __eq__(self, other: Any) -> bool:
        if not self.is_finitely_supported():
            raise ValueError("Can only determine equality between finitely supported laminations")

        if isinstance(other, Lamination):
            if not other.is_finitely_supported():
                raise ValueError("Can only determine equality between finitely supported laminations")

            return self.support() == other.support() and all(self(edge) == other(edge) for edge in self.support())
        elif isinstance(other, dict):
            return self.support() == set(other) and all(self(edge) == other[edge] for edge in self.support())

        return NotImplemented

    def __str__(self) -> str:
        if not self.is_finitely_supported():
            return "Infinitely supported lamination {} ...".format(self.describe(islice(self.support(), 10)))

        return "Lamination {}".format(self.describe(self.support()))

    def __repr__(self) -> str:
        return str(self)

    def __add__(self, other: Lamination[Edge]) -> Lamination[Edge]:
        """Return the Haken sum of this lamination and another."""

        def weight(edge: Edge) -> int:
            return self(edge) + other(edge)

        return self.triangulation(weight, lambda: chain(self.support(), other.support()), self.is_finitely_supported() and other.is_finitely_supported())

    def __sub__(self, other: Lamination[Edge]) -> Lamination[Edge]:
        def weight(edge: Edge) -> int:
            return self(edge) - other(edge)

        return self.triangulation(weight, lambda: chain(self.support(), other.support()), self.is_finitely_supported() and other.is_finitely_supported())

    def __mul__(self, other: int) -> Lamination[Edge]:
        """Return this lamination scaled by other."""

        def weight(edge: Edge) -> int:
            return other * self(edge)

        return self.triangulation(weight, self.support)

    def __rmul__(self, other: int) -> Lamination[Edge]:
        """Return this lamination scaled by other."""

        return self * other

    def complexity(self) -> int:
        """Return the number of intersections between this Lamination and its underlying Triangulation."""

        assert self.is_finitely_supported()

        return sum(max(self(edge), 0) for edge in self.support())

    def trace(self, side: bigger.Side[Edge], intersection: int) -> Iterable[tuple[bigger.Side[Edge], int]]:
        """Yield the intersections of the triangulation run over by this lamination from a starting point.

        The starting point is specified by a `Side` and how many intersections into that side."""

        start = (side, intersection)

        assert 0 <= intersection < self(side)  # Sanity.
        while True:
            yield side, intersection
            corner = self.triangulation.corner(~side)
            x, y, z = corner
            if intersection < self.dual(z):  # Turn right.
                side, intersection = y, intersection  # pylint: disable=self-assigning-variable
            elif self.dual(x) < 0 and self.dual(z) <= intersection < self.dual(z) - self.dual(x):  # Terminate.
                break
            else:  # Turn left.
                side, intersection = z, self(z) - self(x) + intersection

            if (side, intersection) == start:
                break

    def meeting_components(self, edge: Edge) -> Iterable[Lamination[Edge]]:
        """Yield the components of self which meet the given edge.

        Note: self does not need to be finitely supported but each component meeting edge must be.
        Unfortunately we have no way of knowing this in advance."""

        num_intersections = self(edge)
        start_side = bigger.Side(edge)
        intersections = set(range(num_intersections))
        while intersections:
            hits: Dict[Edge, int] = defaultdict(int)
            start_intersection = next(iter(intersections))  # pylint: disable=stop-iteration-return
            for side, intersection in self.trace(start_side, start_intersection):
                hits[side.edge] += 1
                if side == start_side:
                    intersections.remove(intersection)
                elif side == ~start_side:
                    intersections.remove(num_intersections - 1 - intersection)

            yield self.triangulation(hits)

    def meeting(self, edge: Edge) -> Lamination[Edge]:
        """Return the sublamination of self meeting the given edge."""

        hits: Dict[Edge, int] = defaultdict(int)
        for component in self.meeting_components(edge):
            for edgy in component.support():
                hits[edgy] += component(edgy)

        return self.triangulation(hits)

    def parallel_components(self) -> dict[Lamination[Edge], tuple[int, bigger.Side[Edge]]]:
        """Return a dictionary mapping component to (multiplicity, edge) for each component of self that is parallel to an edge."""

        assert self.is_finitely_supported()

        components = dict()
        sides = set(side for edge in self.support() for side in self.triangulation.link(bigger.Side(edge)))
        for side in sides:
            if self(side):
                continue

            if side.orientation:  # Don't double count.
                multiplicity = -self(side)
                if multiplicity > 0:
                    components[self.triangulation.side_arc(side)] = (multiplicity, side)

            walk = list(self.triangulation.walk_vertex(side))

            if walk[-1] == ~side:
                v_edges = walk[:-1]
                if len(v_edges) > 2:
                    around_v = bigger.utilities.maximin([0], (self.left(sidey) for sidey in v_edges))
                    twisting = bigger.utilities.maximin([0], (self.left(sidey) - around_v for sidey in v_edges[1:-1]))

                    if self.left(v_edges[0]) == self.left(v_edges[-1]) == around_v:
                        multiplicity = twisting

                        if multiplicity > 0:
                            components[self.triangulation.side_curve(side)] = (multiplicity, side)

        return components

    def is_short(self) -> bool:
        """Return whether this Lamination is short."""

        # Note that when :meth:`shorten` is upgraded this will need to change to the curver definition of is_short.
        return self.complexity() == 2  # or all(self(edge) == 2 for edge in self.support())

    def shorten(self) -> tuple[bigger.Lamination[Edge], bigger.Encoding[Edge]]:
        """Return an :class:`~bigger.encoding.Encoding` that minimises self.complexity.

        Note that in the future this should do curvers full Lamination shortening algorithm."""

        assert self.is_finitely_supported()

        lamination = self
        complexity = lamination.complexity()
        conjugator = lamination.triangulation.identity()
        time_since_last_progress = 0
        while not lamination.is_short():
            time_since_last_progress += 1
            best_complexity, best_h = complexity, lamination.triangulation.identity()
            for edge in lamination.support():  # Uses finite support assumption.
                h = lamination.triangulation.flip({bigger.Side(edge)})
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

    def twist(self, power: int = 1) -> bigger.Encoding[Edge]:
        """Return an :class:`~bigger.encoding.Encoding` that performs a Dehn twist about this Lamination.

        Assumes but does not check that this lamination is a multicurve."""

        if self.is_finitely_supported():
            short, conjugator = self.shorten()

            twist = short.triangulation.identity()
            for multiplicity, a in short.parallel_components().values():
                num_flips = short.complexity() - short.dual(a)
                for _ in range(num_flips):
                    twist = twist.target.flip({twist.target.left(a)}) * twist

                isom = dict()
                x = y = a
                while x != ~a:
                    isom[y] = x
                    x = ~twist.source.left(x)
                    y = ~twist.target.left(y)

                twist = twist.target.relabel_from_dict(isom) * twist
                twist = twist ** multiplicity

            return ~conjugator * twist ** power * conjugator

        def action(lamination: bigger.Lamination[Edge]) -> bigger.Lamination[Edge]:
            def weight(edge: Edge) -> int:
                # We used to do:
                #  X = lamination
                #  for curve in self.meeting_components(edge):
                #      X = curve.twist(power=power)(X)
                #  return X
                # But by now using twisted_by we can get additional performance through memoization.
                return lamination.twisted_by(frozenset(self.meeting_components(edge)), power=power)(edge)

            def support() -> Iterable[Edge]:
                for edge in lamination.support():
                    if weight(edge):
                        yield edge

                    for edgy in self.meeting(edge).support():
                        if weight(edgy):
                            yield edgy

            return self.triangulation(weight, support, lamination.is_finitely_supported())

        def inv_action(lamination: bigger.Lamination[Edge]) -> bigger.Lamination[Edge]:
            def weight(edge: Edge) -> int:
                return lamination.twisted_by(frozenset(self.meeting_components(edge)), power=-power)(edge)

            def support() -> Iterable[Edge]:
                for edge in lamination.support():
                    if weight(edge):
                        yield edge

                    for edgy in self.meeting(edge).support():
                        if weight(edgy):
                            yield edgy

            return self.triangulation(weight, support, lamination.is_finitely_supported())

        return bigger.Move(self.triangulation, self.triangulation, action, inv_action).encode()

    @memoize
    def twisted_by(self, curves: set[Lamination[Edge]], power: int = 1) -> Lamination[Edge]:
        """Return curves.twist()(self).

        This is used purely for performance by allowing for memoizeation in self.twist."""

        X = self  # Linters get confused if we use the non-local variable.
        for curve in curves:
            X = curve.twist(power=power)(X)
        return X

    def draw(self, edges: list[Edge], **options: Any) -> Image:
        """Return a PIL image of this Lamination around the given edges."""

        return bigger.draw(self, edges=edges, **options)
