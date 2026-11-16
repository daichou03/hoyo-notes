"""Reduce HoYoLAB real-time notes to the daily and weekly checklist.

Genshin encounter points are the resin rewards HoYoLAB calls attendance
rewards. Commissions completed that way are already included in the finished
commission count. Activity points in Star Rail and ZZZ increase when the
reward is claimed, and those note payloads have no separate claim flag, so
a full point bar is both fulfilled and claimed.
"""

from __future__ import annotations


_ENCOUNTER_FILLED = {
    "AttendanceRewardStatusTakenAward",
    "AttendanceRewardStatusWaitTaken",
}


def extract_state(game: str, data: dict) -> dict:
    if game == "genshin":
        return {"daily_commissions": _genshin_commissions(data)}
    if game == "starrail":
        return {
            "daily": _point_bar(
                data,
                (("current_train_score",),),
                (("max_train_score",),),
            ),
            # rogue_tourn_weekly_max is still 1000, while the shared weekly bar is period_score.
            # grid_fight is the Currency War score and uses the same 18000 cap.
            "weekly": _point_bar(
                data,
                (
                    ("period_score",),
                    ("grid_fight_weekly_cur",),
                ),
                (
                    ("period_max_score",),
                    ("grid_fight_weekly_max",),
                ),
            ),
        }
    if game == "zzz":
        return {
            "daily": _point_bar(
                data,
                (("engagement", "current"), ("vitality", "current")),
                (("engagement", "max"), ("vitality", "max")),
            ),
            "weekly": _point_bar(
                data,
                (("weekly_task", "cur_point"),),
                (("weekly_task", "max_point"),),
            ),
            # Hollow Zero and Bagel share this bounty score. Its cap is 8000.
            "hollow": _point_bar(
                data,
                (
                    ("bounty_commission", "num"),
                    ("hollow_zero", "bounty_commission", "cur_completed"),
                    ("hollow_zero", "bounty_commission", "num"),
                ),
                (
                    ("bounty_commission", "total"),
                    ("hollow_zero", "bounty_commission", "total"),
                ),
            ),
        }
    raise ValueError(f"Unsupported game: {game}")


def _genshin_commissions(data: dict) -> dict:
    daily = data.get("daily_task") if isinstance(data.get("daily_task"), dict) else {}
    completed = _first_int(
        data,
        daily,
        (("completed_commissions",), ("finished_task_num",)),
        (("completed_tasks",), ("finished_num",)),
    )
    required = _first_int(
        data,
        daily,
        (("max_commissions",), ("total_task_num",)),
        (("max_tasks",), ("total_num",)),
    )
    via_encounter_points = sum(
        _status(item) in _ENCOUNTER_FILLED for item in daily.get("attendance_rewards") or []
    )
    done = completed is not None and required is not None and completed >= required
    # This is Katheryne's 20 primogem bonus, not the per-commission reward slots.
    # Encounter-point completions leave those slots unfinished after the bonus is claimed.
    bonus_claimed = _first_bool(
        data,
        daily,
        (("claimed_commission_reward",), ("is_extra_task_reward_received",)),
        (("claimed_commission_reward",), ("is_extra_task_reward_received",)),
    )
    claimed = bonus_claimed is True
    encounter_points_left = _lookup_number(daily, (("stored_attendance",),))
    if encounter_points_left is None:
        encounter_points_left = _lookup_number(data, (("stored_attendance",),))
    return {
        "done": done,
        "completed": completed,
        "required": required,
        "via_encounter_points": via_encounter_points,
        "claimed": claimed,
        "encounter_points_left": encounter_points_left,
    }


def _point_bar(data: dict, current_paths: tuple, required_paths: tuple) -> dict:
    current = _lookup_int(data, current_paths)
    required = _lookup_int(data, required_paths)
    if current is None or required is None:
        return {"done": None, "points": current, "required": required, "claimed": None}
    done = current >= required
    return {"done": done, "points": current, "required": required, "claimed": done}


def _lookup_int(data: dict, paths: tuple) -> int | None:
    for path in paths:
        value = _dig(data, path)
        if isinstance(value, bool) or value is None:
            continue
        if isinstance(value, (int, float, str)) and str(value).lstrip("-").isdigit():
            return int(value)
    return None


def _lookup_number(data: dict, paths: tuple) -> float | None:
    for path in paths:
        value = _dig(data, path)
        if isinstance(value, bool) or value is None:
            continue
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                continue
    return None


def _first_int(data: dict, daily: dict, top_paths: tuple, daily_paths: tuple) -> int | None:
    return _lookup_int(data, top_paths) if _lookup_int(data, top_paths) is not None else _lookup_int(daily, daily_paths)


def _first_bool(data: dict, daily: dict, top_paths: tuple, daily_paths: tuple) -> bool | None:
    for source, paths in ((data, top_paths), (daily, daily_paths)):
        for path in paths:
            value = _dig(source, path)
            if isinstance(value, bool):
                return value
    return None


def _dig(data: dict, path: tuple):
    current = data
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def _status(item) -> str:
    if isinstance(item, dict):
        item = item.get("status")
    value = getattr(item, "value", item)
    return "" if value is None else str(value)
