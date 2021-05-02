""" Example flute surfaces. """

from __future__ import annotations

import bigger
from bigger.types import FlatTriangle
from bigger.triangulation import Triangle
from .utils import integers, extract_curve_and_test

Edge = int


def flute() -> bigger.MCG[Edge]:
    """The infinitely punctured sphere, with punctures that accumulate in one direction.

    With mapping classes:

     - a_n which twists about the curve parallel to edges n and n+1
     - b_n which twists about the curve which separates punctures n and n+1
     - a{expr(n)} which twists about all a_n curves when expr(n) is True
     - b{expr(n)} which twists about all b_n curves when expr(n) is True

    Shortcuts:

     - a[start:stop:step] = a{n in range(start, stop, step)}
     - a == a[:]
    """

    #             #----2----#----5----#----8----#---
    #            /|        /|        /|        /|
    #         -1  |      /  |      /  |      /  |
    #        #    0    1    3    4    6    7    9 ...
    #         -1  |  /      |  /      |  /      |
    #            \|/        |/        |/        |
    #             #----2----#----5----#----8----#---

    T = bigger.Triangulation.from_pos(
        lambda: integers(-1),
        lambda edge: (0, True, -1, False, -1, True, 0, True)
        if edge == -1
        else (-1, False, -1, True, 1, True, 2, False)
        if edge == 0
        else [
            (edge - 2, False, edge - 1, True, edge + 1, True, edge + 2, False),
            (edge + 1, False, edge - 1, False, edge + 1, True, edge + 2, True),
            (edge + 1, True, edge - 1, False, edge - 2, False, edge - 1, True),
        ][edge % 3],
    )

    def generator(name: str) -> bigger.Encoding[Edge]:
        curve, test = extract_curve_and_test("ab", name)

        if curve == "a":
            a = T(lambda n: 1 if n >= 0 and n % 3 != 0 and test(n // 3) else 0)
            return a.twist()
        if curve == "b":

            def build(k: Edge) -> bigger.Encoding[Edge]:
                # Build the encoding which twists around b[n] when test(n) and n % 3 == k.

                def retest(n: Edge) -> bool:
                    if n % 3 != k:
                        return False

                    if test(n):
                        if test(n - 1):
                            raise ValueError("Cannot twist along b[{}] and b[{}] simultaneously".format(n - 1, n))

                        if test(n + 1):
                            raise ValueError("Cannot twist along b[{}] and b[{}] simultaneously".format(n, n + 1))

                        return True

                    return False

                def b_isom(side: bigger.Side[Edge]) -> bigger.Side[Edge]:
                    n, r = divmod(side.edge, 3)
                    modifier = +3 if r == 0 and retest(n) else -3 if r == 0 and retest(n - 1) else +6 if r == 1 and retest(n + 1) else -6 if r == 1 and retest(n - 1) else 0

                    return bigger.Side(side.edge + modifier, side.orientation)

                prefix = T.encode(
                    [
                        lambda side: side.edge % 3 == 2 and side.orientation and (retest(side.edge // 3 - 1) or retest(side.edge // 3 + 1)),
                        lambda side: side.edge % 3 == 1 and side.orientation and retest(side.edge // 3),
                        lambda side: side.edge % 3 == 0 and side.orientation and (retest(side.edge // 3) or retest(side.edge // 3 - 1)),
                    ]
                )
                twist = prefix.target.encode(
                    [
                        (b_isom, b_isom),
                        lambda side: side.edge % 3 == 1 and side.orientation and (retest(side.edge // 3 - 1) or retest(side.edge // 3 + 1)),
                        lambda side: side.edge % 3 == 0 and side.orientation and (retest(side.edge // 3) or retest(side.edge // 3 - 1)),
                    ]
                )
                return ~prefix * twist * prefix

            return build(0) * build(1) * build(2)

        raise ValueError("Unknown mapping class {}".format(name))

    def layout(triangle: Triangle[Edge]) -> FlatTriangle:
        if triangle[0].edge == -1:
            return (0.0, 1.0), (-1.0, 0.5), (0.0, 0.0)
        elif triangle[0].edge % 3 == 0:
            n = triangle[0].edge // 3
            return (n, 1.0), (n, 0.0), (n + 1.0, 1.0)
        else:  # triangle[0] % 3 == 1:
            n = triangle[0].edge // 3
            return (n + 1.0, 1.0), (n, 0.0), (n + 1.0, 0.0)

    return bigger.MCG(T, generator, layout)


def biflute() -> bigger.MCG[Edge]:
    """The infinitely punctured sphere, with punctures that accumulate in two directions.

    With mapping classes:

     - a_n which twists about the curve parallel to edges n and n+1
     - b_n which twists about the curve which separates punctures n and n+1
     - a{expr(n)} which twists about all a_n curves when expr(n) is True
     - b{expr(n)} which twists about all b_n curves when expr(n) is True
     - s which shifts the surface down
     - r which rotates the surface fixing the curve a_0

    Shortcuts:

     - a[start:stop:step] = a{n in range(start, stop, step)}
     - a == a[:]

    Note: Since b_n and b_{n+1} intersect, any b expression cannot be true for consecutive values.
    """

    #  ---#----2----#----5----#----8----#---
    #     |        /|        /|        /|
    #     |      /  |      /  |      /  |
    # ... 0    1    3    4    6    7    9 ...
    #     |  /      |  /      |  /      |
    #     |/        |/        |/        |
    #  ---#----2----#----5----#----8----#---

    T = bigger.Triangulation.from_pos(
        integers,
        lambda edge: [
            (edge - 2, False, edge - 1, True, edge + 1, True, edge + 2, False),
            (edge + 1, False, edge - 1, False, edge + 1, True, edge + 2, True),
            (edge + 1, True, edge - 1, False, edge - 2, False, edge - 1, True),
        ][edge % 3],
    )

    shift = T.isometry(T, lambda edge: edge + 3, lambda edge: edge - 3)
    rotate = T.isometry(
        T,
        lambda edge: [3, 2, 4][edge % 3] - edge,
        lambda edge: [3, 2, 4][edge % 3] - edge,
    )

    def generator(name: str) -> bigger.Encoding[Edge]:
        if name in ("s", "shift"):
            return shift

        if name in ("r", "rotate"):
            return rotate

        curve, test = extract_curve_and_test("ab", name)

        if curve == "a":
            return T(lambda n: 1 if n % 3 != 0 and test(n // 3) else 0).twist()
        if curve == "b":
            def weight(n: Edge) -> int:
                n, r = divmod(n, 3)
                if r == 0:
                    return 2 if test(n) or test(n - 1) else 0
                if r == 1:
                    if test(n) or (test(n - 1) and test(n + 1)): return 2
                    return 1 if test(n - 1) or test(n + 1) else 0
                if r == 2:
                    if test(n): return 0
                    if test(n - 1) and test(n + 1): return 2
                    return 1 if test(n - 1) or test(n + 1) else 0

            return T(weight).twist()

        raise ValueError("Unknown mapping class {}".format(name))

    def layout(triangle: Triangle[Edge]) -> FlatTriangle:
        n, k = divmod(triangle[0].edge, 3)
        if k == 0:
            return (n, 1.0), (n, 0.0), (n + 1.0, 1.0)
        else:  # k == 1.
            return (n + 1.0, 1.0), (n, 0.0), (n + 1.0, 0.0)

    return bigger.MCG(T, generator, layout)
