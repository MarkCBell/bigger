
from typing import Union, Callable, TypeVar, Tuple
from fractions import Fraction

import bigger  # noqa: F401  # pylint: disable=unused-import

Rational = Union[Fraction, int]

Edge = int

Weight = Callable[['bigger.Edge'], int]
Isom = Callable[['bigger.Edge'], 'bigger.Edge']
Square = Tuple['bigger.Edge', 'bigger.Edge', 'bigger.Edge', 'bigger.Edge']
Neighbours = Callable[['bigger.Edge'], Square]

TypedLamination = TypeVar('TypedLamination', 'bigger.Lamination', 'bigger.FinitelySupportedLamination')
Action = Callable[[TypedLamination], TypedLamination]

