import unittest

from core_service.src.balancer import AccountRuntime, AccountStatus, DynamicLimitPolicy
from core_service.src.ranking import rank_category, reference_density


class RankingTests(unittest.TestCase):
    def test_rank_category(self):
        self.assertEqual(rank_category(0), 'cold')
        self.assertEqual(rank_category(1), 'warm')
        self.assertEqual(rank_category(2), 'hot')
        self.assertEqual(rank_category(5), 'very_hot')

    def test_density(self):
        self.assertEqual(reference_density(3, 0), 0.0)
        self.assertEqual(reference_density(3, 10), 0.3)


class BalancerTests(unittest.TestCase):
    def test_small_flood_reduces_limit_and_cooldown(self):
        policy = DynamicLimitPolicy()
        runtime = AccountRuntime(dynamic_limit=100)
        updated = policy.on_small_flood(runtime)
        self.assertEqual(updated.status, AccountStatus.COOLDOWN)
        self.assertLessEqual(updated.dynamic_limit, 100)
        self.assertGreaterEqual(updated.dynamic_limit, policy.min_limit)
        self.assertIsNotNone(updated.sleep_until)

    def test_long_flood_puts_account_to_sleep(self):
        policy = DynamicLimitPolicy()
        runtime = AccountRuntime(dynamic_limit=100)
        updated = policy.on_long_flood(runtime, flood_wait_seconds=7200)
        self.assertEqual(updated.status, AccountStatus.SLEEP)
        self.assertLessEqual(updated.dynamic_limit, 50)
        self.assertGreaterEqual(updated.dynamic_limit, policy.min_limit)
        self.assertIsNotNone(updated.sleep_until)

    def test_reward_grows_limit(self):
        policy = DynamicLimitPolicy(max_limit=150)
        runtime = AccountRuntime(dynamic_limit=80, trust_score=0)
        updated = policy.reward_stable_period(runtime)
        self.assertGreaterEqual(updated.dynamic_limit, 80)
        self.assertEqual(updated.trust_score, 1)


if __name__ == '__main__':
    unittest.main()
