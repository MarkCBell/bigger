
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
    
    T = bigger.Triangulation(lambda edge: [(edge-2, edge-1, edge+1, edge+2), (edge+1, edge-1, edge+1, edge+2), (edge+1, edge-1, edge-2, edge-1)][edge % 3])
    
    shift = T.encode_isometry(lambda edge: edge+3, lambda edge: edge-3)
    
    twist_re = re.compile(r'(?P<curve>[aAbB])(?P<number>-?\d+)$')
    
    def generator(name: str) -> 'bigger.Encoding':
        twist_match = twist_re.match(name)
        if name in ('s', 'shift'):
            return shift
        elif name in ('S', 'SHIFT'):
            return ~generator('shift')
        elif name == 't':
            isom = lambda edge: edge + [0, +1, -1][edge % 3]
            return T.encode([(isom, isom), lambda edge: edge % 3 == 1])
        elif name == 'T':
            return ~generator('t')
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

def tree3() -> 'bigger.MCG':
    pass
