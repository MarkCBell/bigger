""" A module for representing laminations on Triangulations. """

from __future__ import annotations

from collections import defaultdict
from itertools import chain, islice
from typing import Any, Callable, Dict, Generic, Iterable, Union
from PIL import Image  # type: ignore

import bigger
from bigger.types import Edge
from bigger.decorators import memoize, finite


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
            for orientation in [True, False]:
                yield bigger.Side(edge, orientation)

    def supporting_triangles(self) -> set[bigger.triangulation.Triangle[Edge]]:
        """Return a set of triangles supporting this lamination, useful for debugging."""

        return set(self.triangulation.triangle(side) for side in self.supporting_sides())

    @memoize
    def __call__(self, edge: Union[Edge, bigger.Side[Edge]]) -> int:
        if isinstance(edge, bigger.Side):
            return self(edge.edge)

        return self.weight(edge)

    @finite
    def __hash__(self) -> int:
        return hash(frozenset((edge, self(edge)) for edge in self.support()))

    @finite
    def __bool__(self) -> bool:
        return any(self(edge) for edge in self.support())

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

    @finite
    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Lamination):
            if not other.is_finitely_supported():
                raise ValueError("Equality testing requires finitely supported laminations")

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
        def weight(edge: Edge) -> int:
            return other * self(edge)

        return self.triangulation(weight, self.support, self.is_finitely_supported())

    def __rmul__(self, other: int) -> Lamination[Edge]:
        return self * other

    @finite
    def complexity(self) -> int:
        """Return the number of intersections between this Lamination and its underlying Triangulation."""

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

    def meeting(self, edge: Edge) -> Lamination[Edge]:
        """Return the sublamination of self meeting the given edge.

        Note: self does not need to be finitely supported but the sublamination must be.
        Unfortunately we have no way of knowing this in advance."""

        num_intersections = self(edge)
        start_side = bigger.Side(edge)
        intersections = set(range(num_intersections))
        hits: Dict[Edge, int] = defaultdict(int)
        while intersections:
            start_intersection = next(iter(intersections))
            for side, intersection in self.trace(start_side, start_intersection):
                hits[side.edge] += 1
                if side == start_side:
                    intersections.remove(intersection)
                elif side == ~start_side:
                    intersections.remove(num_intersections - 1 - intersection)

        return self.triangulation(hits)

    @memoize
    @finite
    def peripheral_components(self) -> dict[Lamination[Edge], tuple[int, list[bigger.Side[Edge]]]]:
        """Return a dictionary mapping component to (multiplicity, vertex) for each component of self that is peripheral around a vertex."""

        components = dict()
        sides = self.supporting_sides()
        for side in sides:
            walk = list(self.triangulation.walk_vertex(side))
            if walk[0] != min(walk):
                continue

            multiplicity = bigger.utilities.maximin([0], (self.left(side) for side in walk))
            if multiplicity > 0:
                component = self.triangulation({side.edge: 1 for side in walk})
                components[component] = (multiplicity, walk)

        return components

    @finite
    def parallel_components(self) -> dict[Lamination[Edge], tuple[int, bigger.Side[Edge], bool]]:
        """Return a dictionary mapping component to (multiplicity, edge, is_arc) for each component of self that is parallel to an edge."""

        components = dict()
        sides = set(side for edge in self.support() for side in self.triangulation.star(bigger.Side(edge)))
        for side in sides:
            if self(side) > 0:
                continue

            if side.orientation:  # Don't double count.
                multiplicity = -self(side)
                if multiplicity > 0:
                    components[self.triangulation.side_arc(side)] = (multiplicity, side, True)

            walk = list(self.triangulation.walk_vertex(side))

            if walk[-1] == ~side:
                v_edges = walk[:-1]
                if len(v_edges) > 2:
                    around_v = bigger.utilities.maximin([0], (self.left(sidey) for sidey in v_edges))
                    twisting = bigger.utilities.maximin([0], (self.left(sidey) - around_v for sidey in v_edges[1:-1]))

                    if self.left(v_edges[0]) == self.left(v_edges[-1]) == around_v:
                        multiplicity = twisting

                        if multiplicity > 0:
                            components[self.triangulation.side_curve(side)] = (multiplicity, side, False)

        return components

    @finite
    def peripheral(self) -> Lamination[Edge]:
        """Return the lamination consisting of the peripheral components of this Lamination."""

        return self.triangulation.disjoint_sum(dict((component, multiplicity) for component, (multiplicity, _) in self.peripheral_components().items()))

    @finite
    def is_short(self) -> bool:
        """Return whether this Lamination is short."""

        return self == self.triangulation.disjoint_sum(dict((component, multiplicity) for component, (multiplicity, _, _) in self.parallel_components().items()))

    @memoize
    @finite
    def shorten(self) -> tuple[bigger.Lamination[Edge], bigger.Encoding[Edge]]:  # pylint: disable=too-many-branches
        """Return an :class:`~bigger.encoding.Encoding` that maps self to a short lamination."""

        def shorten_strategy(self: Lamination[Edge], side: bigger.Side[Edge]) -> bool:
            """Return whether flipping this side is a good idea."""

            if not self.triangulation.is_flippable(side):
                return False

            ed, ad, bd = [self.dual(sidey) for sidey in self.triangulation.corner(side)]

            return ed < 0 or (ed == 0 and ad > 0 and bd > 0)  # Non-parallel arc.

        peripheral = self.peripheral()
        lamination = self - peripheral
        conjugator = self.triangulation.identity()
        arc_components, curve_components = dict(), dict()
        while True:
            # Subtract.
            for component, (multiplicity, side, is_arc) in lamination.parallel_components().items():
                lamination = lamination - component * multiplicity
                if is_arc:
                    arc_components[side] = multiplicity
                else:  # is a curve.
                    curve_components[side] = multiplicity

            if not lamination:
                break

            # The arcs will be dealt with in the first round and once they are gone, they are gone.
            extra: Iterable[bigger.Side[Edge]] = []  # High priority edges to check.
            while True:
                try:
                    side = next(side for side in chain(extra, lamination.supporting_sides()) if shorten_strategy(lamination, side))
                except StopIteration:
                    break

                extra = lamination.triangulation.corner(~side)[1:]

                move = lamination.triangulation.flip({side})  # side is always flippable.
                conjugator = move * conjugator
                lamination = move(lamination)
                peripheral = move(peripheral)

            # Now all arcs should be parallel to edges and there should now be no bipods.
            assert all(lamination.left(side) >= 0 for side in lamination.supporting_sides())
            assert all(sum(1 if lamination.left(side) > 0 else 0 for side in lamination.triangulation.triangle(side)) != 2 for side in lamination.supporting_sides())

            used_sides = set()
            hits: Dict[Edge, int] = defaultdict(int)
            triangulation = lamination.triangulation
            # Build a parallel multiarc. This is pretty inefficient.
            for starting_side in lamination.supporting_sides():
                if starting_side in used_sides or not lamination.left(starting_side):
                    continue

                side = starting_side
                add_sequence = False
                while True:  # Until we get back to the starting point.
                    used_sides.add(side)
                    if add_sequence:  # Only record the edge in the sequence once we have made a right turn away from the vertex.
                        hits[side.edge] += 1

                    # Move around to the next edge following the lamination.
                    side = triangulation.left(~side) if lamination.left(~side) > 0 else triangulation.right(~side)

                    add_sequence = add_sequence or lamination.right(side) <= 0
                    if side == starting_side:
                        break

            if hits:
                multiarc = triangulation(hits)
                # Recurse an use multiarc.shorten() now.
                _, sub_conjugator = multiarc.shorten()
                conjugator = sub_conjugator * conjugator
                lamination = sub_conjugator(lamination)
                peripheral = sub_conjugator(peripheral)

        # Rebuild the image of self under conjugator from its components.
        short = lamination.triangulation.disjoint_sum(
            dict(
                [(peripheral, 1)]
                + [(lamination.triangulation.side_arc(edge), multiplicity) for edge, multiplicity in arc_components.items()]
                + [(lamination.triangulation.side_curve(edge), multiplicity) for edge, multiplicity in curve_components.items()]
            )
        )

        return short, conjugator

    def twist(self, power: int = 1) -> bigger.Encoding[Edge]:
        """Return an :class:`~bigger.encoding.Encoding` that performs a Dehn twist about this Lamination.

        Assumes but does not check that this lamination is a multicurve."""

        if self.is_finitely_supported():
            short, conjugator = self.shorten()

            twist = short.triangulation.identity()
            for multiplicity, a, is_arc in short.parallel_components().values():
                assert not is_arc
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
                #  return self.meeting(edge).twist(lamination, power)
                # But by now using twisted_by we can get additional performance through memoization.
                return lamination.twisted_by(self.meeting(edge), power=power)(edge)

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
                return lamination.twisted_by(self.meeting(edge), power=-power)(edge)

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
    def twisted_by(self, multicurve: Lamination[Edge], power: int = 1) -> Lamination[Edge]:
        """Return multicurve.twist()(self).

        This is used purely for performance by allowing for memoization in self.twist."""

        return multicurve.twist(power)(self)

    @finite
    def intersection(self, *laminations: Lamination[Edge]) -> int:
        """Return the number of times that self intersects other."""

        short, conjugator = self.shorten()
        short_laminations = [conjugator(lamination) for lamination in laminations]

        intersection = 0

        # Peripheral components.
        for _, (multiplicity, vertex) in short.peripheral_components().items():
            for lamination in laminations:
                intersection += multiplicity * sum(max(-lamination(edge), 0) + max(-lamination.left(edge), 0) for edge in vertex)

        # Parallel components.
        for _, (multiplicity, p, is_arc) in short.parallel_components().items():
            if is_arc:
                for short_lamination in short_laminations:
                    intersection += multiplicity * max(short_lamination(p), 0)
            else:  # is curve
                walk = list(self.triangulation.walk_vertex(p))
                v_edges = walk[:1]  # The set of edges that come out of v from p round to ~p.

                for short_lamination in short_laminations:
                    around_v = bigger.utilities.maximin([0], (short_lamination.left(edgy) for edgy in v_edges))
                    out_v = sum(max(-short_lamination.left(edge), 0) for edge in v_edges) + sum(max(-short_lamination(edge), 0) for edge in v_edges[1:])
                    # around_v > 0 ==> out_v == 0; out_v > 0 ==> around_v == 0.
                    intersection += multiplicity * (max(short_lamination(p), 0) - 2 * around_v + out_v)

        return intersection

    def draw(self, edges: list[Edge], **options: Any) -> Image:
        """Return a PIL image of this Lamination around the given edges."""

        return bigger.draw(self, edges=edges, **options)
