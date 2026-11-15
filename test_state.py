import unittest

from state import extract_state


class ExtractStateTests(unittest.TestCase):
    def test_genshin_counts_encounter_points_and_unclaimed_rewards(self):
        state = extract_state(
            "genshin",
            {
                "finished_task_num": 4,
                "total_task_num": 4,
                "is_extra_task_reward_received": False,
                "daily_task": {
                    "task_rewards": [
                        {"status": "TaskRewardStatusTakenAward"},
                        {"status": "TaskRewardStatusTakenAward"},
                        {"status": "TaskRewardStatusFinished"},
                        {"status": "TaskRewardStatusFinished"},
                    ],
                    "attendance_rewards": [
                        {"status": "AttendanceRewardStatusTakenAward"},
                        {"status": "AttendanceRewardStatusWaitTaken"},
                        {"status": "AttendanceRewardStatusUnfinished"},
                        {"status": "AttendanceRewardStatusForbid"},
                    ],
                },
            },
        )
        self.assertEqual(
            state["daily_commissions"],
            {
                "done": True,
                "completed": 4,
                "required": 4,
                "via_encounter_points": 2,
                "claimed": False,
            },
        )

    def test_genshin_claimed_when_rewards_and_bonus_are_taken(self):
        state = extract_state(
            "genshin",
            {
                "completed_commissions": 4,
                "max_commissions": 4,
                "claimed_commission_reward": True,
                "daily_task": {
                    "task_rewards": [{"status": "TaskRewardStatusTakenAward"}] * 4,
                    "attendance_rewards": [{"status": "AttendanceRewardStatusTakenAward"}] * 4,
                },
            },
        )
        commissions = state["daily_commissions"]
        self.assertTrue(commissions["done"])
        self.assertTrue(commissions["claimed"])
        self.assertEqual(commissions["via_encounter_points"], 4)

    def test_star_rail_daily_training_and_divergent_universe_points(self):
        state = extract_state(
            "starrail",
            {
                "current_train_score": 500,
                "max_train_score": 500,
                "current_rogue_score": 0,
                "max_rogue_score": 18000,
                "rogue_tourn_weekly_cur": 1000,
                "rogue_tourn_weekly_max": 1000,
            },
        )
        self.assertEqual(state["daily"], {"done": True, "points": 500, "required": 500, "claimed": True})
        self.assertEqual(state["weekly"], {"done": True, "points": 1000, "required": 1000, "claimed": True})

    def test_star_rail_incomplete_points_are_not_claimed(self):
        state = extract_state(
            "starrail",
            {"current_train_score": 200, "max_train_score": 500, "current_bonus_synchronicity_points": 100, "max_bonus_synchronicity_points": 1000},
        )
        self.assertFalse(state["daily"]["done"])
        self.assertFalse(state["daily"]["claimed"])
        self.assertFalse(state["weekly"]["done"])

    def test_zzz_daily_engagement_and_weekly_points(self):
        state = extract_state(
            "zzz",
            {
                "vitality": {"current": 400, "max": 400},
                "weekly_task": {"cur_point": 750, "max_point": 2100},
                "bounty_commission": {"num": 8000, "total": 8000},
            },
        )
        self.assertEqual(state["daily"], {"done": True, "points": 400, "required": 400, "claimed": True})
        self.assertEqual(state["weekly"], {"done": False, "points": 750, "required": 2100, "claimed": False})
        self.assertEqual(state["hollow"], {"done": True, "points": 8000, "required": 8000, "claimed": True})


if __name__ == "__main__":
    unittest.main()
