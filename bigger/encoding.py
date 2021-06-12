""" A module for representing and manipulating maps between Triangulations. """

from __future__ import annotations
from typing import Callable, Generic, Iterator, List, Union, overload

import bigger
from bigger.types import Edge


class Move(Generic[Edge]):
    """A function that takes :class:`Laminations <bigger.lamination.Lamination>` on one :class:`~bigger.triangulation.Triangulation` to another."""

    def __init__(
        self,
        source: bigger.Triangulation[Edge],
        target: bigger.Triangulation[Edge],
        action: Callable[[bigger.Lamination[Edge]], bigger.Lamination[Edge]],
        inv_action: Callable[[bigger.Lamination[Edge]], bigger.Lamination[Edge]],
    ) -> None:
        self.source = source
        self.target = target
        self.action = action
        self.inv_action = inv_action

    def __invert__(self) -> bigger.Move[Edge]:
        return Move(self.target, self.source, self.inv_action, self.action)

    def __call__(self, lamination: bigger.Lamination[Edge]) -> bigger.Lamination[Edge]:
        if lamination.is_finitely_supported() and not lamination:  # Optimisation for empty laminations.
            return self.target.empty_lamination()

        return self.action(lamination)

    def encode(self) -> bigger.Encoding[Edge]:
        """Return the :class:`~bigger.encoding.Encoding` consisting of only this Move."""
        return bigger.Encoding([self])


class Encoding(Generic[Edge]):
    """A sequence of :class:`Moves <bigger.encoding.Move>` to apply to a :class:`~bigger.lamination.Lamination`."""

    def __init__(self, sequence: List[bigger.Move[Edge]]) -> None:
        self.sequence = sequence
        self.source = self.sequence[-1].source
        self.target = self.sequence[0].target

    def __iter__(self) -> Iterator[bigger.Move[Edge]]:
        # Iterate through self.sequence in application order (i.e. reverse).
        return iter(reversed(self.sequence))

    def __mul__(self, other: bigger.Encoding[Edge]) -> bigger.Encoding[Edge]:
        return Encoding(self.sequence + other.sequence)

    def __invert__(self) -> bigger.Encoding[Edge]:
        return Encoding([~move for move in self])

    def __len__(self) -> int:
        return len(self.sequence)

    @overload
    def __getitem__(self, index: slice) -> bigger.Encoding[Edge]:
        ...

    @overload
    def __getitem__(self, index: int) -> bigger.Move[Edge]:
        ...

    def __getitem__(self, index: Union[slice, int]) -> Union[bigger.Encoding[Edge], bigger.Move[Edge]]:
        if isinstance(index, slice):
            start = 0 if index.start is None else index.start % len(self)
            stop = len(self) if index.stop is None else index.stop % len(self)
            if start == stop:
                if 0 <= start < len(self):
                    return self.sequence[start].target.identity()
                elif start == len(self):
                    return self.source.identity()
                else:
                    raise IndexError("list index out of range")
            elif stop < start:
                raise IndexError("list index out of range")
            else:  # start < stop.
                return Encoding(self.sequence[index])
        else:
            return self.sequence[index]

    def __call__(self, lamination: bigger.Lamination[Edge]) -> bigger.Lamination[Edge]:
        if lamination.is_finitely_supported() and not lamination:  # Optimisation for empty laminations.
            return self.target.empty_lamination()

        for move in self:
            lamination = move(lamination)

        return lamination

    def __pow__(self, power: int) -> bigger.Encoding[Edge]:
        if power == 0:
            return self.source.identity()

        abs_power = Encoding(self.sequence * abs(power))
        return abs_power if power > 0 else ~abs_power

    def conjugate_by(self, other: Encoding[Edge]) -> Encoding[Edge]:
        """Return this Encoding conjugated by other."""

        return ~other * self * other
