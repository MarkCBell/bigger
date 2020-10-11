
from unittest import TestCase
import bigger
from itertools import islice

class TestFlute(TestCase):
    S = bigger.load.flute()
    T = S.triangulation
    L = T.as_lamination()
    edges = list(islice(T, 10))
    a = T({edges[0]: -1})
    b = T({edges[2]: -1})
    m = T(dict((e, -i) for i, e in enumerate(edges)))
    
    def test_str(self):
        self.assertEqual(str(self.L), 'Infinitely supported lamination 0: -1, -1: -1, 1: -1, -2: -1, 2: -1, -3: -1, 3: -1, -4: -1, 4: -1, -5: -1 ...')
        self.assertEqual(str(self.a), 'Lamination 0: -1')
        self.assertEqual(repr(self.L), str(self.L))
    
    def test_twist(self):
        self.assertEqual(self.S('b_1')(self.L).describe(range(10)), '0: -1, 1: 8, 2: 7, 3: 16, 4: 11, 5: -1, 6: 16, 7: 8, 8: 7, 9: -1')
        self.assertEqual(self.S('a')(self.L).describe(range(10)), '0: -1, 1: 1, 2: -1, 3: -1, 4: 1, 5: -1, 6: -1, 7: 1, 8: -1, 9: -1')
        self.assertEqual(self.S('a_4.a.B_2')(self.L).describe(range(10)), '0: -1, 1: 1, 2: -1, 3: -1, 4: 7, 5: 6, 6: 14, 7: 39, 8: 19, 9: 14')
    
    def test_flip(self):
        self.assertEqual(self.S('a_0')(self.T({1: 4, 2: 2, 3: 4})), {1: 6, 2: 4, 3: 4})
        self.assertEqual(self.S('a_0')(self.T({0: 4, 1: 4, 2: 2})), {0: 4, 1: 6, 2: 4})
        self.assertEqual(self.T.encode([1])(self.a), {0: -1})
    
    def test_slice(self):
        h = self.S('a.a.b_1.a_3')
        self.assertEqual((h[:5] * h[5:])(self.m), h(self.m))

class TestBiflute(TestCase):
    S = bigger.load.biflute()
    T = S.triangulation
    L = T.as_lamination()
    edges = list(islice(T, 10))
    a = T({edges[0]: -1})
    b = T({edges[2]: -1})
    m = T(dict((e, -i) for i, e in enumerate(edges)))
    
    def assertEqualSquares(self, s1, s2):
        ''' Return whether two squares are equal since they are only defined up to 180 degree rotation. '''
        
        return s1 == s2 or s1 == s2[2:] + s2[:2]
    
    def test_twist(self):
        self.assertEqual(self.S('a_0')(self.a), self.a)
        self.assertEqual(self.S('A_0.a_0')(self.m), self.m)
        self.assertEqual(self.S('b_1')(self.b), {3: 1, 4: 1, 6: 2, 7: 1, 8: 1})
    
    def test_flip(self):
        h = self.T.encode([{0}, {0}])
        self.assertEqualSquares(h.target.link(0), h.source.link(0))
    
    def test_expr(self):
        h = self.S('a{n > 7 or n % 6 == 3}')
        self.assertEqual(h(self.m), {1: -2, 2: -4, 3: -6, 4: -8, -2: -3, -5: -9, -4: -7, -3: -5, -1: -1})
    
    def test_powers(self):
        self.assertEqual((self.S('a_0.a.b_1')**0)(self.b), self.b)
        self.assertEqual((self.S('a_0')**1)(self.b), {2: -1})
        self.assertEqual((self.S('a_0')**2)(self.b), {1: 1})
        self.assertEqual((self.S('a_0')**10)(self.b), {1: 9, 2: 8})
        self.assertEqual((self.S('s.a_0.a_0')**10)(self.b), {31: 1})

    def test_infinite_twist_commutes(self):
        s = self.S('s')
        t = self.S('a')
        self.assertEqual((t * s**1)(self.b), (s**1 * t)(self.b))
        self.assertEqual((t * s**10)(self.b), (s**10 * t)(self.b))

class TestLadder(TestCase):
    S = bigger.load.ladder()
    T = S.triangulation
    L = T.as_lamination()
    edges = list(islice(T, 10))
    a = T({edges[0]: -1})
    b = T({edges[2]: -1})
    m = T(dict((e, -i) for i, e in enumerate(edges)))
    
    def test_str(self):
        self.assertEqual(str(self.L), 'Infinitely supported lamination (0, 0): -1, (0, 1): -1, (0, 2): -1, (0, 3): -1, (0, 4): -1, (0, 5): -1, (0, 6): -1, (0, 7): -1, (0, 8): -1, (-1, 0): -1 ...')
        self.assertEqual(str(self.a), 'Lamination (0, 0): -1')
        self.assertEqual(repr(self.L), str(self.L))
    
    def test_twist(self):
        self.assertEqual(self.S('a_1')(self.m), {(0, 1): -1, (0, 7): -7, (0, 4): -4, (0, 3): -3, (0, 6): -6, (-1, 0): -9, (0, 2): -2, (0, 5): -5, (0, 8): -8})
        self.assertEqual(self.S('a.b.s.s.a_1.B_1')(self.m), self.S('a_3.s.b.a.s.B_1')(self.m))

class TestSpottedCantor(TestCase):
    S = bigger.load.spotted_cantor()
    T = S.triangulation
    L = T.as_lamination()
    edges = list(islice(T, 10))
    a = T({edges[0]: -1})
    b = T({edges[2]: -1})
    m = T(dict((e, -i) for i, e in enumerate(edges)))
    
    def test_str(self):
        self.assertEqual(str(self.L), 'Infinitely supported lamination (0, 0): -1, (0, 1): -1, (0, 2): -1, (0, 3): -1, (1, 0): -1, (1, 1): -1, (1, 2): -1, (1, 3): -1, (2, 0): -1, (2, 1): -1 ...')
        self.assertEqual(str(self.a), 'Lamination (0, 0): -1')
        self.assertEqual(repr(self.L), str(self.L))
    
    def test_twist(self):
        self.assertEqual(self.S('A_1.a_1')(self.m), self.m)
        self.assertEqual(self.S('a_1')(self.m), {(0, 1): -1, (1, 2): -6, (2, 1): -9, (1, 1): 4, (0, 3): -3, (2, 0): -8, (0, 2): -2, (1, 0): -5, (1, 3): -7})
        self.assertEqual(self.S('a.a.A_1')(self.m), self.S('A_1.a.a')(self.m))

