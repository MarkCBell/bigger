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
     - a{expr(n)} which twists about all a_n curves when expr(n) is True

    Shortcuts:

     - a[start:stop:step] = a{n in range(start, stop, step)}
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
            return T(lambda edge: 1 if edge[1] in {0, 1} and test(edge[0]) else 0).twist()

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

    def edges() -> Iterable[Edge]:
        for x in naturals():
            for y in [POS, EQ, NEG]:
                yield x, y

    def negate(X: Edge) -> Edge:
        return X[0], -X[1]

    def invert(sign: int, X: tuple[Edge, bool, Edge, bool, Edge, bool, Edge, bool]) -> tuple[Edge, bool, Edge, bool, Edge, bool, Edge, bool]:
        return X if sign == POS else (negate(X[6]), not X[7], negate(X[4]), not X[5], negate(X[2]), not X[3], negate(X[0]), not X[1])

    def link(edge: Edge) -> tuple[Edge, bool, Edge, bool, Edge, bool, Edge, bool]:
        n, k = edge
        if k == EQ:  # Equator
            if n == 0:
                return ((0, NEG), False, (1, NEG), True, (1, POS), False, (0, POS), True)
            elif n == 1:
                return ((2, POS), False, (0, POS), False, (0, NEG), True, (2, NEG), True)
            else:  # n > 1
                return ((3 * n - 3, NEG), False, (3 * n - 1, NEG), True, (3 * n - 1, POS), False, (3 * n - 3, POS), True)

        # Northern / Southern hemisphere.
        if n == 0:
            return invert(k, ((0, EQ), False, (1, POS), False, (1, EQ), True, (2, POS), False))
        elif n == 1:
            return invert(k, ((4, POS), False, (3, POS), False, (0, POS), True, (0, EQ), False))
        elif n == 2:
            return invert(k, ((7, POS), False, (6, POS), False, (0, POS), False, (1, EQ), True))
        N, r = n // 3 + 1, n % 3
        incoming = 3 * (N // 2) - (1 if N % 2 else 2)
        if r == 0:
            return invert(k, ((N, EQ), False, (n + 2, POS), False, (incoming, POS), True, (n + 1, POS), False))
        elif r == 1:
            return invert(k, ((6 * N - 2, POS), False, (6 * N - 3, POS), False, (n - 1, POS), False, (incoming, POS), True))
        else:  # r == 2:
            return invert(k, ((6 * N + 1, POS), False, (6 * N + 0, POS), False, (n - 2, POS), True, (N, EQ), False))

    T = bigger.Triangulation.from_pos(edges, link)

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

            return T.encode([(-1, isom, isom)])

        raise ValueError("Unknown mapping class {}".format(name))

    return bigger.MCG(T, generator)
