
''' A module for representing and manipulating maps between Triangulations. '''

from typing import List, Iterator, Union, TypeVar, Callable, overload

import bigger

TypedLamination = TypeVar('TypedLamination', 'bigger.Lamination', 'bigger.FinitelySupportedLamination')
Action = Callable[[TypedLamination], TypedLamination]

class Move:
    ''' A function that takes :class:`Laminations <bigger.lamination.Lamination>` on one :class:`~bigger.triangulation.Triangulation` to another. '''
    def __init__(self, source: 'bigger.Triangulation', target: 'bigger.Triangulation', action: Action, inv_action: Action) -> None:
        self.source = source
        self.target = target
        self.action = action
        self.inv_action = inv_action
    def __invert__(self) -> 'bigger.Move':
        return Move(self.target, self.source, self.inv_action, self.action)
    def __call__(self, lamination: TypedLamination) -> TypedLamination:
        return self.action(lamination)
    def encode(self) -> 'bigger.Encoding':
        ''' Return the :class:`~bigger.encoding.Encoding` consisting of only this Move. '''
        return bigger.Encoding([self])

class Encoding:
    ''' A sequence of :class:`Moves <bigger.encoding.Move>` to apply to a :class:`~bigger.lamination.Lamination`. '''
    def __init__(self, sequence: List['bigger.Move']) -> None:
        self.sequence = sequence
        self.source = self.sequence[-1].source
        self.target = self.sequence[0].target
    def __iter__(self) -> Iterator['bigger.Move']:
        # Iterate through self.sequence in application order (i.e. reverse).
        return iter(reversed(self.sequence))
    def __mul__(self, other: 'bigger.Encoding') -> 'bigger.Encoding':
        return Encoding(self.sequence + other.sequence)
    def __invert__(self) -> 'bigger.Encoding':
        return Encoding([~move for move in self])
    def __getitem__(self, index: int) -> 'bigger.Move':
        if isinstance(index, slice):
            return Encoding(self.sequence[index])
        else:
            return self.sequence[index]
    @overload
    def __call__(self, lamination: 'bigger.FinitelySupportedLamination') -> 'bigger.FinitelySupportedLamination':
        ...
    @overload
    def __call__(self, lamination: 'bigger.Lamination') -> 'bigger.Lamination':  # noqa: F811
        ...
    def __call__(self, lamination: Union['bigger.Lamination', 'bigger.FinitelySupportedLamination']) -> Union['bigger.Lamination', 'bigger.FinitelySupportedLamination']:  # noqa: F811
        for move in self:
            lamination = move(lamination)
        return lamination
    def __pow__(self, power: int) -> 'bigger.Encoding':
        if power == 0:
            return self.source.encode_identity()
        abs_power = Encoding(self.sequence * abs(power))
        return abs_power if power > 0 else ~abs_power

