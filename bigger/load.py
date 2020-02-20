
''' Functions for building example mapping class groups. '''

from typing import Tuple

import re

import bigger

def flute() -> 'bigger.MCG':
    ''' The infinitely punctured sphere, with punctures that accumulate in one direction.
    
    With mapping classes:
    
     - an which twists about the curve parallel to edges n and n+1
     - bn which twists about the curve which separates punctures n and n+1
     - a which twists about all an curves simultaneously
    '''
    
    #             #----2----#----5----#----8----#---
    #            /|        /|        /|        /|
    #         -1  |      /  |      /  |      /  |
    #        #    0    1    3    4    6    7    9 ...
    #         -1  |  /      |  /      |  /      |
    #            \|/        |/        |/        |
    #             #----2----#----5----#----8----#---
    
    T = bigger.Triangulation(
        lambda edge:
        (0, -1, -1, 0) if edge == -1 else
        (-1, -1, 1, 2) if edge == 0 else
        [(edge-2, edge-1, edge+1, edge+2), (edge+1, edge-1, edge+1, edge+2), (edge+1, edge-1, edge-2, edge-1)][edge % 3]
        )
    
    twist_re = re.compile(r'(?P<curve>[aAbB])(?P<number>\d+)$')
    
    def generator(name: str) -> 'bigger.Encoding':
        twist_match = twist_re.match(name)
        if name == 'a':
            isom = lambda edge: -1 if edge == -1 else edge + [0, +1, -1][edge % 3]
            return T.encode([(isom, isom), lambda edge: edge % 3 == 1])
        elif twist_match is not None:
            parameters = twist_match.groupdict()
            n = int(parameters['number'])
            if parameters['curve'] == 'a':
                return T({3*n+1: 1, 3*n+2: 1}).encode_twist()
            if parameters['curve'] == 'b':
                return T({3*n-2: 1, 3*n-1: 1, 3*n+0: 2, 3*n+1: 2, 3*n+3: 2, 3*n+4: 1, 3*n+5: 1}).encode_twist()
        
        raise ValueError('Unknown mapping class {}'.format(name))
    
    return bigger.MCG(T, generator)

def biflute() -> 'bigger.MCG':
    ''' The infinitely punctured sphere, with punctures that accumulate in two directions.
    
    With mapping classes:
    
     - an which twists about the curve parallel to edges n and n+1
     - bn which twists about the curve which separates punctures n and n+1
     - a which twists about all an curves simultaneously
     - s which shifts the surface down
    '''
    
    #  ---#----2----#----5----#----8----#---
    #     |        /|        /|        /|
    #     |      /  |      /  |      /  |
    # ... 0    1    3    4    6    7    9 ...
    #     |  /      |  /      |  /      |
    #     |/        |/        |/        |
    #  ---#----2----#----5----#----8----#---
    
    T = bigger.Triangulation(lambda edge: [(edge-2, edge-1, edge+1, edge+2), (edge+1, edge-1, edge+1, edge+2), (edge+1, edge-1, edge-2, edge-1)][edge % 3])
    
    shift = T.encode_isometry(lambda edge: edge+3, lambda edge: edge-3)
    
    twist_re = re.compile(r'(?P<curve>[aAbB])(?P<number>-?\d+)$')
    
    def generator(name: str) -> 'bigger.Encoding':
        twist_match = twist_re.match(name)
        if name in ('s', 'shift'):
            return shift
        elif name == 'a':
            isom = lambda edge: edge + [0, +1, -1][edge % 3]
            return T.encode([(isom, isom), lambda edge: edge % 3 == 1])
        elif twist_match is not None:
            parameters = twist_match.groupdict()
            n = int(parameters['number'])
            if parameters['curve'] == 'a':
                return T({3*n+1: 1, 3*n+2: 1}).encode_twist()
            if parameters['curve'] == 'b':
                return T({3*n-2: 1, 3*n-1: 1, 3*n+0: 2, 3*n+1: 2, 3*n+3: 2, 3*n+4: 1, 3*n+5: 1}).encode_twist()
        
        raise ValueError('Unknown mapping class {}'.format(name))
    
    return bigger.MCG(T, generator)

def ladder() -> 'bigger.MCG':
    ''' The infinite-genus, two-ended surface.
    
    With mapping classes:
    
     - an which twists about the curve parallel to edges n and n+1
     - bn which twists about the curve which separates punctures n and n+1
     - a which twists about all an curves simultaneously
     - b which twists about all bn curves simultaneously
     - s which shifts the surface down
    '''
    
    #  #---n,0---#---n,8---#
    #  |        /|        /|
    #  |      /  |      /  |
    # n,1  n,2  n,4  n,7  n+1,0
    #  |  /      |  /      |
    #  |/        |/        |
    #  #---n,3---#---n,8---#
    #  |        /|
    #  |      /  |
    # n,5  n,6  n,5
    #  |  /      |
    #  |/        |
    #  #--n+1,1--#
    
    Edge = Tuple[int, int]
    
    def link(edge: Edge) -> Tuple[Edge, Edge, Edge, Edge]:
        n, k = edge
        return {
            0: ((n, 1), (n, 2), (n-1, 7), (n-1, 8)),
            1: ((n-1, 5), (n-1, 6), (n, 2), (n, 0)),
            2: ((n, 0), (n, 1), (n, 3), (n, 4)),
            3: ((n, 4), (n, 2), (n, 5), (n, 6)),
            4: ((n, 2), (n, 3), (n, 7), (n, 8)),
            5: ((n, 6), (n, 3), (n, 6), (n+1, 1)),
            6: ((n, 3), (n, 5), (n+1, 1), (n, 5)),
            7: ((n, 8), (n, 4), (n, 8), (n+1, 0)),
            8: ((n+1, 0), (n, 7), (n, 4), (n, 7))
        }[k]
    T = bigger.Triangulation(link)
    
    shift = T.encode_isometry(lambda edge: (edge[0]+1, edge[1]), lambda edge: (edge[0]-1, edge[1]))
    
    twist_re = re.compile(r'(?P<curve>[aAbB])(?P<number>-?\d+)$')
    
    def generator(name: str) -> 'bigger.Encoding':
        twist_match = twist_re.match(name)
        if name in ('s', 'shift'):
            return shift
        elif name == 'a':
            isom = lambda edge: (edge[0], [0, 1, 2, 3, 4, 5, 6, 8, 7][edge[1]])
            return T.encode([(isom, isom), lambda edge: edge[1] == 7])
        elif name == 'b':
            isom = lambda edge: (edge[0], [0, 1, 2, 3, 4, 6, 5, 7, 8][edge[1]])
            return T.encode([(isom, isom), lambda edge: edge[1] == 6])
        elif twist_match is not None:
            parameters = twist_match.groupdict()
            n = int(parameters['number'])
            if parameters['curve'] == 'a':
                return T({(n, 7): 1, (n, 8): 1}).encode_twist()
            if parameters['curve'] == 'b':
                return T({(n, 5): 1, (n, 6): 1}).encode_twist()
        
        raise ValueError('Unknown mapping class {}'.format(name))
    
    return bigger.MCG(T, generator)

