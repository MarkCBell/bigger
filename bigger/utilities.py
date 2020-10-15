""" A module of useful, generic functions. """

from fractions import Fraction
from typing import Union, overload


class Half:
    """ A class for representing 1/2 in such a way that multiplication preserves types. """

    @overload
    def __mul__(self, other: Fraction) -> Fraction:
        ...

    @overload
    def __mul__(self, other: int) -> int:
        ...

    def __mul__(self, other: Union[Fraction, int]) -> Union[Fraction, int]:
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

    def __rmul__(self, other: int) -> int:
        return self * other

    def __call__(self, other: int) -> int:
        return self * other


half = Half()
