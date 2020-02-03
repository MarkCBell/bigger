
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
    def encode_flip(self, edges: Set['bigger.Edge']) -> 'bigger.Encoding':
        
        def flipped(edgy: 'bigger.Edge') -> bool:
            return edgy in edges
        
        # Use the following for reference:
        # #----a----#     #----a----#
        # |        /|     |\        |
        # |      /  |     |  \      |
        # b    e    d --> b    e    d
        # |  /      |     |      \  |
        # |/        |     |        \|
        # #----c----#     #----c----#
        
        def neighbours(edgy: 'bigger.Edge') -> 'bigger.Square':
            a, b, c, d = self.neighbours(edgy)
            if flipped(edgy):
                return (b, c, d, a)
            if flipped(a):
                aa, ab, ac, ad = self.neighbours(a)
                if ad != edgy: aa, ab, ac, ad = ac, ad, aa, ab
                w, x = aa, a
            elif flipped(b):
                ba, bb, bc, bd = self.neighbours(b)
                if bc != edgy: ba, bb, bc, bd = bc, bd, ba, bb
                w, x = b, bb
            else:
                w, x = a, b
            
            if flipped(c):
                ca, cb, cc, cd = self.neighbours(c)
                if cd != edgy: ca, cb, cc, cd = cc, cd, ca, cb
                y, z = ca, c
            elif flipped(d):
                da, db, dc, dd = self.neighbours(d)
                if dc != edgy: da, db, dc, dd = dc, dd, da, db
                y, z = d, db
            else:
                y, z = c, d
            
            return (w, x, y, z)
        
        target = Triangulation(neighbours)
        
        def action(lamination: 'bigger.TypedLamination') -> 'bigger.TypedLamination':
            def weight(edgy: 'bigger.Edge') -> int:
                if not flipped(edgy):
                    return lamination(edgy)
                
                # Compute fi.
                ei = lamination(edgy)
                ai0, bi0, ci0, di0 = [max(lamination(edgy), 0) for edgy in self.neighbours(edgy)]
                
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
            support = set(edge for support in lamination.support for edge in (target.neighbours(support) + (support,)) if weight(edge)) if isinstance(lamination, bigger.FinitelySupportedLamination) else None
            return target(weight, support)
        
        def inv_action(lamination: 'bigger.TypedLamination') -> 'bigger.TypedLamination':
            def weight(edgy: 'bigger.Edge') -> int:
                if not flipped(edgy):
                    return lamination(edgy)
                
                # Compute fi.
                ei = lamination(edgy)
                ai0, bi0, ci0, di0 = [max(lamination(edgy), 0) for edgy in target.neighbours(edgy)]
                
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
            support = set(edge for support in lamination.support for edge in (self.neighbours(support) + (support,)) if weight(edge)) if isinstance(lamination, bigger.FinitelySupportedLamination) else None
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
            support = {inv_isom(arc) for arc in lamination.support} if isinstance(lamination, bigger.FinitelySupportedLamination) else None
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
    @overload
    def __call__(self, weights: 'bigger.Weight', support: Set['bigger.Edge']) -> 'bigger.FinitelySupportedLamination':  # noqa: F811
        ...
    @overload
    def __call__(self, weights: 'bigger.Weight', support: None) -> 'bigger.Lamination':  # noqa: F811
        ...
    
    def __call__(self, weights: Union[Dict['bigger.Edge', int], 'bigger.Weight'], support: Optional[Set['bigger.Edge']] = None) -> Union['bigger.Lamination', 'bigger.FinitelySupportedLamination']:  # noqa: F811
        if isinstance(weights, dict):
            weight_dict = dict((key, value) for key, value in weights.items() if value)
            
            def weight(edge: 'bigger.Edge') -> int:
                return weight_dict.get(edge, 0)
            
            return bigger.FinitelySupportedLamination(self, weight, set(weight_dict))
        elif support is not None:
            return bigger.FinitelySupportedLamination(self, weights, support)
        else:
            return bigger.Lamination(self, weights)
    
    def encode(self, sequence: List[Union['bigger.Edge', Set['bigger.Edge'], Dict['bigger.Edge', 'bigger.Edge']]]) -> 'bigger.Encoding':
        h = self.encode_identity()
        for term in reversed(sequence):
            if isinstance(term, int):
                move = h.target.encode_flip({term})
            elif isinstance(term, set):
                move = h.target.encode_flip(term)
            elif isinstance(term, dict):
                move = h.target.encode_isometry_from_dict(term)
            h = move * h
        
        return h

