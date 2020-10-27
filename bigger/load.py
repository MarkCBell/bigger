""" Functions for building example mapping class groups. """

from __future__ import annotations

import re
from itertools import count
from typing import Any, Callable, Iterable, Tuple

import bigger
from .types import Triangle, FlatTriangle


def integers() -> Iterable[int]:
    """ Return an iterable that yields all of the integers. """

    for i in count():
        yield i
        yield ~i


def extract_curve_and_test(curve_names: str, name: str) -> Tuple[str, Callable[[Any], bool]]:
    """ Return a curve and a test to apply for which of it's components to twist. """

    twist_match = re.match(r"(?P<curve>[%s])_(?P<n>-?\d+)$" % (curve_names), name)
    twist_mod_match = re.match(r"(?P<curve>[%s])(\[(?P<p>\d+)(, *(?P<k>-?\d+))?\])?$" % (curve_names), name)
    twist_expr_match = re.match(r"(?P<curve>[%s])\{(?P<expr>.*)\}$" % (curve_names), name)

    if twist_match is not None:
        parameters = twist_match.groupdict()
        curve = parameters["curve"]
        n = int(parameters["n"])
        test = lambda edge: edge == n
    elif twist_mod_match is not None:
        parameters = twist_mod_match.groupdict()
        curve = parameters["curve"]
        p = int(parameters["p"]) if parameters["p"] is not None else 1
        k = int(parameters["k"]) if parameters["k"] is not None else 0
        test = lambda edge: edge % p == k
    elif twist_expr_match is not None:
        parameters = twist_expr_match.groupdict()
        curve = parameters["curve"]
        test = lambda n: eval(parameters["expr"], {"n": n, **globals()})  # pylint: disable=eval-used
    else:
        raise ValueError("Unknown mapping class {}".format(name))

    return curve, test


def flute() -> bigger.MCG[int]:
    """The infinitely punctured sphere, with punctures that accumulate in one direction.

    With mapping classes:

     - a_n which twists about the curve parallel to edges n and n+1
     - b_n which twists about the curve which separates punctures n and n+1
     - a{expr(n)} which twists about all a_n curves when expr(n) is True
     - b{expr(n)} which twists about all b_n curves when expr(n) is True

    Shortcuts:

     - a[p, k] == a{n % p == k}
     - a[p] == a[p, 0]
     - a == a[1]
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

    def generator(name: str) -> bigger.Encoding[int]:
        curve, test = extract_curve_and_test("ab", name)

        if curve == "a":
            a_isom = lambda edge: (edge + [0, +1, -1][edge % 3]) if edge >= 0 and test(edge // 3) else edge
            return T.encode([(a_isom, a_isom), lambda edge: edge % 3 == 2 and edge >= 0 and test(edge // 3)])
        if curve == "b":

            def b_isom(edge: int) -> int:
                if edge % 3 == 0:
                    if test(edge // 3):
                        return edge + 3
                    if test(edge // 3 - 1):
                        return edge - 3
                    return edge
                if edge % 3 == 1:
                    if test(edge // 3 - 1):
                        return edge - 6
                    if test(edge // 3 + 1):
                        return edge + 6
                return edge

            prefix = T.encode(
                [
                    lambda edge: edge % 3 == 2 and (test(edge // 3 - 1) or test(edge // 3 + 1)),
                    lambda edge: edge % 3 == 1 and test(edge // 3),
                    lambda edge: edge % 3 == 0 and (test(edge // 3) or test(edge // 3 - 1)),
                ]
            )
            twist = prefix.target.encode(
                [
                    (b_isom, b_isom),
                    lambda edge: edge % 3 == 1 and (test(edge // 3 - 1) or test(edge // 3 + 1)),
                    lambda edge: edge % 3 == 0 and (test(edge // 3) or test(edge // 3 - 1)),
                ]
            )
            return ~prefix * twist * prefix

        raise ValueError("Unknown mapping class {}".format(name))

    def layout(triangle: Triangle) -> FlatTriangle:
        if triangle[0] == -1:
            return (0.0, 1.0), (-1.0, 0.5), (0.0, 0.0)
        elif triangle[0] % 3 == 0:
            n = triangle[0] // 3
            return (n, 1.0), (n, 0.0), (n + 1.0, 1.0)
        else:  # triangle[0] % 3 == 1:
            n = triangle[0] // 3
            return (n + 1.0, 1.0), (n, 0.0), (n + 1.0, 0.0)

    return bigger.MCG(T, generator, layout)


def biflute() -> bigger.MCG[int]:
    """The infinitely punctured sphere, with punctures that accumulate in two directions.

    With mapping classes:

     - a_n which twists about the curve parallel to edges n and n+1
     - b_n which twists about the curve which separates punctures n and n+1
     - a{expr(n)} which twists about all a_n curves when expr(n) is True
     - b{expr(n)} which twists about all b_n curves when expr(n) is True
     - s which shifts the surface down
     - r which rotates the surface fixing the curve a_0

    Shortcuts:

     - a[p, k] == a{n % p == k}
     - a[p] == a[p, 0]
     - a == a[1]

    Note: Since b_n and b_{n+1} intersect, any b expression cannot be true for consecutive values.
    """

    #  ---#----2----#----5----#----8----#---
    #     |        /|        /|        /|
    #     |      /  |      /  |      /  |
    # ... 0    1    3    4    6    7    9 ...
    #     |  /      |  /      |  /      |
    #     |/        |/        |/        |
    #  ---#----2----#----5----#----8----#---

    T = bigger.Triangulation(
        integers,
        lambda edge: [(edge - 2, edge - 1, edge + 1, edge + 2), (edge + 1, edge - 1, edge + 1, edge + 2), (edge + 1, edge - 1, edge - 2, edge - 1)][edge % 3],
    )

    shift = T.isometry(lambda edge: edge + 3, lambda edge: edge - 3)
    rotate = T.isometry(lambda edge: [3, 2, 4][edge % 3] - edge, lambda edge: [3, 2, 4][edge % 3] - edge)

    def generator(name: str) -> bigger.Encoding[int]:
        if name in ("s", "shift"):
            return shift

        if name in ("r", "rotate"):
            return rotate

        curve, test = extract_curve_and_test("ab", name)

        if curve == "a":
            a_isom = lambda edge: (edge + [0, +1, -1][edge % 3]) if test(edge // 3) else edge
            return T.encode([(a_isom, a_isom), lambda edge: edge % 3 == 2 and test(edge // 3)])
        if curve == "b":

            def b_isom(edge: int) -> int:
                if edge % 3 == 0:
                    if test(edge // 3):
                        return edge + 3
                    if test(edge // 3 - 1):
                        return edge - 3
                    return edge
                if edge % 3 == 1:
                    if test(edge // 3 - 1):
                        return edge - 6
                    if test(edge // 3 + 1):
                        return edge + 6
                return edge

            prefix = T.encode(
                [
                    lambda edge: edge % 3 == 2 and (test(edge // 3 - 1) or test(edge // 3 + 1)),
                    lambda edge: edge % 3 == 1 and test(edge // 3),
                    lambda edge: edge % 3 == 0 and (test(edge // 3) or test(edge // 3 - 1)),
                ]
            )
            twist = prefix.target.encode(
                [
                    (b_isom, b_isom),
                    lambda edge: edge % 3 == 1 and (test(edge // 3 - 1) or test(edge // 3 + 1)),
                    lambda edge: edge % 3 == 0 and (test(edge // 3) or test(edge // 3 - 1)),
                ]
            )
            return ~prefix * twist * prefix

        raise ValueError("Unknown mapping class {}".format(name))

    def layout(triangle: Triangle) -> FlatTriangle:
        if triangle[0] % 3 == 0:
            n = triangle[0] // 3
            return (n, 1.0), (n, 0.0), (n + 1.0, 1.0)
        else:  # triangle[0] % 3 == 1:
            n = triangle[0] // 3
            return (n + 1.0, 1.0), (n, 0.0), (n + 1.0, 0.0)

    return bigger.MCG(T, generator, layout)


def ladder() -> bigger.MCG[Tuple[int, int]]:
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


def spotted_cantor() -> bigger.MCG[Tuple[int, int]]:
    """The uncountably-punctured sphere.

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

    T = bigger.Triangulation(lambda: ((x, y) for x in count() for y in range(4)), link)

    def generator(name: str) -> bigger.Encoding[Tuple[int, int]]:
        curve, test = extract_curve_and_test("a", name)

        if curve == "a":
            isom = lambda edge: (edge[0], [1, 0, 2, 3][edge[1]]) if test(edge[0]) else edge
            return T.encode([(isom, isom), lambda edge: edge[1] == 0 and test(edge[0])])

        raise ValueError("Unknown mapping class {}".format(name))

    return bigger.MCG(T, generator)


def cantor() -> bigger.MCG[Tuple[int, int]]:  # pylint: disable=too-many-statements
    """A sphere minus a cantor set.

    With mapping classes:

     - a_n which twists about the curve about the nth hole
     - b_n which twists about the curve about the nth hole
     - r an order two rotation
    """

    Edge = Tuple[int, int]
    Link = Tuple[Edge, Edge, Edge, Edge]
    POS, EQ, NEG = +1, 0, -1

    def invert(sign: int, X: Link) -> Link:
        return X if sign == POS else (X[1], X[0], X[3], X[2])

    def link(edge: Edge) -> Link:
        n, k = edge
        if k == EQ:  # Equator
            if n == 0:
                return ((1, POS), (0, POS), (0, NEG), (1, NEG))
            elif n == 1:
                return ((2, POS), (0, POS), (0, NEG), (2, NEG))
            else:  # n > 1
                return ((3 * n - 1, POS), (3 * n - 3, POS), (3 * n - 3, NEG), (3 * n - 1, NEG))

        # Northern / Southern hemisphere.
        if n == 0:
            return invert(k, ((0, EQ), (1, k), (1, EQ), (2, k)))
        elif n == 1:
            return invert(k, ((4, k), (3, k), (0, k), (0, EQ)))
        elif n == 2:
            return invert(k, ((0, k), (1, EQ), (7, k), (6, k)))
        N, r = n // 3 + 1, n % 3
        incoming = 3 * (N // 2) - (1 if N % 2 else 2)
        if r == 0:
            return invert(k, ((incoming, k), (n + 1, k), (N, EQ), (n + 2, k)))
        elif r == 1:
            return invert(k, ((n - 1, k), (incoming, k), (6 * N - 2, k), (6 * N - 3, k)))
        else:  # r == 2:
            return invert(k, ((n - 2, k), (N, EQ), (6 * N + 1, k), (6 * N + 0, k)))

    T = bigger.Triangulation(lambda: ((x, y) for x in count() for y in [+1, 0, -1]), link)

    def generator(name: str) -> bigger.Encoding[Tuple[int, int]]:  # pylint: disable=too-many-branches
        twist_match = re.match(r"(?P<curve>[ab])_(?P<n>-?\d+)$", name)
        rotate_match = re.match(r"r$", name)

        if twist_match is not None:
            parameters = twist_match.groupdict()
            curve_name = parameters["curve"]
            N = int(parameters["n"])
            if curve_name == "a":
                if N == 1:
                    cut_sequence = [(0, EQ), (0, POS), (1, EQ)]
                else:
                    cut_sequence = [(0, EQ), (N, EQ), (3 * N - 3, POS)]
                    while N > 1:
                        low_N = N // 2
                        cut_sequence.append((3 * low_N - (1 if N % 2 else 2), POS))
                        if N % 2:
                            cut_sequence.append((3 * low_N - 3, POS))
                        N = low_N
            elif curve_name == "b":
                if N <= 3:
                    cut_sequence = [(0, EQ), (0, POS), (1, EQ)]
                else:
                    extend_left = N % 2
                    N = N // 2
                    cut_sequence = [(N, EQ), (3 * N - 3, POS)]
                    while N > 1:
                        N_low = N // 2
                        cut_sequence.append((3 * N_low - (1 if N % 2 else 2), POS))
                        if extend_left:
                            cut_sequence.append((3 * N_low - 3, POS))
                        if N % 2 != extend_left:
                            cut_sequence.append((N_low, EQ))
                            break
                        N = N_low
                    else:
                        cut_sequence.append((0, EQ))

            curve = T(dict(((x, y * s), 1) for x, y in cut_sequence for s in [+1, -1]))
            return curve.twist()
        elif rotate_match is not None:

            def isom(edge: Edge) -> Edge:
                n, k = edge
                if k == EQ:
                    if n == 0:
                        return (1, EQ)
                    elif n == 1:
                        return (0, EQ)
                    return (n ^ (1 << n.bit_length() - 2), k)

                if n == 0:
                    return (0, k)
                elif n == 1:
                    return (2, k)
                elif n == 2:
                    return (1, k)
                N, r = n // 3 + 1, n % 3
                return (3 * (N ^ (1 << N.bit_length() - 2)) - 3 + r, k)

            return T.encode([(isom, isom)])

        raise ValueError("Unknown mapping class {}".format(name))

    return bigger.MCG(T, generator)
