from datetime import datetime, timedelta, timezone
import unittest

from core_service.src.monitor_analysis import (
    ChatterHeuristics,
    MessageSample,
    choose_monitor_parse_mode,
    is_chatter_group,
)


class MonitorAnalysisTests(unittest.TestCase):
    def test_chatter_group_true(self):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        messages = []
        for idx in range(45):
            user = (idx % 18) + 1
            messages.append(MessageSample(user_id=user, sent_at=start + timedelta(minutes=idx)))

        self.assertTrue(is_chatter_group(messages))

    def test_chatter_group_false_due_to_dominance(self):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        messages = [MessageSample(user_id=1, sent_at=start + timedelta(minutes=i)) for i in range(40)]
        messages.extend(
            [
                MessageSample(user_id=2, sent_at=start + timedelta(minutes=41)),
                MessageSample(user_id=3, sent_at=start + timedelta(minutes=42)),
            ]
        )
        self.assertFalse(is_chatter_group(messages))

    def test_mode_selection(self):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        active = [MessageSample(user_id=(i % 17) + 1, sent_at=start + timedelta(minutes=i)) for i in range(34)]
        quiet = [MessageSample(user_id=1, sent_at=start + timedelta(minutes=i)) for i in range(10)]

        m1 = choose_monitor_parse_mode(members_open=True, messages=[])
        self.assertEqual(m1.parse_mode, 'members_list')

        m2 = choose_monitor_parse_mode(members_open=False, messages=active)
        self.assertEqual(m2.parse_mode, 'messages_full_history')

        m3 = choose_monitor_parse_mode(members_open=False, messages=quiet)
        self.assertEqual(m3.parse_mode, 'messages_recent_authors')

    def test_custom_heuristics(self):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        messages = [MessageSample(user_id=(i % 6) + 1, sent_at=start + timedelta(minutes=i)) for i in range(20)]
        strict = ChatterHeuristics(min_unique_authors=10)
        relaxed = ChatterHeuristics(min_unique_authors=6, min_time_span_minutes=10)

        self.assertFalse(is_chatter_group(messages, strict))
        self.assertTrue(is_chatter_group(messages, relaxed))


if __name__ == '__main__':
    unittest.main()
