""" A module for representing a triangulation of a punctured surface. """

from __future__ import annotations

from functools import partial
from dataclasses import dataclass
from typing import Any, Callable, Generic, Iterable, Iterator, Mapping, Union, Optional, Tuple, cast
from PIL import Image  # type: ignore

import bigger
from bigger.types import Edge


@dataclass(order=True, frozen=True)
class Side(Generic[Edge]):
    """Represents a side of an edge."""

    edge: Edge
    orientation: bool = True

    def __invert__(self) -> Side[Edge]:
        """Return the other side of this edge."""
        return Side(self.edge, not self.orientation)

    def __pos__(self) -> Side[Edge]:
        return Side(self.edge, True)

    def __neg__(self) -> Side[Edge]:
        return Side(self.edge, False)


Triangle = Tuple[Side[Edge], Side[Edge], Side[Edge]]
Square = Tuple[Side[Edge], Side[Edge], Side[Edge], Side[Edge]]
Star = Tuple[Side[Edge], Side[Edge], Side[Edge], Side[Edge], Side[Edge]]
Tetra = Tuple[Side[Edge], Side[Edge], Side[Edge], Side[Edge], Side[Edge], Side[Edge]]


def unorient_functor(f: Callable[[Side[Edge]], Side[Edge]]) -> Callable[[Edge], Edge]:
    """Return a function on edges from a function on sides."""
    return lambda edge: f(Side(edge)).edge


class Triangulation(Generic[Edge]):
    """A triangulation of a (possibly infinite type) surface.

    The triangulation is specified via two functions:

     - edges: which returns an iterable over the edges of the triangulation, and
     - link: which maps an oriented edge to its link, i.e., link(e) = (a, b, c, d)

    #<---a----#
    |        ^^
    |      /  |
    b    e    d
    |  /      |
    V/        |
    #----c--->#
    """

    def __init__(self, edges: Callable[[], Iterable[Edge]], link: Callable[[Side[Edge]], Square[Edge]]) -> None:

        # We could define the link by a function that takes Edges as input
        # It could also return Side[Edge] or Tuples[Edge, bool].

        self.edges = edges
        self.link = link

    @classmethod
    def from_pos(cls, edges: Callable[[], Iterable[Edge]], ulink: Callable[[Edge], tuple[Edge, bool, Edge, bool, Edge, bool, Edge, bool]]) -> Triangulation[Edge]:
        """Return a triangulation from a link function defined on only the positive edges."""

        def link(side: Side[Edge]) -> Square[Edge]:
            """The full link function."""

            X = ulink(side.edge)
            if not side.orientation:
                X = X[4:] + X[:4]

            return Side(X[0], X[1]), Side(X[2], X[3]), Side(X[4], X[5]), Side(X[6], X[7])

        return cls(edges, link)

    def star(self, side: Side[Edge]) -> Star[Edge]:
        """Return the link of an Side together with the Side itself."""

        return self.link(side) + (side,)

    def tetra(self, side: Side[Edge]) -> Tetra[Edge]:
        """Return the link of an Side together with the Side itself and its inverse."""

        return self.link(side) + (side, ~side)

    def corner(self, side: bigger.Side[Edge]) -> Triangle[Edge]:
        """Return the triangle starting at this side."""

        a, b, _, _ = self.link(side)
        return (side, a, b)

    def triangle(self, side: Side[Edge]) -> Triangle[Edge]:
        """Return the triangle containing this side."""

        triangle = self.corner(side)
        triangle = min(triangle, triangle[1:] + triangle[:1], triangle[2:] + triangle[:2])
        return triangle

    def __iter__(self) -> Iterator[Edge]:
        return iter(self.edges())

    def flip(self, is_flipped: Union[Callable[[Side[Edge]], bool], set[Side[Edge]]]) -> bigger.Encoding[Edge]:
        """Return an :class:`~bigger.encoding.Encoding` consisting of a single :class:`~bigger.encoding.Move` which flips all edges where :attr:`is_flipped` is True.

        Alternatively, this can be given a set of Sides and will use membership of this set to test which edges flip.
        Note that if :attr:`is_flipped` is True for edge then it must be False for all edge in its link and ~edge."""

        if isinstance(is_flipped, set):
            # Start again with the function lambda edge: edge in is_flipped.
            return self.flip(is_flipped.__contains__)

        flipped = is_flipped

        # Use the following for reference:
        # #<---a----#     #<---a----#
        # |        ^^     |\        ^
        # |      /  |     |  \      |
        # b    e    d --> b    e    d
        # |  /      |     |      \  |
        # V/        |     V        V|
        # #----c--->#     #----c--->#

        # Define the new triangulation.
        def link(e: Side[Edge]) -> Square[Edge]:
            a, b, c, d = self.link(e)
            for x in [a, b, c, d, e]:
                assert not (flipped(x) and flipped(~x)), "Flipping both {} and {}".format(x, ~x)

            if flipped(e):
                assert not flipped(~e), "Flipping both {} and {}".format(e, ~e)
                for x in [a, ~a, b, ~b, c, ~c, d, ~d]:
                    assert not flipped(x), "Flipping {} and {} which do not have disjoint support".format(e, x)

                return (d, a, b, c)
            elif flipped(~e):
                assert not flipped(e), "Flipping both {} and {}".format(e, ~e)
                for x in [a, ~a, b, ~b, c, ~c, d, ~d]:
                    assert not flipped(x), "Flipping {} and {} which do not have disjoint support".format(~e, x)

                return (b, c, d, a)

            def side_edges(p: Side[Edge], q: Side[Edge]) -> tuple[Side[Edge], Side[Edge]]:
                """Return the two new sides formed by p & q."""
                if flipped(+p):
                    _, _, w, _, _, x = self.tetra(p)
                elif flipped(-p):
                    _, _, w, _, x, _ = self.tetra(p)
                elif flipped(+q):
                    _, _, _, x, w, _ = self.tetra(q)
                elif flipped(-q):
                    _, _, _, x, _, w = self.tetra(q)
                else:
                    w, x = p, q
                return w, x

            w, x = side_edges(a, b)
            y, z = side_edges(c, d)

            return w, x, y, z

        target = Triangulation(self.edges, link)

        # Since the action and inv_action are so similar, we define both at once and just use a partial function to set the correct source / target.
        def helper(source: bigger.Triangulation[Edge], target: bigger.Triangulation[Edge], lamination: bigger.Lamination[Edge]) -> bigger.Lamination[Edge]:
            def weight(edge: Edge) -> int:
                oedge = Side(edge)
                if not flipped(oedge) and not flipped(~oedge):
                    return lamination(edge)

                # Compute fi.
                ei = lamination(edge)
                ai0, bi0, ci0, di0 = [max(lamination(side), 0) for side in source.link(Side(edge))]

                if ei >= ai0 + bi0 and ai0 >= di0 and bi0 >= ci0:  # CASE: A(ab)
                    return ai0 + bi0 - ei
                elif ei >= ci0 + di0 and di0 >= ai0 and ci0 >= bi0:  # CASE: A(cd)
                    return ci0 + di0 - ei
                elif ei <= 0 and ai0 >= bi0 and di0 >= ci0:  # CASE: D(ad)
                    return ai0 + di0 - ei
                elif ei <= 0 and bi0 >= ai0 and ci0 >= di0:  # CASE: D(bc)
                    return bi0 + ci0 - ei
                elif ei >= 0 and ai0 >= bi0 + ei and di0 >= ci0 + ei:  # CASE: N(ad)
                    return ai0 + di0 - 2 * ei
                elif ei >= 0 and bi0 >= ai0 + ei and ci0 >= di0 + ei:  # CASE: N(bc)
                    return bi0 + ci0 - 2 * ei
                elif ai0 + bi0 >= ei and bi0 + ei >= 2 * ci0 + ai0 and ai0 + ei >= 2 * di0 + bi0:  # CASE: N(ab)
                    return bigger.half(ai0 + bi0 - ei)
                elif ci0 + di0 >= ei and di0 + ei >= 2 * ai0 + ci0 and ci0 + ei >= 2 * bi0 + di0:  # CASE: N(cd)
                    return bigger.half(ci0 + di0 - ei)
                else:
                    return max(ai0 + ci0, bi0 + di0) - ei

            # Determine support.
            if lamination.is_finitely_supported():
                support = set(side.edge for edge in lamination.support() for side in target.star(Side(edge)) if weight(side.edge))
                return target(weight, lambda: support)

            return target(weight, lambda: (side.edge for edge in lamination.support() for side in target.star(Side(edge)) if weight(side.edge)))

        action = partial(helper, self, target)
        inv_action = partial(helper, target, self)

        return bigger.Move(self, target, action, inv_action).encode()

    def isometry(self, target: Triangulation[Edge], isom: Callable[[Edge], Edge], inv_isom: Callable[[Edge], Edge]) -> bigger.Encoding[Edge]:
        """Return an :class:`~bigger.encoding.Encoding` which maps edges under the specified relabelling."""

        def action(lamination: bigger.Lamination[Edge]) -> bigger.Lamination[Edge]:
            def weight(edge: Edge) -> int:
                return lamination(inv_isom(edge))

            if lamination.is_finitely_supported():
                support = set(isom(arc) for arc in lamination.support())
                return target(weight, lambda: support)

            return target(weight, lambda: (isom(arc) for arc in lamination.support()))

        def inv_action(lamination: bigger.Lamination[Edge]) -> bigger.Lamination[Edge]:
            def weight(edge: Edge) -> int:
                return lamination(isom(edge))

            if lamination.is_finitely_supported():
                support = set(inv_isom(arc) for arc in lamination.support())
                return self(weight, lambda: support)

            return self(weight, lambda: (inv_isom(arc) for arc in lamination.support()))

        return bigger.Move(self, target, action, inv_action).encode()

    def relabel(self, isom: Callable[[Side[Edge]], Side[Edge]], inv_isom: Callable[[Side[Edge]], Side[Edge]]) -> bigger.Encoding[Edge]:
        """Return an :class:`~bigger.encoding.Encoding` which maps edges under the specified relabelling."""

        # Define the new triangulation.
        def link(side: Side[Edge]) -> Square[Edge]:
            a, b, c, d = self.link(inv_isom(side))
            return (isom(a), isom(b), isom(c), isom(d))

        target = Triangulation(self.edges, link)

        u_isom = unorient_functor(isom)
        u_inv_isom = unorient_functor(inv_isom)

        return self.isometry(target, u_isom, u_inv_isom)

    def relabel_from_dict(self, isom_dict: Mapping[Side[Edge], Side[Edge]]) -> bigger.Encoding[Edge]:
        """Return an :class:`~bigger.encoding.Encoding` which relabels Edges in :attr:`isom_dict` an leaves all other edges unchanged."""
        inv_isom_dict = dict((value, key) for key, value in isom_dict.items())

        def isom(edge: Side[Edge]) -> Side[Edge]:
            return isom_dict.get(edge, ~isom_dict.get(~edge, ~edge))

        def inv_isom(edge: Side[Edge]) -> Side[Edge]:
            return inv_isom_dict.get(edge, ~inv_isom_dict.get(~edge, ~edge))

        return self.relabel(isom, inv_isom)

    def identity(self) -> bigger.Encoding[Edge]:
        """Return an :class:`~bigger.encoding.Encoding` which represents the identity mapping class."""
        return self.relabel_from_dict(dict())

    def encode(
        self,
        sequence: list[
            Union[
                Callable[[Side[Edge]], bool],
                set[Side[Edge]],
                tuple[Callable[[Side[Edge]], Side[Edge]], Callable[[Side[Edge]], Side[Edge]]],
                tuple[int, Callable[[Edge], Edge], Callable[[Edge], Edge]],
                dict[Side[Edge], Side[Edge]],
                Side[Edge],
            ]
        ],
    ) -> bigger.Encoding[Edge]:
        """Return an :class:`~bigger.encoding.Encoding` from a small sequence of data.

        There are several conventions that allow these to be specified by a smaller amount of information:

         - A set or callable is used to flip those edges.
         - A dict or pair of callables is used to encode an isomety.
         - Otherwise, it is assumed to be the label of an edge to flip.

        The sequence is read in reverse in order to respect composition."""
        h = self.identity()
        for term in reversed(sequence):
            if callable(term) or isinstance(term, set):
                move = h.target.flip(term)
            elif isinstance(term, tuple):
                if len(term) == 2:  # and len(term) == 2 and all(callable(item) for item in term):
                    term = cast(Tuple[Callable[[Side[Edge]], Side[Edge]], Callable[[Side[Edge]], Side[Edge]]], term)
                    move = h.target.relabel(*term)
                else:  # len(term) == 3
                    term = cast(Tuple[int, Callable[[Edge], Edge], Callable[[Edge], Edge]], term)
                    T = h[term[0]].source
                    move = h.target.isometry(T, term[1], term[2])
            elif isinstance(term, dict):
                move = h.target.relabel_from_dict(term)
            else:  # Assume term is the label of an edge to flip.
                move = h.target.flip({term})
            h = move * h

        return h

    def __call__(self, weights: Union[dict[Edge, int], Callable[[Edge], int]], support: Optional[Callable[[], Iterable[Edge]]] = None) -> bigger.Lamination[Edge]:
        if isinstance(weights, dict):
            weight_dict = dict((key, value) for key, value in weights.items() if value)

            def weight(edge: Edge) -> int:
                return weight_dict.get(edge, 0)

            return bigger.Lamination(self, weight, lambda: set(weight_dict))

        if support is None:
            support = self.edges

        return bigger.Lamination(self, weights, support)

    def empty_lamination(self) -> bigger.Lamination[Edge]:
        """Return the zero Lamination on this triangulation."""

        return self(lambda edge: 0, support=set)  # set is a callable that returns the empty set.

    def as_lamination(self) -> bigger.Lamination[Edge]:
        """Return this Triangulation as a Lamination on self."""

        return self(lambda edge: -1)

    def draw(self, edges: list[Edge], **options: Any) -> Image:
        """Return a PIL image of this Triangulation around the given edges."""

        return bigger.draw(self, edges=edges, **options)
