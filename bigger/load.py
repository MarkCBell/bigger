
import re

import bigger

def flute() -> 'bigger.MCG':
    
    #  ---#---------#---------#---------#---
    #     |    2   /|    5   /|    8   /|
    #     |      /  |      /  |      /  |
    # ... |0  1/    |3  4/    |6  7/    | ...
    #     |  /      |  /      |  /      |
    #     |/   ~2   |/  ~5    |/  ~8    |
    #  ---#-------->#---------#---------#---
    
    def adjacent(oedge: 'bigger.OrientedEdge') -> 'bigger.OrientedEdge':
        p = oedge.label + (-2 if oedge.label % 3 == 2 else +1)
        return bigger.OrientedEdge(p, oedge.orientation)
    T = bigger.Triangulation(adjacent)
    
    def shift_isom(oedge: 'bigger.OrientedEdge') -> 'bigger.OrientedEdge':
        return bigger.OrientedEdge(oedge.label + 3, oedge.orientation)
    
    def shift_inv_isom(oedge: 'bigger.OrientedEdge') -> 'bigger.OrientedEdge':
        return bigger.OrientedEdge(oedge.label - 3, oedge.orientation)
    shift = T.encode_isometry(shift_isom, shift_inv_isom)
    
    twist_re = re.compile(r'(?P<curve>[aAbB])(?P<number>\d+)$')
    
    def generator(name: str) -> 'bigger.Encoding':
        twist_match = twist_re.match(name)
        if name in ('s', 'shift'):
            return shift
        elif name in ('S', 'SHIFT'):
            return ~shift
        elif twist_match is not None:
            parameters = twist_match.groupdict()
            n = int(parameters['number'])
            if parameters['curve'] == 'a':
                return T({3*n+1: 1, 3*n+2: 1}).encode_twist()
            if parameters['curve'] == 'A':
                return T({3*n+1: 1, 3*n+2: 1}).encode_twist()**-1
            if parameters['curve'] == 'b':
                return T({3*n-2: 1, 3*n-1: 1, 3*n+0: 2, 3*n+1: 2, 3*n+3: 2, 3*n+4: 1, 3*n+5: 1}).encode_twist()
            if parameters['curve'] == 'B':
                return T({3*n-2: 1, 3*n-1: 1, 3*n+0: 2, 3*n+1: 2, 3*n+3: 2, 3*n+4: 1, 3*n+5: 1}).encode_twist()**-1
        
        raise ValueError('Unknown mapping class {}'.format(name))
    
    return bigger.MCG(T, generator)

