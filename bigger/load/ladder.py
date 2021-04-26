""" Example ladder surfaces. """

from __future__ import annotations

from typing import Tuple, Iterable

import bigger
from bigger.types import FlatTriangle
from bigger.triangulation import Triangle
from .utils import integers, extract_curve_and_test

Edge = Tuple[int, int]


def ladder() -> bigger.MCG[Edge]:
    """The infinite-genus, two-ended surface.

    With mapping classes:

     - a which twists about the vertical curves
     - b which twists about the horizontal curves
     - s which shifts the surface down"""

    #  #---n,2---#
    #  |        /|
    #  |      /  |
    # n,0  n,1 n+1,0
    #  |  /      |
    #  |/        |
    #  #---n,3---#
    #  |        /|
    #  |      /  |
    # n,4  n,5  n,4
    #  |  /      |
    #  |/        |
    #  #---n,2---#

    def edges() -> Iterable[Edge]:
        for x in integers():
            for y in range(6):
                yield x, y

    def link(edge: Edge) -> tuple[Edge, bool, Edge, bool, Edge, bool, Edge, bool]:
        n, k = edge
        return {
            0: ((n - 1, 1), False, (n - 1, 3), True, (n, 1), True, (n, 2), False),
            1: ((n, 2), False, (n, 0), False, (n, 3), True, (n + 1, 0), True),
            2: ((n, 4), True, (n, 5), False, (n, 0), False, (n, 1), True),
            3: ((n + 1, 0), True, (n, 1), False, (n, 4), False, (n, 5), True),
            4: ((n, 5), False, (n, 2), True, (n, 5), True, (n, 3), False),
            5: ((n, 3), False, (n, 4), False, (n, 2), True, (n, 4), True),
        }[k]

    T = bigger.Triangulation[Edge].from_pos(edges, link)

    shift = T.isometry(T, lambda edge: (edge[0] + 1, edge[1]), lambda edge: (edge[0] - 1, edge[1]))

    def generator(name: str) -> bigger.Encoding[Edge]:
        if name in ("s", "shift"):
            return shift

        curve, test = extract_curve_and_test("ab", name)

        if curve == "a":
            isom = lambda edge: (edge[0], [0, 5, 3, 2, 4, 1][edge[1]]) if test(edge[0]) else edge
            return T.encode(
                [
                    (-1, isom, isom),
                    lambda side: side.edge[1] in {1, 5} and side.orientation and test(side.edge[0]),
                    lambda side: side.edge[1] in {2, 3} and side.orientation and test(side.edge[0]),
                ]
            )
        if curve == "b":
            isom = lambda edge: (edge[0], [0, 1, 2, 3, 5, 4][edge[1]]) if test(edge[0]) else edge
            return T.encode([(-1, isom, isom), lambda side: side.edge[1] == 5 and side.orientation and test(side.edge[0])])

        raise ValueError("Unknown mapping class {}".format(name))

    def layout(triangle: Triangle[Edge]) -> FlatTriangle:
        n, k = triangle[0].edge
        return {
            0: ((n, 2.0), (n, 1.0), (n + 1.0, 2.0)),
            1: ((n + 1.0, 2.0), (n, 1.0), (n + 1.0, 1.0)),
            3: ((n + 1.0, 1.0), (n, 1.0), (n + 0.1, 0.0)),
            2: ((n + 0.1, 0.0), (n + 1.0 - 0.1, 0.0), (n + 1.0, 1.0)),
        }[k]

    return bigger.MCG(T, generator, layout)


def spotted_ladder() -> bigger.MCG[Edge]:
    """The infinite-genus, two-ended surface.

    With mapping classes:

     - a_n which twists about the curve parallel to edges n and n+1
     - b_n which twists about the curve which separates punctures n and n+1
     - a which twists about all a_n curves simultaneously
     - b which twists about all b_n curves simultaneously
     - s which shifts the surface down
    """

    #  #---n,0---#---n,8---#
    #  |        /|        /|
    #  |      /  |      /  |
    # n,1  n,2  n,4  n,7  n+1,0
    #  |  /      |  /      |
    #  |/        |/        |
    #  #---n,3---#---n,8---#
    #  |        /|
    #  |      /  |
    # n,5  n,6  n,5
    #  |  /      |
    #  |/        |
    #  #--n+1,1--#

    def edges() -> Iterable[Edge]:
        for x in integers():
            for y in range(9):
                yield x, y

    def link(edge: Edge) -> tuple[Edge, bool, Edge, bool, Edge, bool, Edge, bool]:
        n, k = edge
        return {
            0: ((n - 1, 7), False, (n - 1, 8), True, (n, 1), False, (n, 2), True),
            1: ((n - 1, 5), True, (n - 1, 6), False, (n, 2), True, (n, 0), False),
            2: ((n, 0), False, (n, 1), False, (n, 3), True, (n, 4), True),
            3: ((n, 4), True, (n, 2), False, (n, 5), False, (n, 6), True),
            4: ((n, 2), False, (n, 3), True, (n, 7), True, (n, 8), False),
            5: ((n, 6), False, (n + 1, 1), True, (n, 6), True, (n, 3), False),
            6: ((n, 3), False, (n, 5), False, (n + 1, 1), True, (n, 5), True),
            7: ((n, 8), False, (n, 4), False, (n, 8), True, (n + 1, 0), True),
            8: ((n + 1, 0), True, (n, 7), False, (n, 4), False, (n, 7), True),
        }[k]

    T = bigger.Triangulation.from_pos(edges, link)

    shift = T.isometry(T, lambda edge: (edge[0] + 1, edge[1]), lambda edge: (edge[0] - 1, edge[1]))

    def generator(name: str) -> bigger.Encoding[Edge]:
        if name in ("s", "shift"):
            return shift

        curve, test = extract_curve_and_test("ab", name)

        if curve == "a":
            isom = lambda edge: (edge[0], [0, 1, 2, 3, 4, 5, 6, 8, 7][edge[1]]) if test(edge[0]) else edge
            return T.encode([(-1, isom, isom), lambda side: side.edge[1] == 8 and side.orientation and test(side.edge[0])])
        if curve == "b":
            isom = lambda edge: (edge[0], [0, 1, 2, 3, 4, 6, 5, 7, 8][edge[1]]) if test(edge[0]) else edge
            return T.encode([(-1, isom, isom), lambda side: side.edge[1] == 6 and side.orientation and test(side.edge[0])])

        raise ValueError("Unknown mapping class {}".format(name))

    def layout(triangle: Triangle) -> FlatTriangle:
        n, k = triangle[0].edge
        return {
            0: ((n + 0.25, -0.25), (n, 0.0), (n + 0.25, 0.25)),
            2: ((n + 0.25, -0.25), (n + 0.25, 0.25), (n + 0.5, 0.0)),
            3: ((n + 0.5, 0.0), (n + 0.25, 0.25), (n + 1.25, 0.3)),
            5: ((n + 1.0, 0.05), (n + 0.5, 0.0), (n + 1.25, 0.3)),
            4: ((n + 0.25, -0.25), (n + 0.5, 0.0), (n + 1.25, -0.25)),
            7: ((n + 1.25, -0.25), (n + 0.5, 0.0), (n + 1.0, 0.0)),
        }[k]

    return bigger.MCG(T, generator, layout)
