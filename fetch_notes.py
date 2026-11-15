"""Fetch HoYoLAB overseas real-time notes for explicitly configured game UIDs.

Never commit cookies, local config files, or fetched account data.
"""
import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import genshin

from state import extract_state

METHODS = {
    "genshin": "get_genshin_notes",
    "starrail": "get_starrail_notes",
    "zzz": "get_zzz_notes",
}


def load_config(path: str) -> dict:
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    accounts = {account["id"]: account for account in config["accounts"]}
    for profile in config["profiles"]:
        if profile["account"] not in accounts:
            raise ValueError(f"Unknown account: {profile['account']}")
        if profile["game"] not in METHODS:
            raise ValueError(f"Unsupported game: {profile['game']}")
        uid = profile.get("uid")
        if uid not in (None, ""):
            int(uid)
    return config


def cookie_file_path(config_path: str) -> Path:
    return Path(config_path).resolve().with_name("cookies.json")


def load_stored_cookies(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} must be a JSON object")
    stored = {}
    for key, value in data.items():
        if not isinstance(value, str):
            raise ValueError(f"{path.name} value for {key} must be a string")
        stored[str(key)] = value
    return stored


def resolve_cookie(cookie_env: str, stored: dict[str, str]) -> str:
    from_env = os.environ.get(cookie_env, "")
    if from_env.strip():
        return from_env
    return stored.get(cookie_env, "")


def store_cookie(path: Path, cookie_env: str, value: str, stored: dict[str, str]) -> None:
    updated = dict(stored)
    updated[cookie_env] = value
    path.write_text(json.dumps(updated, indent=2) + "\n", encoding="utf-8")


def store_cookies_from_env(path: Path, accounts: dict, stored: dict[str, str]) -> list[str]:
    """Write currently set cookie variables into cookies.json without dropping saved ones."""
    updated = dict(stored)
    saved = []
    for account in accounts.values():
        env_name = account["cookie_env"]
        value = os.environ.get(env_name, "")
        if value.strip():
            updated[env_name] = value
            saved.append(env_name)
    if saved:
        path.write_text(json.dumps(updated, indent=2) + "\n", encoding="utf-8")
    return saved


async def query_profile(profile: dict, accounts: dict, stored: dict[str, str], *, include_raw: bool) -> dict:
    timestamp = datetime.now(timezone.utc).isoformat()
    result = {
        "name": profile["name"],
        "account": profile["account"],
        "game": profile["game"],
        "uid": "" if profile.get("uid") in (None, "") else str(profile["uid"]),
        "fetched_at": timestamp,
    }
    if profile.get("uid") in (None, ""):
        return {**result, "ok": False, "error": "Missing uid"}
    account = accounts[profile["account"]]
    cookie_env = account["cookie_env"]
    cookies = resolve_cookie(cookie_env, stored)
    if not cookies.strip():
        return {**result, "ok": False, "error": f"Missing cookie: {cookie_env}"}

    # A separate client/cookie jar is used for each login account.
    # This genshin Client opens a session per request and closes it itself.
    try:
        client = genshin.Client(cookies, region=genshin.Region.OVERSEAS)
        method = getattr(client, METHODS[profile["game"]])
        notes = await method(uid=int(profile["uid"]), return_raw_data=True)
        extracted = {**result, "ok": True, "state": extract_state(profile["game"], notes)}
        if include_raw:
            extracted["data"] = notes
        return extracted
    except Exception as exc:
        # Do not include exception messages: upstream errors may echo auth headers.
        return {**result, "ok": False, "error_type": type(exc).__name__}


async def main(config_path: str, *, include_raw: bool, save_cookies: bool) -> int:
    config = load_config(config_path)
    accounts = {account["id"]: account for account in config["accounts"]}
    stored_path = cookie_file_path(config_path)
    stored = load_stored_cookies(stored_path)
    if save_cookies:
        saved = store_cookies_from_env(stored_path, accounts, stored)
        if saved:
            print(f"Saved {', '.join(saved)} to {stored_path.name}", file=sys.stderr)
            stored = load_stored_cookies(stored_path)
        else:
            print(f"No cookie environment variables were set; {stored_path.name} was left unchanged", file=sys.stderr)
    # Sequential on purpose: easiest to debug and minimizes request bursts.
    results = []
    for profile in config["profiles"]:
        results.append(await query_profile(profile, accounts, stored, include_raw=include_raw))
    print(json.dumps({"profiles": results}, ensure_ascii=False, indent=2, default=str))
    return 0 if all(item["ok"] for item in results) else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch overseas HoYoLAB game real-time notes")
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--raw", action="store_true", help="Include the full notes payload")
    parser.add_argument(
        "--save-cookies",
        action="store_true",
        help="Store the current cookie environment variables in cookies.json",
    )
    args = parser.parse_args()
    try:
        sys.exit(asyncio.run(main(args.config, include_raw=args.raw, save_cookies=args.save_cookies)))
    except (ValueError, KeyError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        sys.exit(2)
