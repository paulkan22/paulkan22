import unittest

from core_service.src.monitor_utils import MonitorCandidate, cap_candidates


class MonitorIngestionCapsTests(unittest.TestCase):
    def test_cap_candidates(self):
        cands = [MonitorCandidate(user_id=i) for i in range(10)]
        capped = cap_candidates(cands, 3)
        self.assertEqual(len(capped), 3)
        self.assertEqual([c.user_id for c in capped], [0, 1, 2])

    def test_cap_zero(self):
        cands = [MonitorCandidate(user_id=1)]
        self.assertEqual(cap_candidates(cands, 0), [])


if __name__ == '__main__':
    unittest.main()
