""" A module for representing triangulations along with laminations and mapping classes on them. """

from typing import Callable, Generic, TypeVar, Iterable

import bigger  # pylint: disable=unused-import

Edge = TypeVar("Edge")


def splitter(strn: str) -> Iterable[str]:
    """ Break strn into words on .'s except when they are inside braces. """
    word = []
    brackets = 0
    for letter in strn:
        word.append(letter)
        if letter == "." and brackets == 0:
            yield "".join(word)
            word = []
        elif letter == "{":
            brackets += 1
        elif letter == "}":
            brackets -= 1
    yield "".join(word)


class MappingClassGroup(Generic[Edge]):  # pylint: disable=too-few-public-methods
    """ A :class:`~bigger.triangulation.Triangulation` together with a function which produces mapping classes from names. """

    def __init__(self, triangulation: "bigger.Triangulation[Edge]", generator: Callable[[str], "bigger.Encoding[Edge]"]) -> None:
        self.triangulation = triangulation
        self.generator = generator

    def _helper(self, name: str) -> "bigger.Encoding[Edge]":
        try:
            return self.generator(name)
        except ValueError:
            return ~(self.generator(name.swapcase()))

    def __call__(self, strn: str) -> "bigger.Encoding[Edge]":
        sequence = [item for name in splitter(strn) for item in self._helper(name).sequence]
        return bigger.Encoding(sequence) if sequence else self.triangulation.encode_identity()
