""" A module for representing triangulations along with laminations and mapping classes on them. """

from __future__ import annotations

from typing import Any, Callable, Generic, Iterable, List, Optional
from PIL import Image  # type: ignore

import bigger
from .types import Edge, Triangle, FlatTriangle


def splitter(strn: str) -> Iterable[str]:
    """ Break strn into words on .'s except when they are inside braces. """

    start = 0
    brackets = 0
    for index, letter in enumerate(strn):
        if letter == "." and brackets == 0:
            yield strn[start:index]
            start = index + 1
        elif letter == "{":
            brackets += 1
        elif letter == "}":
            brackets -= 1

        if brackets < 0:
            raise ValueError("Mismatched braces")

    if brackets:
        raise ValueError("Mismatched braces")

    yield strn[start:]


def swapcase(strn: str) -> str:
    """ Swapcase of strn, except for items that are inside braces. """

    output = []
    brackets = 0
    for letter in strn:
        output.append(letter if brackets else letter.swapcase())
        if letter == "{":
            brackets += 1
        elif letter == "}":
            brackets -= 1

        if brackets < 0:
            raise ValueError("Mismatched braces")

    if brackets:
        raise ValueError("Mismatched braces")

    return "".join(output)


class MappingClassGroup(Generic[Edge]):
    """ A :class:`~bigger.triangulation.Triangulation` together with a function which produces mapping classes from names. """

    def __init__(
        self, triangulation: bigger.Triangulation[Edge], generator: Callable[[str], bigger.Encoding[Edge]], layout: Optional[Callable[[Triangle], FlatTriangle]] = None
    ) -> None:
        self.triangulation = triangulation
        self.generator = generator
        self.layout = layout

    def _helper(self, name: str) -> bigger.Encoding[Edge]:
        try:
            return self.generator(name)
        except ValueError:
            return ~(self.generator(swapcase(name)))

    def __call__(self, strn: str) -> bigger.Encoding[Edge]:
        sequence = [item for name in splitter(strn) for item in self._helper(name).sequence]
        return bigger.Encoding(sequence) if sequence else self.triangulation.identity()

    def draw(self, edges: List[Edge], **options: Any) -> Image:
        """ Return a PIL image of the triangulation of this MCG around the given edges. """

        return bigger.draw(self, edges=edges, **options)
