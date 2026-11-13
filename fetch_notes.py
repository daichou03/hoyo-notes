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
        int(profile["uid"])
    return config


async def query_profile(profile: dict, accounts: dict) -> dict:
    timestamp = datetime.now(timezone.utc).isoformat()
    result = {
        "name": profile["name"],
        "account": profile["account"],
        "game": profile["game"],
        "uid": str(profile["uid"]),
        "fetched_at": timestamp,
    }
    account = accounts[profile["account"]]
    cookie_env = account["cookie_env"]
    cookies = os.environ.get(cookie_env, "")
    if not cookies.strip():
        return {**result, "ok": False, "error": f"Missing environment variable: {cookie_env}"}

    # A separate client/cookie jar is used for each login account.
    client = None
    try:
        client = genshin.Client(cookies, region=genshin.Region.OVERSEAS)
        method = getattr(client, METHODS[profile["game"]])
        notes = await method(uid=int(profile["uid"]))
        data = notes.model_dump(mode="json") if hasattr(notes, "model_dump") else notes
        return {**result, "ok": True, "data": data}
    except Exception as exc:
        # Do not include exception messages: upstream errors may echo auth headers.
        return {**result, "ok": False, "error_type": type(exc).__name__}
    finally:
        if client is not None:
            await client.close()


async def main(config_path: str) -> int:
    config = load_config(config_path)
    accounts = {account["id"]: account for account in config["accounts"]}
    # Sequential on purpose: easiest to debug and minimizes request bursts.
    results = []
    for profile in config["profiles"]:
        results.append(await query_profile(profile, accounts))
    print(json.dumps({"profiles": results}, ensure_ascii=False, indent=2, default=str))
    return 0 if all(item["ok"] for item in results) else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch overseas HoYoLAB game real-time notes")
    parser.add_argument("--config", default="config.json")
    args = parser.parse_args()
    try:
        sys.exit(asyncio.run(main(args.config)))
    except (ValueError, KeyError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        sys.exit(2)
