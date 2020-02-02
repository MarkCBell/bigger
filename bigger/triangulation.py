
from typing import Any, Tuple, Union, Dict, Optional, Set, List, overload

import bigger

class OrientedEdge:
    def __init__(self, label: int, orientation: int) -> None:
        self.label = label
        self.orientation = orientation
    def __repr__(self) -> str:
        return 'OrientedEdge({}, {})'.format(self.label, self.orientation)
    def __hash__(self) -> int:
        return hash((self.label, self.orientation))
    def __eq__(self, other: Any) -> bool:
        return self.label == other.label and self.orientation == other.orientation
    def __invert__(self) -> 'bigger.OrientedEdge':
        return OrientedEdge(self.label, -self.orientation)
    def unorient(self) -> 'bigger.Edge':
        return Edge(self.label)

class Edge:  # pylint: disable=too-few-public-methods
    def __init__(self, label: int) -> None:
        self.label = label
    def __repr__(self) -> str:
        return 'Edge({})'.format(self.label)
    def __hash__(self) -> int:
        return hash(self.label)
    def __eq__(self, other: Any) -> bool:
        return self.label == other.label
    def orient(self, orientation: int = +1) -> 'bigger.OrientedEdge':
        return OrientedEdge(self.label, orientation)

def oedger(data: 'bigger.Oedger') -> OrientedEdge:
    return data if isinstance(data, OrientedEdge) else OrientedEdge(data, +1)
def edger(data: 'bigger.Edger') -> Edge:
    return data if isinstance(data, Edge) else Edge(data)

class Triangulation:
    def __init__(self, adjacent: 'bigger.Adjacency') -> None:
        self.adjacent = adjacent
    def left(self, oedge: 'bigger.OrientedEdge') -> 'bigger.OrientedEdge':
        oedge = oedger(oedge)
        return self.adjacent(oedge)
    def right(self, oedge: 'bigger.OrientedEdge') -> 'bigger.OrientedEdge':
        oedge = oedger(oedge)
        return self.adjacent(self.adjacent(oedge))
    def square(self, oedge: 'bigger.OrientedEdge') -> Tuple['bigger.OrientedEdge', ...]:
        oedge = oedger(oedge)
        return (self.left(oedge), self.right(oedge), self.left(~oedge), self.right(~oedge), oedge)
    def encode_flip(self, oedge: 'bigger.Oedger') -> 'bigger.Encoding':
        
        # Use the following for reference:
        # #<--------#     #---------#
        # |    a   ^^     |\   a    |
        # |      /  |     |  \      |
        # |b  e/   d| --> |b   \e' d|
        # |  /      |     |      \  |
        # V/   c    |     |    c   V|
        # #-------->#     #---------#
        
        oedge = oedger(oedge)
        a, b, c, d, e = self.square(oedge)
        pairs = {a: e, e: d, d: a, c: ~e, ~e: b, b: c}
        
        def adjacent(oedgy: 'bigger.OrientedEdge') -> 'bigger.OrientedEdge':
            return pairs[oedgy] if oedgy in pairs else self.adjacent(oedgy)
        
        target = Triangulation(adjacent)
        edge = oedge.unorient()
        
        def action(lamination: 'bigger.TypedLamination') -> 'bigger.TypedLamination':
            def weight(edgy: 'bigger.Edge') -> int:
                if edgy != edge:
                    return lamination(edgy)
                
                # Compute fi.
                ei = lamination(edge)
                ai0, bi0, ci0, di0, _ = [max(lamination(edgy), 0) for edgy in self.square(edge.orient())]
                
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
            support = lamination.support.difference([edge]).union([edge] if weight(edge) else []) if isinstance(lamination, bigger.FinitelySupportedLamination) else None
            return target(weight, support)
        
        def inv_action(lamination: 'bigger.TypedLamination') -> 'bigger.TypedLamination':
            def weight(edgy: 'bigger.Edge') -> int:
                if edgy != edge:
                    return lamination(edgy)
                
                # Compute fi.
                ei = lamination(edge)
                ai0, bi0, ci0, di0, _ = [max(lamination(edgy), 0) for edgy in target.square(edge.orient())]
                
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
            support = lamination.support.difference([edge]).union([edge] if weight(edge) else []) if isinstance(lamination, bigger.FinitelySupportedLamination) else None
            return self(weight, support)
        
        return bigger.Move(self, target, action, inv_action).encode()
    
    def relabel(self, isom: 'bigger.Isom', inv_isom: 'bigger.Isom') -> 'bigger.Triangulation':
        def adjacent(oedge: 'bigger.OrientedEdge') -> 'bigger.OrientedEdge':
            return isom(self.adjacent(inv_isom(oedge)))
        
        return Triangulation(adjacent)
    def encode_isometry(self, isom: 'bigger.Isom', inv_isom: 'bigger.Isom') -> 'bigger.Encoding':
        target = self.relabel(isom, inv_isom)
        
        def action(lamination: 'bigger.TypedLamination') -> 'bigger.TypedLamination':
            def weight(edge: 'bigger.Edge') -> int:
                return lamination(inv_isom(edge.orient()))
            support = {isom(arc.orient()).unorient() for arc in lamination.support} if isinstance(lamination, bigger.FinitelySupportedLamination) else None
            return target(weight, support)
        
        def inv_action(lamination: 'bigger.TypedLamination') -> 'bigger.TypedLamination':
            def weight(edge: 'bigger.Edge') -> int:
                return lamination(isom(edge.orient()))
            support = {isom(arc.orient()).unorient() for arc in lamination.support} if isinstance(lamination, bigger.FinitelySupportedLamination) else None
            return self(weight, support)
        
        return bigger.Move(self, target, action, inv_action).encode()
    def encode_isometry_from_dict(self, isom_dict: Dict['bigger.OrientedEdge', 'bigger.OrientedEdge']) -> 'bigger.Encoding':
        inv_isom_dict = dict((value, key) for key, value in isom_dict.items())
        
        def isom(oedge: 'bigger.OrientedEdge') -> 'bigger.OrientedEdge':
            return isom_dict.get(oedge, oedge)
        
        def inv_isom(oedge: 'bigger.OrientedEdge') -> 'bigger.OrientedEdge':
            return inv_isom_dict.get(oedge, oedge)
        
        return self.encode_isometry(isom, inv_isom)
    
    def encode_identity(self) -> 'bigger.Encoding':
        return self.encode_isometry_from_dict(dict())
    
    @overload
    def __call__(self, weights: Dict['bigger.Edger', int], support: None = None) -> 'bigger.FinitelySupportedLamination':
        ...
    @overload  # noqa: F811  # Can be removed once flake8 updates https://github.com/PyCQA/pyflakes/pull/435#issuecomment-570738527
    def __call__(self, weights: 'bigger.Weight', support: Set['bigger.Edge']) -> 'bigger.FinitelySupportedLamination':
        ...
    @overload  # noqa: F811  # Can be removed once flake8 updates https://github.com/PyCQA/pyflakes/pull/435#issuecomment-570738527
    def __call__(self, weights: 'bigger.Weight', support: None) -> 'bigger.Lamination':
        ...
    
    def __call__(self, weights: Union[Dict['bigger.Edger', int], 'bigger.Weight'], support: Optional[Set['bigger.Edge']] = None) -> Union['bigger.Lamination', 'bigger.FinitelySupportedLamination']:  # noqa: F811  # Can be removed once flake8 updates https://github.com/PyCQA/pyflakes/pull/435#issuecomment-570738527
        if isinstance(weights, dict):
            weight_dict = dict((edger(key), value) for key, value in weights.items())
            
            def weight(edge: 'bigger.Edge') -> int:
                return weight_dict.get(edge, 0)
            
            return bigger.FinitelySupportedLamination(self, weight, set(weight_dict))
        elif support is not None:
            return bigger.FinitelySupportedLamination(self, weights, support)
        else:
            return bigger.Lamination(self, weights)
    
    def encode(self, sequence: List[Union['bigger.Move', 'bigger.OrientedEdge', Dict['bigger.OrientedEdge', 'bigger.OrientedEdge']]]) -> 'bigger.Encoding':
        h = self.encode_identity()
        for term in reversed(sequence):
            if isinstance(term, bigger.Move):
                move = term.encode()
            elif isinstance(term, OrientedEdge):
                move = h.target.encode_flip(term)
            elif isinstance(term, dict):
                move = h.target.encode_isometry_from_dict(term)
            h = move * h
        
        return h

