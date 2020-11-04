""" Example ladder surfaces. """

from __future__ import annotations

from typing import Tuple

import bigger
from bigger.types import Triangle, FlatTriangle
from .utils import integers, extract_curve_and_test

Edge = Tuple[int, int]


def ladder() -> bigger.MCG[Edge]:
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

    def link(edge: Edge) -> Tuple[Edge, Edge, Edge, Edge]:
        n, k = edge
        return {
            0: ((n, 1), (n, 2), (n - 1, 7), (n - 1, 8)),
            1: ((n - 1, 5), (n - 1, 6), (n, 2), (n, 0)),
            2: ((n, 0), (n, 1), (n, 3), (n, 4)),
            3: ((n, 4), (n, 2), (n, 5), (n, 6)),
            4: ((n, 2), (n, 3), (n, 7), (n, 8)),
            5: ((n, 6), (n, 3), (n, 6), (n + 1, 1)),
            6: ((n, 3), (n, 5), (n + 1, 1), (n, 5)),
            7: ((n, 8), (n, 4), (n, 8), (n + 1, 0)),
            8: ((n + 1, 0), (n, 7), (n, 4), (n, 7)),
        }[k]

    T = bigger.Triangulation(lambda: ((x, y) for x in integers() for y in range(9)), link)

    shift = T.isometry(lambda edge: (edge[0] + 1, edge[1]), lambda edge: (edge[0] - 1, edge[1]))

    def generator(name: str) -> bigger.Encoding[Edge]:
        if name in ("s", "shift"):
            return shift

        curve, test = extract_curve_and_test("ab", name)

        if curve == "a":
            isom = lambda edge: (edge[0], [0, 1, 2, 3, 4, 5, 6, 8, 7][edge[1]]) if test(edge[0]) else edge
            return T.encode([(isom, isom), lambda edge: edge[1] == 8 and test(edge[0])])
        if curve == "b":
            isom = lambda edge: (edge[0], [0, 1, 2, 3, 4, 6, 5, 7, 8][edge[1]]) if test(edge[0]) else edge
            return T.encode([(isom, isom), lambda edge: edge[1] == 6 and test(edge[0])])

        raise ValueError("Unknown mapping class {}".format(name))

    def layout(triangle: Triangle) -> FlatTriangle:
        n, k = triangle[0]
        return {
            0: ((n + 0.25, -0.25), (n, 0.0), (n + 0.25, 0.25)),
            2: ((n + 0.25, -0.25), (n + 0.25, 0.25), (n + 0.5, 0.0)),
            3: ((n + 0.5, 0.0), (n + 0.25, 0.25), (n + 1.25, 0.3)),
            5: ((n + 1.0, 0.05), (n + 0.5, 0.0), (n + 1.25, 0.3)),
            4: ((n + 0.25, -0.25), (n + 0.5, 0.0), (n + 1.25, -0.25)),
            7: ((n + 1.25, -0.25), (n + 0.5, 0.0), (n + 1.0, 0.0)),
        }[k]

    return bigger.MCG(T, generator, layout)
