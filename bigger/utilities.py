
from fractions import Fraction
from typing import Union, overload

class Half:
    ''' A class for representing 1/2 in such a way that multiplication preserves types. '''
    @overload
    def __mul__(self, other: Fraction) -> Fraction:
        ...
    @overload  # noqa: F811  # Can be removed once flake8 updates https://github.com/PyCQA/pyflakes/pull/435#issuecomment-570738527
    def __mul__(self, other: int) -> int:
        ...
    
    def __mul__(self, other: Union[Fraction, int]) -> Union[Fraction, int]:  # noqa: F811  # Can be removed once flake8 updates https://github.com/PyCQA/pyflakes/pull/435#issuecomment-570738527
        if isinstance(other, int):
            result = other // 2
        else:
            result = other / 2
        if 2*result != other:  # Sanity check.
            raise ValueError('{} is not halvable in its field'.format(other))
        return result
    def __str__(self) -> str:
        return '1/2'
    def __repr__(self) -> str:
        return str(self)
    def __rmul__(self, other: int) -> int:
        return self * other
    def __call__(self, other: int) -> int:
        return self * other

half = Half()

