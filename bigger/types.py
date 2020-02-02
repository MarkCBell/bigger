
from typing import Union, Callable
from fractions import Fraction

import bigger  # noqa: F401  # pylint: disable=unused-import

Weight = Callable[['bigger.Edge'], int]
Isom = Callable[['bigger.OrientedEdge'], 'bigger.OrientedEdge']
Adjacency = Callable[['bigger.OrientedEdge'], 'bigger.OrientedEdge']

Rational = Union[Fraction, int]

Oedger = Union['bigger.OrientedEdge', int]
Edger = Union['bigger.Edge', int]

