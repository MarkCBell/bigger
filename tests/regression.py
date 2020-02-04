
from unittest import TestCase
import bigger

class TestRegression(TestCase):
    S = bigger.load.flute()
    a = S.triangulation({0: -1})
    b = S.triangulation({1: -1})
    m = S.triangulation({1: -1})
    m2 = S.triangulation(dict((i, -i) for i in range(10)))
    
    def assertEqualSquares(self, s1, s2):
        ''' Return whether two squares are equal since they are only defined up to 180 degree rotation. '''
        
        return s1 == s2 or s1 == s2[2:] + s2[:2]
    
    def test_twist(self):
        self.assertEqual(self.S('a0')(self.a), self.a)
        self.assertEqual(self.S('A0.a0')(self.m), self.m)
        self.assertEqual(self.S('A0.a0')(self.m2), self.m2)
    
    def test_flip(self):
        h = self.S.triangulation.encode([{0}, {0}])
        self.assertEqualSquares(h.target.link(0), h.source.link(0))
    
    def test_explicit(self):
        self.assertEqual((self.S('a0')**1)(self.b), {2: 1})
        self.assertEqual((self.S('a0')**2)(self.b), {1: 1, 2: 2})
        self.assertEqual((self.S('a0')**10)(self.b), {1: 9, 2: 10})
        self.assertEqual((self.S('s.a0.a0')**10)(self.b), {32: 2, 31: 1})

    def test_infinite_twist_commutes(self):
        s = self.S('s')
        t = self.S('t')
        self.assertEqual((t * s**1)(self.b), (s**1 * t)(self.b))
        self.assertEqual((t * s**10)(self.b), (s**10 * t)(self.b))

