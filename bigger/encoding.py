
from typing import List, Iterator, Union, overload

import bigger  # pylint: disable=unused-import

class Encoding:
    def __init__(self, source: 'bigger.Triangulation', target: 'bigger.Triangulation', sequence: List['bigger.Move']) -> None:
        self.source = source
        self.target = target
        self.sequence = sequence
    def __iter__(self) -> Iterator['bigger.Move']:
        # Iterate through self.sequence in application order (i.e. reverse).
        return iter(reversed(self.sequence))
    def __mul__(self, other: 'bigger.Encoding') -> 'bigger.Encoding':
        return Encoding(self.target, other.source, self.sequence + other.sequence)
    def __invert__(self) -> 'bigger.Encoding':
        return Encoding(self.target, self.source, [~move for move in self.sequence])
    @overload  # noqa: F811
    def __call__(self, lamination: 'bigger.FinitelySupportedLamination') -> 'bigger.FinitelySupportedLamination':
        ...
    @overload  # noqa: F811
    def __call__(self, lamination: 'bigger.Lamination') -> 'bigger.Lamination':
        ...
    def __call__(self, lamination: Union['bigger.Lamination', 'bigger.FinitelySupportedLamination']) -> Union['bigger.Lamination', 'bigger.FinitelySupportedLamination']:  # noqa: F811
        for move in self:
            lamination = move(lamination)
        return lamination
    def __pow__(self, power: int) -> 'bigger.Encoding':
        if power == 0:
            return self.source.encode_identity()
        abs_power = Encoding(self.source, self.target, self.sequence * abs(power))
        return abs_power if power > 0 else ~abs_power

