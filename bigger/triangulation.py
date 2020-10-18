""" A module for representing a triangulation of a punctured surface. """

from __future__ import annotations

from functools import partial
from typing import Any, Callable, Dict, Generic, Iterable, Iterator, List, Mapping, Set, Tuple, Union
from PIL import Image  # type: ignore

import bigger
from bigger.types import Edge


class IterableStore(Generic[Edge]):  # pylint: disable=too-few-public-methods
    """ A restartable iterable that yields Edges. """

    def __init__(self, iterable_spawner: Callable[[], Iterable[Edge]]) -> None:
        self.iterable_spawner = iterable_spawner

    def __iter__(self) -> Iterator[Edge]:
        return iter(self.iterable_spawner())


class Triangulation(Generic[Edge]):
    """A triangulation of a (possibly infinite type) surface.

    The triangulation is specified via two functions:

     - edges: which returns an iterable over the edges of the triangulation, and
     - link: which maps an edge to its link.

    Note that this cannot be used to define S_{1,1} since its edge links are invariant under the hyperelliptic involution."""

    def __init__(self, edges: Union[Iterable[Edge], Callable[[], Iterable[Edge]]], link: Callable[[Edge], Tuple[Edge, Edge, Edge, Edge]]) -> None:
        # Use the following for reference:
        # #----a----#
        # |        /|
        # |      /  |
        # b    e    d
        # |  /      |
        # |/        |
        # #----c----#
        #
        # link(e) = (a, b, c, d)

        if callable(edges):
            edges = IterableStore(edges)
        self.edges = edges
        self._link = link

    def link(self, edge: Edge, **kwargs: Edge) -> Tuple[Edge, Edge, Edge, Edge]:
        """ Return the link of an edge. """

        a, b, c, d = self._link(edge)
        if "a" in kwargs and a != kwargs["a"]:
            a, b, c, d = c, d, a, b
        if "b" in kwargs and b != kwargs["b"]:
            a, b, c, d = c, d, a, b
        if "c" in kwargs and c != kwargs["c"]:
            a, b, c, d = c, d, a, b
        if "d" in kwargs and d != kwargs["d"]:
            a, b, c, d = c, d, a, b

        return a, b, c, d

    def star(self, edge: Edge, **kwargs: Edge) -> Tuple[Edge, Edge, Edge, Edge, Edge]:
        """ Return the link of an Edge together with the Edge itself. """

        return self.link(edge, **kwargs) + (edge,)

    def __iter__(self) -> Iterator[Edge]:
        return iter(self.edges)

    def encode_flip(self, is_flipped: Union[Callable[[Edge], bool], Set[Edge]]) -> bigger.Encoding[Edge]:
        """Return an :class:`~bigger.encoding.Encoding` consisting of a single :class:`~bigger.encoding.Move` which flips all edges where :attr:`is_flipped` is True.

        Alternatively, this can be given a set of Edges and will use membership of this set to test which edges flip.
        Note that if :attr:`is_flipped` is True for an Edge then it must be False for all edge in its link."""

        if isinstance(is_flipped, set):
            # Start again with the function lambda edge: edge in is_flipped.
            return self.encode_flip(is_flipped.__contains__)

        flipped = is_flipped

        # Use the following for reference:
        # #----a----#     #----a----#
        # |        /|     |\        |
        # |      /  |     |  \      |
        # b    e    d --> b    e    d
        # |  /      |     |      \  |
        # |/        |     |        \|
        # #----c----#     #----c----#

        # Define the new triangulation.
        def link(edge: Edge) -> Tuple[Edge, Edge, Edge, Edge]:
            a, b, c, d = self.link(edge)
            if flipped(edge):
                assert not flipped(a), "Flipping edges {} and {} which do not have disjoint support".format(edge, a)
                assert not flipped(b), "Flipping edges {} and {} which do not have disjoint support".format(edge, b)
                assert not flipped(c), "Flipping edges {} and {} which do not have disjoint support".format(edge, c)
                assert not flipped(d), "Flipping edges {} and {} which do not have disjoint support".format(edge, d)

                return (b, c, d, a)

            if flipped(a):
                w, _, _, _, x = self.star(a, c=b, d=edge)
            elif flipped(b):
                _, x, _, _, w = self.star(b, c=edge, d=a)
            else:
                w, x = a, b

            if flipped(c):
                y, _, _, _, z = self.star(c, c=d, d=edge)
            elif flipped(d):
                _, z, _, _, y = self.star(d, c=edge, d=c)
            else:
                y, z = c, d

            return (w, x, y, z)

        target = Triangulation(self.edges, link)

        # Since the action and inv_action are so similar, we define both at once and just use a partial function to set the correct source / target.
        def helper(source: bigger.Triangulation[Edge], target: bigger.Triangulation[Edge], lamination: bigger.Lamination[Edge]) -> bigger.Lamination[Edge]:
            def weight(edge: Edge) -> int:
                if not flipped(edge):
                    return lamination(edge)

                # Compute fi.
                ei = lamination(edge)
                ai0, bi0, ci0, di0 = [max(lamination(edge), 0) for edge in source.link(edge)]

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
            if isinstance(lamination.support, set):
                return target(weight, set(edge for arc in lamination.support for edge in target.star(arc) if weight(edge)))

            return target(weight, lambda: (edge for arc in lamination.support for edge in target.star(arc) if weight(edge)))

        action = partial(helper, self, target)
        inv_action = partial(helper, target, self)

        return bigger.Move(self, target, action, inv_action).encode()

    def encode_isometry(self, isom: Callable[[Edge], Edge], inv_isom: Callable[[Edge], Edge]) -> bigger.Encoding[Edge]:
        """ Return an :class:`~bigger.encoding.Encoding` which maps edges under the specified relabelling. """

        # Define the new triangulation.
        def link(edge: Edge) -> Tuple[Edge, Edge, Edge, Edge]:
            a, b, c, d = self.link(inv_isom(edge))
            return (isom(a), isom(b), isom(c), isom(d))

        target = Triangulation(self.edges, link)

        def action(lamination: bigger.Lamination[Edge]) -> bigger.Lamination[Edge]:
            def weight(edge: Edge) -> int:
                return lamination(inv_isom(edge))

            if isinstance(lamination.support, set):
                return target(weight, set(isom(arc) for arc in lamination.support))

            return target(weight, lambda: (isom(arc) for arc in lamination.support))

        def inv_action(lamination: bigger.Lamination[Edge]) -> bigger.Lamination[Edge]:
            def weight(edge: Edge) -> int:
                return lamination(isom(edge))

            if isinstance(lamination.support, set):
                return self(weight, set(inv_isom(arc) for arc in lamination.support))

            return self(weight, lambda: (inv_isom(arc) for arc in lamination.support))

        return bigger.Move(self, target, action, inv_action).encode()

    def encode_isometry_from_dict(self, isom_dict: Mapping[Edge, Edge]) -> bigger.Encoding[Edge]:
        """ Return an :class:`~bigger.encoding.Encoding` which relabels Edges in :attr:`isom_dict` an leaves all other edges unchanged. """
        inv_isom_dict = dict((value, key) for key, value in isom_dict.items())

        def isom(edge: Edge) -> Edge:
            return isom_dict.get(edge, edge)

        def inv_isom(edge: Edge) -> Edge:
            return inv_isom_dict.get(edge, edge)

        return self.encode_isometry(isom, inv_isom)

    def encode_identity(self) -> bigger.Encoding[Edge]:
        """ Return an :class:`~bigger.encoding.Encoding` which represents the identity mapping class. """
        return self.encode_isometry_from_dict(dict())

    def encode(
        self,
        sequence: List[Union[Tuple[Callable[[Edge], Edge], Callable[[Edge], Edge]], Callable[[Edge], bool], Edge, Set[Edge], Dict[Edge, Edge]]],
    ) -> bigger.Encoding[Edge]:
        """Return an :class:`~bigger.encoding.Encoding` from a small sequence of data.

        There are several conventions that allow these to be specified by a smaller amount of information:

         - A set or callable is used to flip those edges.
         - A dict or pair of callables is used to encode an isomety.
         - Otherwise, it is assumed to be the label of an edge to flip.

        The sequence is read in reverse in order to respect composition."""
        h = self.encode_identity()
        for term in reversed(sequence):
            if isinstance(term, set) or callable(term):
                move = h.target.encode_flip(term)
            elif isinstance(term, dict):
                move = h.target.encode_isometry_from_dict(term)
            elif isinstance(term, tuple):  # and len(term) == 2 and all(callable(item) for item in term):
                move = h.target.encode_isometry(*term)
            else:  # Assume term is the label of an edge to flip.
                move = h.target.encode_flip({term})
            h = move * h

        return h

    def __call__(
        self, weights: Union[Dict[Edge, int], Callable[[Edge], int]], support: Union[Iterable[Edge], Callable[[], Iterable[Edge]], None] = None
    ) -> bigger.Lamination[Edge]:
        if isinstance(weights, dict):
            weight_dict = dict((key, value) for key, value in weights.items() if value)

            def weight(edge: Edge) -> int:
                return weight_dict.get(edge, 0)

            return bigger.Lamination(self, weight, set(weight_dict))

        if support is None:
            support = self.edges
        elif callable(support):
            support = IterableStore(support)

        return bigger.Lamination(self, weights, support)

    def empty_lamination(self) -> bigger.Lamination[Edge]:
        """ Return the zero Lamination on this triangulation. """

        return self(lambda edge: 0)

    def as_lamination(self) -> bigger.Lamination[Edge]:
        """ Return this Triangulation as a Lamination on self. """

        return self(lambda edge: -1)

    def draw(self, edges: List[Edge], **options: Any) -> Image:
        """ Return a PIL image of this Triangulation around the given edges. """

        return bigger.draw(self, edges=edges, **options)
