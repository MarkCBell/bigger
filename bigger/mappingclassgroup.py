
''' A module for representing triangulations along with laminations and mapping classes on them. '''

from typing import Callable

import bigger  # pylint: disable=unused-import

class MappingClassGroup:  # pylint: disable=too-few-public-methods
    ''' A :class:`~bigger.triangulation.Triangulation` together with a function which produces mapping classes from names. '''
    def __init__(self, triangulation: 'bigger.Triangulation', generator: Callable[[str], 'bigger.Encoding']) -> None:
        self.triangulation = triangulation
        self.generator = generator
    def __call__(self, strn: str) -> 'bigger.Encoding':
        sequence = [item for name in strn.split('.') for item in self.generator(name).sequence]
        return bigger.Encoding(sequence) if sequence else self.triangulation.encode_identity()

