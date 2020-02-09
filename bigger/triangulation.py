
''' A module for representing a triangulation of a punctured surface. '''

from functools import partial
from typing import Callable, Union, Tuple, Dict, Optional, Set, List, overload

import bigger

class Triangulation:
    ''' A triangulation of a (possibly infinite type) surface.
    
    The triangulation is specified via a function which takes an edge to its link.
    Note that this cannot be used to define S_{1,1} since its edge links are invariant under the hyperelliptic involution. '''
    def __init__(self, link: 'bigger.Link') -> None:
        # Use the following for reference:
        # #----a----#
        # |        /|
        # |      /  |
        # b    e    d
        # |  /      |
        # |/        |
        # #----c----#
        #
        # link(e) = (a, b, c, d, e)
        
        self.link = link
    
    def star(self, edge: 'bigger.Edge') -> 'bigger.Neighbourhood':
        ''' Return the link of an Edge together with the Edge itself. '''
        
        return self.link(edge) + (edge,)
    def encode_flip(self, is_flipped: Union[Callable[['bigger.Edge'], bool], Set['bigger.Edge']]) -> 'bigger.Encoding':
        ''' Return an :class:`~bigger.encoding.Encoding` consisting of a single :class:`~bigger.encoding.Move` which flips all edges where :attr:`is_flipped` is True.
        
        Alternatively, this can be given a set of Edges and will use membership of this set to test which edges flip.
        Note that if :attr:`is_flipped` is True for an Edge then it must be False for all edge in its link. '''
        
        if isinstance(is_flipped, set):
            flipped = lambda edge: edge in is_flipped
        else:
            flipped = is_flipped
        
        # Use the following for reference:
        # #----a----#     #----a----#
        # |        /|     |\        |
        # |      /  |     |  \      |
        # b    e    d --> b    e    d
        # |  /      |     |      \  |
        # |/        |     |        \|
        # #----c----#     #----c----#
        
        # Define the new triangulation.
        
        def link(edge: 'bigger.Edge') -> 'bigger.Square':
            a, b, c, d = self.link(edge)
            if flipped(edge):
                return (b, c, d, a)
            if flipped(a):
                aa, ab, ac, ad = self.link(a)
                if ad != edge: aa, ab, ac, ad = ac, ad, aa, ab
                w, x = aa, a
            elif flipped(b):
                ba, bb, bc, bd = self.link(b)
                if bc != edge: ba, bb, bc, bd = bc, bd, ba, bb
                w, x = b, bb
            else:
                w, x = a, b
            
            if flipped(c):
                ca, cb, cc, cd = self.link(c)
                if cd != edge: ca, cb, cc, cd = cc, cd, ca, cb
                y, z = ca, c
            elif flipped(d):
                da, db, dc, dd = self.link(d)
                if dc != edge: da, db, dc, dd = dc, dd, da, db
                y, z = d, db
            else:
                y, z = c, d
            
            return (w, x, y, z)
        
        target = Triangulation(link)
        
        # Since the action and inv_action are so similar, we define both at once and just use a partial function to set the correct source / target.
        def helper(source: 'bigger.Triangulation', target: 'bigger.Triangulation', lamination: 'bigger.TypedLamination') -> 'bigger.TypedLamination':
            def weight(edge: 'bigger.Edge') -> int:
                if not flipped(edge):
                    return lamination(edge)
                
                # Compute fi.
                ei = lamination(edge)
                ai0, bi0, ci0, di0 = [max(lamination(edge), 0) for edge in source.link(edge)]
                
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
            support = set(edge for support in lamination.support for edge in target.star(support) if weight(edge)) if isinstance(lamination, bigger.FinitelySupportedLamination) else None
            return target(weight, support)
        
        action = partial(helper, self, target)
        inv_action = partial(helper, target, self)
        
        return bigger.Move(self, target, action, inv_action).encode()
    
    def encode_isometry(self, isom: 'bigger.Isom', inv_isom: 'bigger.Isom') -> 'bigger.Encoding':
        ''' Return an :class:`~bigger.encoding.Encoding` which maps edges under the specified relabelling. '''
        
        # Define the new triangulation.
        
        def link(edge: 'bigger.Edge') -> 'bigger.Square':
            a, b, c, d = self.link(inv_isom(edge))
            return (isom(a), isom(b), isom(c), isom(d))
        
        target = Triangulation(link)
        
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
        ''' Return an :class:`~bigger.encoding.Encoding` which relabels Edges in :attr:`isom_dict` an leaves all other edges unchanged. '''
        inv_isom_dict = dict((value, key) for key, value in isom_dict.items())
        
        def isom(edge: 'bigger.Edge') -> 'bigger.Edge':
            return isom_dict.get(edge, edge)
        
        def inv_isom(edge: 'bigger.Edge') -> 'bigger.Edge':
            return inv_isom_dict.get(edge, edge)
        
        return self.encode_isometry(isom, inv_isom)
    
    def encode_identity(self) -> 'bigger.Encoding':
        ''' Return an :class:`~bigger.encoding.Encoding` which represents the identity mapping class. '''
        return self.encode_isometry_from_dict(dict())
    
    def encode(self, sequence: List[Union[Tuple['bigger.Isom', 'bigger.Isom'], Callable[['bigger.Edge'], bool], 'bigger.Edge', Set['bigger.Edge'], Dict['bigger.Edge', 'bigger.Edge']]]) -> 'bigger.Encoding':
        ''' Return an :class:`~bigger.encoding.Encoding` from a small sequence of data.
        
        There are several conventions that allow these to be specified by a smaller amount of information:
        
         - A set or callable is used to flip those edges.
         - A dict or pair of callables is used to encode an isomety.
         - Otherwise, it is assumed to be the label of an edge to flip.
        
        The sequence is read in reverse in order to respect composition. '''
        h = self.encode_identity()
        for term in reversed(sequence):
            if isinstance(term, set) or callable(term):
                move = h.target.encode_flip(term)
            elif isinstance(term, dict):
                move = h.target.encode_isometry_from_dict(term)
            elif isinstance(term, tuple) and len(term) == 2 and all(callable(item) for item in term):
                move = h.target.encode_isometry(*term)
            else:  # Assume term is the label of an edge to flip.
                move = h.target.encode_flip({term})
            h = move * h
        
        return h
    
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

