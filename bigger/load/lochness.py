""" Example lochness surfaces. """

from __future__ import annotations

import bigger
from bigger.types import FlatTriangle
from bigger.triangulation import Triangle
from .utils import integers, extract_curve_and_test

Edge = int


def loch_ness_monster() -> bigger.MCG[Edge]:
    """The infinite-genus, one-ended surface.

    With mapping classes:

     - a which twists about the longitudes of the monster
     - b which twists about the meridians of the monster
     - c which twists about the curves linking the nth and n+1st handles
     - s which shifts the surface down"""

    #  #---n+2---#
    #  |        /|
    #  |      /  |
    #  n   n+1  n+6
    #  |  /      |
    #  |/        |
    #  #---n+3---#
    #  |        /|
    #  |      /  |
    # n+4  n+5  n+4
    #  |  /      |
    #  |/        |
    #  #---n+2---#

    def link(edge: Edge) -> tuple[Edge, bool, Edge, bool, Edge, bool, Edge, bool]:
        n, k = divmod(edge, 6)
        return {
            0: (6 * n - 6 + 1, False, 6 * n - 6 + 3, True, 6 * n + 1, True, 6 * n + 2, False),
            1: (6 * n + 2, False, 6 * n, False, 6 * n + 3, True, 6 * n + 6, True),
            2: (6 * n + 4, True, 6 * n + 5, False, 6 * n, False, 6 * n + 1, True),
            3: (6 * n + 6, True, 6 * n + 1, False, 6 * n + 4, False, 6 * n + 5, True),
            4: (6 * n + 5, False, 6 * n + 2, True, 6 * n + 5, True, 6 * n + 3, False),
            5: (6 * n + 3, False, 6 * n + 4, False, 6 * n + 2, True, 6 * n + 4, True),
        }[k]

    T = bigger.Triangulation[Edge].from_pos(integers, link)

    shift = T.isometry(T, lambda edge: edge + 6, lambda edge: edge - 6)

    def generator(name: str) -> bigger.Encoding[Edge]:
        if name in ("s", "shift"):
            return shift

        curve, test = extract_curve_and_test("abc", name)

        if curve == "a":
            return T(lambda edge: 1 if edge % 6 in {1, 2, 3, 5} and test(edge // 6) else 0).twist()
        if curve == "b":
            return T(lambda edge: 1 if edge % 6 in {4, 5} and test(edge // 6) else 0).twist()
        if curve == "c":

            def c(edge: Edge) -> int:
                n, k = divmod(edge, 6)
                if test(n) and test(n + 1):
                    return {0: 2, 1: 4, 2: 2, 3: 2, 4: 2, 5: 2}[k]
                elif test(n):
                    return {0: 2, 1: 2, 2: 0, 3: 2, 4: 1, 5: 1}[k]
                elif test(n + 1):
                    return {0: 0, 1: 2, 2: 2, 3: 0, 4: 1, 5: 1}[k]
                else:
                    return 0

            return T(c).twist()

        raise ValueError("Unknown mapping class {}".format(name))

    def layout(triangle: Triangle[Edge]) -> FlatTriangle:
        n, k = divmod(triangle[0].edge, 6)
        return {
            0: ((n, 2.0), (n, 1.0), (n + 1.0, 2.0)),
            1: ((n + 1.0, 2.0), (n, 1.0), (n + 1.0, 1.0)),
            3: ((n + 1.0, 1.0), (n, 1.0), (n + 0.1, 0.0)),
            2: ((n + 0.1, 0.0), (n + 1.0 - 0.1, 0.0), (n + 1.0, 1.0)),
        }[k]

    return bigger.MCG(T, generator, layout)
