import unittest

from core_service.src.flood_control import classify_flood


class FloodControlTests(unittest.TestCase):
    def test_small(self):
        d = classify_flood(120)
        self.assertEqual(d.severity, 'small')

    def test_medium(self):
        d = classify_flood(1200)
        self.assertEqual(d.severity, 'medium')

    def test_long(self):
        d = classify_flood(7200)
        self.assertEqual(d.severity, 'long')


if __name__ == '__main__':
    unittest.main()
