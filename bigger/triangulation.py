
from typing import Union, Dict, Optional, Set, List, overload

import bigger

class Triangulation:
    def __init__(self, neigbours: 'bigger.Neighbours') -> None:
        # Use the following for reference:
        # #----a----#
        # |        /|
        # |      /  |
        # b    e    d
        # |  /      |
        # |/        |
        # #----c----#
        #
        # neighbours(e) = (a, b, c, d, e)
        
        self.neighbours = neigbours
    def encode_flip(self, edge: 'bigger.Edge') -> 'bigger.Encoding':
        
        # Use the following for reference:
        # #----a----#     #----a----#
        # |        /|     |\        |
        # |      /  |     |  \      |
        # b    e    d --> b    e    d
        # |  /      |     |      \  |
        # |/        |     |        \|
        # #----c----#     #----c----#
        
        e = edge  # Shorter name.
        a, b, c, d = self.neighbours(e)
        aa, ab, ac, ad = self.neighbours(a)
        ba, bb, bc, bd = self.neighbours(b)
        ca, cb, cc, cd = self.neighbours(c)
        da, db, dc, dd = self.neighbours(d)
        # Rotate to ensure e is in a known position
        if ad != e: aa, ab, ac, ad = ac, ad, aa, ab
        if bc != e: ba, bb, bc, bd = bc, bd, ba, bb
        if cd != e: ca, cb, cc, cd = cc, cd, ca, cb
        if dc != e: da, db, dc, dd = dc, dd, da, db
        assert ad == e and bc == e and cd == e and dc == e
        pairs = {
            a: (aa, ab, e, d),
            b: (ba, bb, c, e),
            c: (ca, cb, e, b),
            d: (da, db, a, e),
            e: (d, a, b, c),
            }
        
        def neighbours(edgy: 'bigger.Edge') -> 'bigger.Square':
            return pairs.get(edgy, self.neighbours(edgy))
        
        target = Triangulation(neighbours)
        
        def action(lamination: 'bigger.TypedLamination') -> 'bigger.TypedLamination':
            def weight(edgy: 'bigger.Edge') -> int:
                if edgy != edge:
                    return lamination(edgy)
                
                # Compute fi.
                ei = lamination(edge)
                ai0, bi0, ci0, di0 = [max(lamination(edgy), 0) for edgy in self.neighbours(edge)]
                
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
                ai0, bi0, ci0, di0 = [max(lamination(edgy), 0) for edgy in target.neighbours(edge)]
                
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
        def neighbours(edge: 'bigger.Edge') -> 'bigger.Square':
            a, b, c, d = self.neighbours(inv_isom(edge))
            return (isom(a), isom(b), isom(c), isom(d))
        
        return Triangulation(neighbours)
    def encode_isometry(self, isom: 'bigger.Isom', inv_isom: 'bigger.Isom') -> 'bigger.Encoding':
        target = self.relabel(isom, inv_isom)
        
        def action(lamination: 'bigger.TypedLamination') -> 'bigger.TypedLamination':
            def weight(edge: 'bigger.Edge') -> int:
                return lamination(inv_isom(edge))
            support = {isom(arc) for arc in lamination.support} if isinstance(lamination, bigger.FinitelySupportedLamination) else None
            return target(weight, support)
        
        def inv_action(lamination: 'bigger.TypedLamination') -> 'bigger.TypedLamination':
            def weight(edge: 'bigger.Edge') -> int:
                return lamination(isom(edge))
            support = {isom(arc) for arc in lamination.support} if isinstance(lamination, bigger.FinitelySupportedLamination) else None
            return self(weight, support)
        
        return bigger.Move(self, target, action, inv_action).encode()
    def encode_isometry_from_dict(self, isom_dict: Dict['bigger.Edge', 'bigger.Edge']) -> 'bigger.Encoding':
        inv_isom_dict = dict((value, key) for key, value in isom_dict.items())
        
        def isom(edge: 'bigger.Edge') -> 'bigger.Edge':
            return isom_dict.get(edge, edge)
        
        def inv_isom(edge: 'bigger.Edge') -> 'bigger.Edge':
            return inv_isom_dict.get(edge, edge)
        
        return self.encode_isometry(isom, inv_isom)
    
    def encode_identity(self) -> 'bigger.Encoding':
        return self.encode_isometry_from_dict(dict())
    
    @overload
    def __call__(self, weights: Dict['bigger.Edge', int], support: None = None) -> 'bigger.FinitelySupportedLamination':
        ...
    @overload  # noqa: F811  # Can be removed once flake8 updates https://github.com/PyCQA/pyflakes/pull/435#issuecomment-570738527
    def __call__(self, weights: 'bigger.Weight', support: Set['bigger.Edge']) -> 'bigger.FinitelySupportedLamination':
        ...
    @overload  # noqa: F811  # Can be removed once flake8 updates https://github.com/PyCQA/pyflakes/pull/435#issuecomment-570738527
    def __call__(self, weights: 'bigger.Weight', support: None) -> 'bigger.Lamination':
        ...
    
    def __call__(self, weights: Union[Dict['bigger.Edge', int], 'bigger.Weight'], support: Optional[Set['bigger.Edge']] = None) -> Union['bigger.Lamination', 'bigger.FinitelySupportedLamination']:  # noqa: F811  # Can be removed once flake8 updates https://github.com/PyCQA/pyflakes/pull/435#issuecomment-570738527
        if isinstance(weights, dict):
            weight_dict = dict((key, value) for key, value in weights.items())
            
            def weight(edge: 'bigger.Edge') -> int:
                return weight_dict.get(edge, 0)
            
            return bigger.FinitelySupportedLamination(self, weight, set(weight_dict))
        elif support is not None:
            return bigger.FinitelySupportedLamination(self, weights, support)
        else:
            return bigger.Lamination(self, weights)
    
    def encode(self, sequence: List[Union['bigger.Move', 'bigger.Edge', Dict['bigger.Edge', 'bigger.Edge']]]) -> 'bigger.Encoding':
        h = self.encode_identity()
        for term in reversed(sequence):
            if isinstance(term, bigger.Move):
                move = term.encode()
            elif isinstance(term, int):
                move = h.target.encode_flip(term)
            elif isinstance(term, dict):
                move = h.target.encode_isometry_from_dict(term)
            h = move * h
        
        return h

