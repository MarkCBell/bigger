""" Functions for building example mapping class groups. """

import re
from itertools import count
from typing import Tuple, Iterable

import bigger


def integers() -> Iterable[int]:
    """ Return an iterable that yields all of the integers. """

    for i in count():
        yield i
        yield ~i


def flute() -> "bigger.MCG[int]":
    """ The infinitely punctured sphere, with punctures that accumulate in one direction.

    With mapping classes:

     - a_n which twists about the curve parallel to edges n and n+1
     - b_n which twists about the curve which separates punctures n and n+1
     - a which twists about all an curves simultaneously
    """

    #             #----2----#----5----#----8----#---
    #            /|        /|        /|        /|
    #         -1  |      /  |      /  |      /  |
    #        #    0    1    3    4    6    7    9 ...
    #         -1  |  /      |  /      |  /      |
    #            \|/        |/        |/        |
    #             #----2----#----5----#----8----#---

    T = bigger.Triangulation(
        integers,
        lambda edge: (0, -1, -1, 0)
        if edge == -1
        else (-1, -1, 1, 2)
        if edge == 0
        else [(edge - 2, edge - 1, edge + 1, edge + 2), (edge + 1, edge - 1, edge + 1, edge + 2), (edge + 1, edge - 1, edge - 2, edge - 1)][edge % 3],
    )

    twist_re = re.compile(r"(?P<curve>[aAbB])_(?P<n>\d+)$")

    def generator(name: str) -> "bigger.Encoding[int]":
        twist_match = twist_re.match(name)
        if name == "a":
            isom = lambda edge: -1 if edge == -1 else edge + [0, +1, -1][edge % 3]
            return T.encode([(isom, isom), lambda edge: edge % 3 == 1])
        elif twist_match is not None:
            parameters = twist_match.groupdict()
            n = int(parameters["n"])
            if parameters["curve"] == "a":
                return T({3 * n + 1: 1, 3 * n + 2: 1}).encode_twist()
            if parameters["curve"] == "b":
                return T({3 * n - 2: 1, 3 * n - 1: 1, 3 * n + 0: 2, 3 * n + 1: 2, 3 * n + 3: 2, 3 * n + 4: 1, 3 * n + 5: 1}).encode_twist()

        raise ValueError("Unknown mapping class {}".format(name))

    return bigger.MCG(T, generator)


def biflute() -> "bigger.MCG[int]":
    """ The infinitely punctured sphere, with punctures that accumulate in two directions.

    With mapping classes:

     - a_n which twists about the curve parallel to edges n and n+1
     - b_n which twists about the curve which separates punctures n and n+1
     - a[p, k] which twists about all an curves where n mod p == k simultaneously
     - s which shifts the surface down

    Note: a[p] == a[p, 0] and a == a[1].
    """

    #  ---#----2----#----5----#----8----#---
    #     |        /|        /|        /|
    #     |      /  |      /  |      /  |
    # ... 0    1    3    4    6    7    9 ...
    #     |  /      |  /      |  /      |
    #     |/        |/        |/        |
    #  ---#----2----#----5----#----8----#---

    T = bigger.Triangulation(
        integers, lambda edge: [(edge - 2, edge - 1, edge + 1, edge + 2), (edge + 1, edge - 1, edge + 1, edge + 2), (edge + 1, edge - 1, edge - 2, edge - 1)][edge % 3],
    )

    shift = T.encode_isometry(lambda edge: edge + 3, lambda edge: edge - 3)

    twist_re = re.compile(r"(?P<curve>[ab])_(?P<n>-?\d+)$")
    twist_mod_re = re.compile(r"a(\[(?P<p>\d+)(, *(?P<k>-?\d+))?\])?$")

    def generator(name: str) -> "bigger.Encoding[int]":
        twist_match = twist_re.match(name)
        twist_mod_match = twist_mod_re.match(name)
        if name in ("s", "shift"):
            return shift
        elif twist_match is not None:
            parameters = twist_match.groupdict()
            n = int(parameters["n"])
            if parameters["curve"] == "a":
                return T({3 * n + 1: 1, 3 * n + 2: 1}).encode_twist()
            if parameters["curve"] == "b":
                return T({3 * n - 2: 1, 3 * n - 1: 1, 3 * n + 0: 2, 3 * n + 1: 2, 3 * n + 3: 2, 3 * n + 4: 1, 3 * n + 5: 1}).encode_twist()
        elif twist_mod_match is not None:
            parameters = twist_mod_match.groupdict()
            p = int(parameters["p"]) if parameters["p"] is not None else 1
            k = int(parameters["k"]) if parameters["k"] is not None else 0

            isom = lambda edge: (edge + [0, +1, -1][edge % 3]) if edge // 3 % p == k else edge
            return T.encode([(isom, isom), lambda edge: edge % 3 == 1 and edge // 3 % p == k])

        raise ValueError("Unknown mapping class {}".format(name))

    return bigger.MCG(T, generator)


def ladder() -> "bigger.MCG[Tuple[int, int]]":
    """ The infinite-genus, two-ended surface.

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

    Edge = Tuple[int, int]

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

    shift = T.encode_isometry(lambda edge: (edge[0] + 1, edge[1]), lambda edge: (edge[0] - 1, edge[1]))

    twist_re = re.compile(r"(?P<curve>[aAbB])_(?P<n>-?\d+)$")

    def generator(name: str) -> "bigger.Encoding[Tuple[int, int]]":
        twist_match = twist_re.match(name)
        if name in ("s", "shift"):
            return shift
        elif name == "a":
            a_isom = lambda edge: (edge[0], [0, 1, 2, 3, 4, 5, 6, 8, 7][edge[1]])
            return T.encode([(a_isom, a_isom), lambda edge: edge[1] == 7])
        elif name == "b":
            b_isom = lambda edge: (edge[0], [0, 1, 2, 3, 4, 6, 5, 7, 8][edge[1]])
            return T.encode([(b_isom, b_isom), lambda edge: edge[1] == 6])
        elif twist_match is not None:
            parameters = twist_match.groupdict()
            n = int(parameters["n"])
            if parameters["curve"] == "a":
                return T({(n, 7): 1, (n, 8): 1}).encode_twist()
            if parameters["curve"] == "b":
                return T({(n, 5): 1, (n, 6): 1}).encode_twist()

        raise ValueError("Unknown mapping class {}".format(name))

    return bigger.MCG(T, generator)


def tree3() -> "bigger.MCG[Tuple[int, int]]":
    """ The uncountably-punctured sphere.

    With mapping classes:

     - a_n which twists about the curve across square n
     - a which twists about all a_n curves simultaneously
    """

    #       #
    #      / \
    # 2n+3,2 2n+4,2
    #    /     \
    #   /       \
    #  #---n,3---#
    #  |        /|
    #  |      /  |
    # n,1  n,0  n,1
    #  |  /      |
    #  |/        |
    #  #---n,2---#

    Edge = Tuple[int, int]

    def link(edge: Edge) -> Tuple[Edge, Edge, Edge, Edge]:
        n, k = edge
        # Down:
        X, Y = (((n - 3) // 2, 3), (n + 1, 2)) if n % 2 == 1 else ((n - 1, 2), ((n - 3) // 2, 3))
        # Three special down edges (squares 0, 1, & 2).
        if k == 2 and 0 <= n < 3:
            return {0: ((0, 1), (0, 0), (2, 2), (1, 2)), 1: ((1, 1), (1, 0), (0, 2), (2, 2)), 2: ((2, 1), (2, 0), (1, 2), (0, 2))}[n]

        return {0: ((n, 3), (n, 1), (n, 2), (n, 1)), 1: ((n, 0), (n, 3), (n, 0), (n, 2)), 2: ((n, 1), (n, 0), X, Y), 3: ((n, 1), (n, 0), (2 * n + 4, 2), (2 * n + 3, 2))}[k]

    T = bigger.Triangulation(lambda: ((x, y) for x in integers() for y in range(4)), link)

    twist_re = re.compile(r"(?P<curve>[aAbB])_(?P<n>-?\d+)$")

    def generator(name: str) -> "bigger.Encoding[Tuple[int, int]]":
        twist_match = twist_re.match(name)
        if name == "a":
            a_isom = lambda edge: (edge[0], [1, 0, 2, 3][edge[1]])
            return T.encode([(a_isom, a_isom), lambda edge: edge[1] == 0])
        elif twist_match is not None:
            parameters = twist_match.groupdict()
            n = int(parameters["n"])
            if parameters["curve"] == "a":
                return T({(n, 0): 1, (n, 1): 1}).encode_twist()

        raise ValueError("Unknown mapping class {}".format(name))

    return bigger.MCG(T, generator)
