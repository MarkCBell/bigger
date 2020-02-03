
from typing import Any, Set, Iterable, Tuple

import bigger

class Lamination:
    def __init__(self, triangulation: 'bigger.Triangulation', weight: 'bigger.Weight') -> None:
        self.triangulation = triangulation
        self.weight = weight
    def __call__(self, edge: 'bigger.Edge') -> int:
        return self.weight(edge)
    def __str__(self) -> str:
        return self.show([bigger.Edge(label) for label in range(10)]) + ' ...'
    def __repr__(self) -> str:
        return str(self)
    def show(self, edges: Iterable['bigger.Edge']) -> str:
        return ', '.join('{}: {}'.format(edge, self(edge)) for edge in edges)

class FinitelySupportedLamination(Lamination):
    def __init__(self, triangulation: 'bigger.Triangulation', weight: 'bigger.Weight', support: Set['bigger.Edge']) -> None:
        super().__init__(triangulation, weight)
        self.support = support
    def __eq__(self, other: Any) -> bool:
        if isinstance(other, FinitelySupportedLamination):
            return self.support == other.support and all(self(edge) == other(edge) for edge in self.support)
        elif isinstance(other, dict):
            return self.support == set(other) and all(self(edge) == other[edge] for edge in self.support)
        
        return NotImplemented
    def __str__(self) -> str:
        return self.show(self.support)
    def __repr__(self) -> str:
        return str(self)
    def complexity(self) -> int:
        return sum(self(edge) for edge in self.support)
    def shorten(self) -> Tuple['bigger.FinitelySupportedLamination', bigger.Encoding]:
        ''' Return an encoding that minimises self.complexity. '''
        
        lamination = self
        complexity = lamination.complexity()
        conjugator = lamination.triangulation.encode_identity()
        time_since_last_progress = 0
        while not lamination.is_short():
            time_since_last_progress += 1
            best_complexity, best_h = complexity, lamination.triangulation.encode_identity()
            for edge in lamination.support:
                h = lamination.triangulation.encode_flip({edge})
                image: FinitelySupportedLamination = h(lamination)
                new_complexity = image.complexity()
                if new_complexity <= best_complexity:
                    best_complexity, best_h = new_complexity, h
            
            if best_complexity < complexity: time_since_last_progress = 0
            conjugator = best_h * conjugator
            lamination = h(lamination)
            complexity = best_complexity
            
            if time_since_last_progress > 3:
                raise ValueError('{} is not a non-isolating curve'.format(lamination))
        
        return lamination, conjugator
    
    def is_short(self) -> bool:
        return self.complexity() == 2  # or all(self(edge) == 2 for edge in self.support)
    
    def encode_twist(self) -> 'bigger.Encoding':
        # Currently only works on non-isolating curves.
        short, conjugator = self.shorten()
        
        # Use the following for reference:
        # #<--------#     #<--------#
        # |    a   ^^     |\   a    ^
        # |------/--|     |  \      |
        # |b  e/   d| --> |b   \e' d|
        # |  /      |     |      \  |
        # v/   c    |     v    c   V|
        # #-------->#     #-------->#
        
        # #<--------#     #<--------#
        # |    a|  ^^     |\   a    ^
        # |     |/  |     |  \      |
        # |b  e/|  d| --> |b   \e' d|
        # |  /  |   |     |      \  |
        # v/   c|   |     v    c   V|
        # #-------->#     #-------->#
        
        e, _ = short.support
        a, b, c, d = short.triangulation.neighbours(e)
        if short(b) == 1:
            assert b == d
            twist = short.triangulation.encode([{e: b, b: e}, {e}])
        else:  # short(a) == 1:
            assert a == c
            twist = short.triangulation.encode([{e: a, a: e}, {e}])
        
        return ~conjugator * twist * conjugator

