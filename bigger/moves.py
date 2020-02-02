
from typing import Union, overload
import bigger

class Move:
    def __init__(self, source: 'bigger.Triangulation', target: 'bigger.Triangulation') -> None:
        self.source = source
        self.target = target
    def __invert__(self) -> 'bigger.Move':
        pass
    def __call__(self, lamination: Union['bigger.Lamination', 'bigger.FinitelySupportedLamination']) -> Union['bigger.Lamination', 'bigger.FinitelySupportedLamination']:
        pass
    def encode(self) -> 'bigger.Encoding':
        return bigger.Encoding(self.source, self.target, [self])

class EdgeFlip(Move):
    def __init__(self, source: 'bigger.Triangulation', target: 'bigger.Triangulation', edge: 'bigger.Edge') -> None:
        super().__init__(source, target)
        self.edge = edge
    def __invert__(self) -> 'bigger.EdgeFlip':
        return EdgeFlip(self.target, self.source, self.edge)
    
    @overload  # noqa: F811
    def __call__(self, lamination: 'bigger.FinitelySupportedLamination') -> 'bigger.FinitelySupportedLamination':
        ...
    @overload  # noqa: F811
    def __call__(self, lamination: 'bigger.Lamination') -> 'bigger.Lamination':
        ...
    def __call__(self, lamination: Union['bigger.Lamination', 'bigger.FinitelySupportedLamination']) -> Union['bigger.Lamination', 'bigger.FinitelySupportedLamination']:  # noqa: F811
        def weight(edge: 'bigger.Edge') -> int:
            if edge != self.edge:
                return lamination(edge)
            
            # Compute fi.
            ei = lamination(self.edge)
            ai0, bi0, ci0, di0, _ = [max(lamination(edge), 0) for edge in self.source.square(self.edge.orient())]
            
            if ei >= ai0 + bi0 and ai0 >= di0 and bi0 >= ci0:  # CASE: A(ab)
                return ai0 + bi0 - ei
            elif ei >= ci0 + di0 and di0 >= ai0 and ci0 >= bi0:  # CASE: A(cd)
                return ci0 + di0 - ei
            elif ei <= 0 and ai0 >= bi0 and di0 >= ci0:  # CASE: D(ad)
                return ai0 + di0 - ei
            elif ei <= 0 and bi0 >= ai0 and ci0 >= di0:  # CASE: D(bc)
                return bi0 + ci0 - ei
            elif ei >= 0 and ai0 >= bi0 + ei and di0 >= ci0 + ei:  # CASE: N(ad)
                return ai0 + di0 - 2*ei
            elif ei >= 0 and bi0 >= ai0 + ei and ci0 >= di0 + ei:  # CASE: N(bc)
                return bi0 + ci0 - 2*ei
            elif ai0 + bi0 >= ei and bi0 + ei >= 2*ci0 + ai0 and ai0 + ei >= 2*di0 + bi0:  # CASE: N(ab)
                return bigger.half(ai0 + bi0 - ei)
            elif ci0 + di0 >= ei and di0 + ei >= 2*ai0 + ci0 and ci0 + ei >= 2*bi0 + di0:  # CASE: N(cd)
                return bigger.half(ci0 + di0 - ei)
            else:
                return max(ai0 + ci0, bi0 + di0) - ei
        # Determine support.
        support = lamination.support.difference([self.edge]).union([self.edge] if weight(self.edge) else []) if isinstance(lamination, bigger.FinitelySupportedLamination) else None
        return self.target(weight, support)

class Isometry(Move):
    def __init__(self, source: 'bigger.Triangulation', target: 'bigger.Triangulation', isom: 'bigger.Isom', inv_isom: 'bigger.Isom') -> None:
        super().__init__(source, target)
        self.isom = isom
        self.inv_isom = inv_isom
    def __invert__(self) -> 'bigger.Isometry':
        return Isometry(self.target, self.source, self.inv_isom, self.isom)
    @overload  # noqa: F811
    def __call__(self, lamination: 'bigger.FinitelySupportedLamination') -> 'bigger.FinitelySupportedLamination':
        ...
    @overload  # noqa: F811
    def __call__(self, lamination: 'bigger.Lamination') -> 'bigger.Lamination':
        ...
    def __call__(self, lamination: Union['bigger.Lamination', 'bigger.FinitelySupportedLamination']) -> Union['bigger.Lamination', 'bigger.FinitelySupportedLamination']:  # noqa: F811
        def weight(edge: 'bigger.Edge') -> int:
            return lamination(self.inv_isom(edge.orient()))
        support = {self.isom(arc.orient()).unorient() for arc in lamination.support} if isinstance(lamination, bigger.FinitelySupportedLamination) else None
        return self.target(weight, support)

