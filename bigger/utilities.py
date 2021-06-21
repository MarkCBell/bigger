""" A module of useful, generic functions. """

from __future__ import annotations

from fractions import Fraction
from itertools import tee
from typing import Iterable, TypeVar

IntFraction = TypeVar("IntFraction", int, Fraction)
T = TypeVar("T")


class Half:
    """A class for representing 1/2 in such a way that multiplication preserves types."""

    def __mul__(self, other: IntFraction) -> IntFraction:
        if isinstance(other, int):
            int_result = other // 2
            assert 2 * int_result == other, "{} is not halvable in its field".format(other)
            return int_result
        else:  # isinstance(other, Fraction):
            frac_result = other / 2
            assert 2 * frac_result == other, "{} is not halvable in its field".format(other)
            return frac_result

    def __str__(self) -> str:
        return "1/2"

    def __repr__(self) -> str:
        return str(self)

    def __rmul__(self, other: IntFraction) -> IntFraction:
        return self * other

    def __call__(self, other: IntFraction) -> IntFraction:
        return self * other


half = Half()


def maximin(*iterables: Iterable[int]) -> int:
    """Return the maximum of the minimum, terminating early.

    This is equivalent to: max(min(iterable) for iterable in iterables)"""

    iter_iterables = iter(iterables)
    try:
        result = min(next(iter_iterables))  # Get the first one through a full evaluation.
    except StopIteration:
        raise ValueError("max() arg is an empty sequence") from None

    for iterable in iter_iterables:
        iterable = iter(iterable)
        try:
            best = next(iterable)
        except StopIteration:
            raise ValueError("min() arg is an empty sequence") from None

        if best <= result:
            continue

        for item in iterable:
            if item <= result:
                break
            if item < best:
                best = item
        else:  # We never broke out, so best > result
            result = best

    return result


def lookahead(iterable: Iterable[T], n: int) -> Iterable[tuple[T, T]]:
    """Yield items of iterable together with the item n steps in the future."""

    current, future = tee(iterable)
    try:
        for _ in range(n):  # Fast forward.
            next(future)
    except StopIteration:
        return

    yield from zip(current, future)
