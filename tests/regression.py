
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

