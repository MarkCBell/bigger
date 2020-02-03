
from unittest import TestCase
import bigger

class TestRegression(TestCase):
    def assertEqualSquares(self, s1, s2):
        ''' Return whether two squares are equal since they are only defined up to 180 degree rotation. '''
        
        return s1 == s2 or s1 == s2[2:] + s2[:2]
    
    def test_flute(self):
        S = bigger.load.flute()
        a = S.triangulation({0: -1})
        self.assertIsInstance(a, bigger.FinitelySupportedLamination)
        self.assertEqual(a, S('a0')(a))
    
    def test_flip(self):
        S = bigger.load.flute()
        T = S.triangulation
        h = T.encode([{0}, {0}])
        self.assertEqualSquares(h.target.neighbours(0), h.source.neighbours(0))
    
    def test_basic_twist(self):
        S = bigger.load.flute()
        m = S.triangulation({1: -1})
        self.assertEqual(S('A0.a0')(m), m)
    
    def test_twist(self):
        S = bigger.load.flute()
        m = S.triangulation(dict((i, -i) for i in range(10)))
        self.assertEqual(S('A0.a0')(m), m)
    
    def test_explicit(self):
        S = bigger.load.flute()
        a = S.triangulation({1: -1})
        self.assertIsInstance(a, bigger.FinitelySupportedLamination)
        self.assertEqual((S('a0')**1)(a), {2: 1})
        self.assertEqual((S('a0')**2)(a), {1: 1, 2: 2})
        self.assertEqual((S('a0')**10)(a), {1: 9, 2: 10})
        self.assertEqual((S('s.a0.a0')**10)(a), {32: 2, 31: 1})

