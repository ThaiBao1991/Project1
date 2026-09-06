import unittest
import time
from gemini_safe import (
    AccountPool,
    GeminiCoordinator,
    ErrorKind,
    track_call,
    get_account_daily_calls,
    get_today_call_stats,
    DAILY_ACCOUNT_BUDGET,
    _call_stats_lock,
    _call_stats,
    _account_call_stats,
    _key_call_stats,
)


class TestGeminiAccountBudget(unittest.TestCase):

    def setUp(self):
        # Reset counters before each test
        with _call_stats_lock:
            _call_stats["total"] = 0
            _account_call_stats.clear()
            _key_call_stats.clear()

    def test_track_call_per_account_and_key(self):
        k1 = {"key": "AIzaSyTestKey1", "email": "acc1@gmail.com", "project_id": "1"}
        k2 = {"key": "AIzaSyTestKey2", "email": "acc2@gmail.com", "project_id": "2"}

        tot1, acct1 = track_call(k1)
        self.assertEqual(tot1, 1)
        self.assertEqual(acct1, 1)
        self.assertEqual(k1.get("today_calls"), 1)
        self.assertEqual(k1.get("today_account_calls"), 1)

        tot2, acct2 = track_call(k1)
        self.assertEqual(tot2, 2)
        self.assertEqual(acct2, 2)
        self.assertEqual(k1.get("today_calls"), 2)

        tot3, acct3 = track_call(k2)
        self.assertEqual(tot3, 3)
        self.assertEqual(acct3, 1)
        self.assertEqual(get_account_daily_calls("acc1@gmail.com"), 2)
        self.assertEqual(get_account_daily_calls("acc2@gmail.com"), 1)

    def test_account_pool_skips_exhausted_account(self):
        pool = AccountPool(account_daily_budget=2)
        keys = [
            {"key": "key_a1", "email": "acc_a@gmail.com", "status": "active"},
            {"key": "key_b1", "email": "acc_b@gmail.com", "status": "active"},
        ]
        pool.sync(keys)

        # Ban đầu cả 2 account đều dùng được
        picked1 = pool.pick()
        self.assertIsNotNone(picked1)

        # Giả lập acc_a đã gọi 2 lần (đạt budget)
        track_call(keys[0])
        track_call(keys[0])
        self.assertEqual(get_account_daily_calls("acc_a@gmail.com"), 2)

        # Sau khi acc_a đạt budget, pool chỉ pick acc_b
        picked2 = pool.pick()
        self.assertEqual(picked2["email"], "acc_b@gmail.com")

        picked3 = pool.pick()
        self.assertEqual(picked3["email"], "acc_b@gmail.com")

    def test_all_accounts_exhausted_daily(self):
        pool = AccountPool(account_daily_budget=1)
        keys = [
            {"key": "k_x", "email": "x@gmail.com", "status": "active"},
            {"key": "k_y", "email": "y@gmail.com", "status": "active"},
        ]
        pool.sync(keys)
        self.assertFalse(pool.all_accounts_exhausted_daily())

        track_call(keys[0])
        self.assertFalse(pool.all_accounts_exhausted_daily())

        track_call(keys[1])
        self.assertTrue(pool.all_accounts_exhausted_daily())

        # Khi all exhausted, pick() trả về None
        self.assertIsNone(pool.pick())

    def test_coordinator_stops_when_all_accounts_exhausted(self):
        keys = [
            {"key": "k_only", "email": "only@gmail.com", "status": "active"}
        ]
        logs = []
        coord = GeminiCoordinator(
            key_loader=lambda: keys,
            account_budget=1,
            log_fn=lambda m: logs.append(m)
        )
        # Giả lập account đã dùng đủ 1 call
        track_call(keys[0])

        res = coord.request("Test prompt")
        self.assertFalse(res["ok"])
        self.assertEqual(res["error"]["kind"], ErrorKind.ALL_BUDGET_EXHAUSTED)
        self.assertTrue(any("đạt ngân sách an toàn" in log for log in logs))


if __name__ == "__main__":
    unittest.main()
