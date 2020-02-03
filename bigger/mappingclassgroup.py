
from typing import Callable

import bigger  # pylint: disable=unused-import

class MappingClassGroup:  # pylint: disable=too-few-public-methods
    def __init__(self, triangulation: 'bigger.Triangulation', generator: Callable[[str], 'bigger.Encoding']) -> None:
        self.triangulation = triangulation
        self.generator = generator
    def __call__(self, strn: str) -> 'bigger.Encoding':
        sequence = [item for name in strn.split('.') for item in self.generator(name).sequence]
        return bigger.Encoding(self.triangulation, self.triangulation, sequence) if sequence else self.triangulation.encode_identity()
    def lamination(self, weight):
        return self.triangulation(weight)

