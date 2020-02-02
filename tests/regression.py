
from unittest import TestCase
import bigger

class TestRegression(TestCase):
    def test_flute(self):
        S = bigger.load.flute()
        a = S.triangulation({0: -1})
        self.assertIsInstance(a, bigger.FinitelySupportedLamination)
        self.assertEqual(a, S('a0')(a))
    
    def test_flip(self):
        S = bigger.load.flute()
        T = S.triangulation
        oe = bigger.oedger(0)
        h = T.encode([~oe, oe])
        self.assertEqual(h.target.square(0), h.source.square(0))
    
    def test_basic_twist(self):
        S = bigger.load.flute()
        m = S.triangulation({1: -1})
        self.assertEqual(S('A0.a0')(m), m)
    
    def test_twist(self):
        S = bigger.load.flute()
        m = S.triangulation(dict((i, -i) for i in range(10)))
        self.assertEqual(S('A0.a0')(m), m)

