
from typing import Callable

import bigger  # pylint: disable=unused-import

class MappingClassGroup:  # pylint: disable=too-few-public-methods
    def __init__(self, triangulation: 'bigger.Triangulation', generator: Callable[[str], 'bigger.Encoding']) -> None:
        self.triangulation = triangulation
        self.generator = generator
    def __call__(self, strn: str) -> 'bigger.Encoding':
        h = self.triangulation.encode_identity()
        for name in strn.split('.'):
            h = h * self.generator(name)
        
        return h

