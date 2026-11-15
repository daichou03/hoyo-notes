"""Open a persistent browser profile and save its HoYoLAB login cookie.

Each account gets its own profile under .browser/, so the login survives
after this script and the browser window close. The cookie value is written
to cookies.json and is not printed.
"""
import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault(
    "PLAYWRIGHT_BROWSERS_PATH",
    str(Path(__file__).resolve().parent / ".browser" / "playwright"),
)

from playwright.sync_api import sync_playwright

from fetch_notes import cookie_file_path, load_config, load_stored_cookies, store_cookie

LOGIN_URL = "https://www.hoyolab.com/"
REQUIRED = ("ltuid_v2", "ltoken_v2")
KEPT = REQUIRED + ("ltmid_v2", "account_id_v2", "account_mid_v2", "cookie_token_v2")


def browser_profile_dir(account_id: str) -> Path:
    return Path(".browser") / account_id


def hoyolab_cookie_header(cookies: list[dict]) -> str:
    found = {}
    for cookie in cookies:
        domain = str(cookie.get("domain", ""))
        name = str(cookie.get("name", ""))
        if "hoyolab.com" not in domain or name not in KEPT:
            continue
        value = str(cookie.get("value", ""))
        if value:
            found[name] = value
    missing = [name for name in REQUIRED if name not in found]
    if missing:
        raise ValueError("HoYoLAB login was not found in the browser profile")
    return "; ".join(f"{name}={found[name]}" for name in KEPT if name in found)


def capture_cookie(account_id: str) -> str:
    profile = browser_profile_dir(account_id)
    profile.mkdir(parents=True, exist_ok=True)
    print(f"Opening a browser for account {account_id}.")
    print("Sign in at hoyolab.com as that account, then return here and press Enter.")
    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            str(profile),
            headless=False,
            viewport={"width": 1280, "height": 800},
        )
        try:
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(LOGIN_URL)
            input()
            return hoyolab_cookie_header(context.cookies())
        finally:
            context.close()


def main(config_path: str, account_id: str) -> int:
    config = load_config(config_path)
    accounts = {account["id"]: account for account in config["accounts"]}
    if account_id not in accounts:
        known = ", ".join(accounts)
        raise ValueError(f"Unknown account {account_id}. Known accounts: {known}")
    cookie_env = accounts[account_id]["cookie_env"]
    header = capture_cookie(account_id)
    stored_path = cookie_file_path(config_path)
    store_cookie(stored_path, cookie_env, header, load_stored_cookies(stored_path))
    print(f"Saved {cookie_env} to {stored_path.name}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Save a HoYoLAB cookie from a persistent browser login")
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--account", required=True, help="Account id from config.json, such as main, 05, 06, or 01")
    args = parser.parse_args()
    try:
        sys.exit(main(args.config, args.account))
    except (ValueError, KeyError, FileNotFoundError) as exc:
        print(f"Login error: {exc}", file=sys.stderr)
        sys.exit(2)
