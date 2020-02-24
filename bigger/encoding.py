""" A module for representing and manipulating maps between Triangulations. """

from typing import List, Iterator, Union, TypeVar, Callable, Generic, overload

import bigger

Edge = TypeVar("Edge")


class Move(Generic[Edge]):
    """ A function that takes :class:`Laminations <bigger.lamination.Lamination>` on one :class:`~bigger.triangulation.Triangulation` to another. """

    def __init__(
        self,
        source: "bigger.Triangulation[Edge]",
        target: "bigger.Triangulation[Edge]",
        action: Callable[["bigger.Lamination[Edge]"], "bigger.Lamination[Edge]"],
        inv_action: Callable[["bigger.Lamination[Edge]"], "bigger.Lamination[Edge]"],
    ) -> None:
        self.source = source
        self.target = target
        self.action = action
        self.inv_action = inv_action

    def __invert__(self) -> "bigger.Move[Edge]":
        return Move(self.target, self.source, self.inv_action, self.action)

    def __call__(self, lamination: "bigger.Lamination[Edge]") -> "bigger.Lamination[Edge]":
        return self.action(lamination)

    def encode(self) -> "bigger.Encoding[Edge]":
        """ Return the :class:`~bigger.encoding.Encoding` consisting of only this Move. """
        return bigger.Encoding([self])


class Encoding(Generic[Edge]):
    """ A sequence of :class:`Moves <bigger.encoding.Move>` to apply to a :class:`~bigger.lamination.Lamination`. """

    def __init__(self, sequence: List["bigger.Move[Edge]"]) -> None:
        self.sequence = sequence
        self.source = self.sequence[-1].source
        self.target = self.sequence[0].target

    def __iter__(self) -> Iterator["bigger.Move[Edge]"]:
        # Iterate through self.sequence in application order (i.e. reverse).
        return iter(reversed(self.sequence))

    def __mul__(self, other: "bigger.Encoding[Edge]") -> "bigger.Encoding[Edge]":
        return Encoding(self.sequence + other.sequence)

    def __invert__(self) -> "bigger.Encoding[Edge]":
        return Encoding([~move for move in self])

    @overload
    def __getitem__(self, index: slice) -> "bigger.Encoding[Edge]":
        ...

    @overload
    def __getitem__(self, index: int) -> "bigger.Move[Edge]":  # noqa: F811
        ...

    def __getitem__(self, index: Union[int, slice]) -> Union["bigger.Move[Edge]", "bigger.Encoding[Edge]"]:  # noqa: F811
        if isinstance(index, slice):
            return Encoding(self.sequence[index])
        else:
            return self.sequence[index]

    def __call__(self, lamination: "bigger.Lamination[Edge]") -> "bigger.Lamination[Edge]":  # noqa: F811
        for move in self:
            lamination = move(lamination)

        return lamination

    def __pow__(self, power: int) -> "bigger.Encoding[Edge]":
        if power == 0:
            return self.source.encode_identity()

        abs_power = Encoding(self.sequence * abs(power))
        return abs_power if power > 0 else ~abs_power
