
import re

import bigger

def flute() -> 'bigger.MCG':
    
    #  ---#----2----#----5----#----8----#---
    #     |        /|        /|        /|
    #     |      /  |      /  |      /  |
    # ... 0    1    3    4    6    7    9 ...
    #     |  /      |  /      |  /      |
    #     |/        |/        |/        |
    #  ---#----2--->#----5----#----8----#---
    
    def neighbours(edge: 'bigger.Edge') -> 'bigger.Square':
        if edge % 3 == 0:
            return (edge-2, edge-1, edge+1, edge+2)
        elif edge % 3 == 1:
            return (edge+1, edge-1, edge+1, edge+2)
        else:  # edge % 3 == 2:
            return (edge+1, edge-1, edge-2, edge-1)
    T = bigger.Triangulation(neighbours)
    
    def shift_isom(edge: 'bigger.Edge') -> 'bigger.Edge':
        return edge + 3
    
    def shift_inv_isom(edge: 'bigger.Edge') -> 'bigger.Edge':
        return edge - 3
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

