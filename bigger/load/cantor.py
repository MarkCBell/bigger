""" Example cantor surfaces. """

from __future__ import annotations

import re
from typing import Iterable, Tuple

import bigger
from .utils import naturals, extract_curve_and_test

Edge = Tuple[int, int]
Link = Tuple[Edge, Edge, Edge, Edge]


def spotted_cantor() -> bigger.MCG[Edge]:
    """The uncountably-punctured sphere.

    With mapping classes:

     - a_n which twists about the curve across square n
     - a which twists about all a_n curves simultaneously

     - a[start:stop:step] = a{n in range(start, stop, slice)}
     - a == a[:]
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

    def edges() -> Iterable[Edge]:
        for x in naturals():
            for y in range(4):
                yield x, y

    def link(edge: Edge) -> tuple[Edge, bool, Edge, bool, Edge, bool, Edge, bool]:
        n, k = edge
        # Down:
        X, Y = (((n - 3) // 2, 3), (n + 1, 2)) if n % 2 == 1 else ((n - 1, 2), ((n - 3) // 2, 3))
        # Three special down edges (squares 0, 1, & 2).
        if k == 2 and 0 <= n < 3:
            return ((n, 1), True, (n, 0), False, ((n + 2) % 3, 2), False, ((n + 1) % 3, 2), False)

        return {
            0: ((n, 3), False, (n, 1), False, (n, 2), True, (n, 1), True),
            1: ((n, 0), False, (n, 2), True, (n, 0), True, (n, 3), False),
            2: ((n, 1), True, (n, 0), False, X, True, Y, False),
            3: ((2 * n + 4, 2), False, (2 * n + 3, 2), False, (n, 1), False, (n, 0), True),
        }[k]

    T = bigger.Triangulation.from_pos(edges, link)

    def generator(name: str) -> bigger.Encoding[Edge]:
        curve, test = extract_curve_and_test("a", name)

        if curve == "a":
            isom = lambda edge: (edge[0], [1, 0, 2, 3][edge[1]]) if test(edge[0]) else edge
            return T.encode([(-1, isom, isom), lambda side: side.edge[1] == 0 and side.orientation and test(side.edge[0])])

        raise ValueError("Unknown mapping class {}".format(name))

    return bigger.MCG(T, generator)


def cantor() -> bigger.MCG[Edge]:  # pylint: disable=too-many-statements
    """A sphere minus a cantor set.

    With mapping classes:

     - a_n which twists about the curve about the nth hole
     - b_n which twists about the curve about the nth hole
     - r an order two rotation
    """

    POS, EQ, NEG = +1, 0, -1

    def invert(sign: int, X: Link) -> Link:
        return X if sign == POS else (X[1], X[0], X[3], X[2])

    def link(edge: Edge) -> tuple[Edge, bool, Edge, bool, Edge, bool, Edge, bool]:
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

    T = bigger.Triangulation(lambda: ((x, y) for x in naturals() for y in [+1, 0, -1]), link)

    def generator(name: str) -> bigger.Encoding[Edge]:  # pylint: disable=too-many-branches
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
