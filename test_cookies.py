import os
import tempfile
import unittest
from pathlib import Path

from fetch_notes import load_stored_cookies, resolve_cookie, store_cookies_from_env
from login_browser import hoyolab_cookie_header


class CookieStoreTests(unittest.TestCase):
    def test_hoyolab_header_keeps_login_cookies_only(self):
        header = hoyolab_cookie_header(
            [
                {"name": "ltuid_v2", "value": "1", "domain": ".hoyolab.com"},
                {"name": "ltoken_v2", "value": "token", "domain": ".hoyolab.com"},
                {"name": "ltmid_v2", "value": "mid", "domain": ".hoyolab.com"},
                {"name": "_ga", "value": "ignore", "domain": ".hoyolab.com"},
                {"name": "ltuid_v2", "value": "other", "domain": ".example.com"},
            ]
        )
        self.assertEqual(header, "ltuid_v2=1; ltoken_v2=token; ltmid_v2=mid")

    def test_hoyolab_header_requires_login_cookie(self):
        with self.assertRaises(ValueError):
            hoyolab_cookie_header([{"name": "ltuid_v2", "value": "1", "domain": ".hoyolab.com"}])

    def test_environment_overrides_saved_cookie(self):
        previous = os.environ.get("HOYO_COOKIE_MAIN")
        os.environ["HOYO_COOKIE_MAIN"] = "from-env"
        try:
            self.assertEqual(resolve_cookie("HOYO_COOKIE_MAIN", {"HOYO_COOKIE_MAIN": "from-file"}), "from-env")
        finally:
            if previous is None:
                os.environ.pop("HOYO_COOKIE_MAIN", None)
            else:
                os.environ["HOYO_COOKIE_MAIN"] = previous

    def test_saved_cookie_is_used_when_environment_is_empty(self):
        previous = os.environ.pop("HOYO_COOKIE_06", None)
        try:
            self.assertEqual(resolve_cookie("HOYO_COOKIE_06", {"HOYO_COOKIE_06": "from-file"}), "from-file")
        finally:
            if previous is not None:
                os.environ["HOYO_COOKIE_06"] = previous

    def test_save_merges_without_dropping_other_accounts(self):
        previous = os.environ.get("HOYO_COOKIE_01")
        os.environ["HOYO_COOKIE_01"] = "new-01"
        try:
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "cookies.json"
                saved = store_cookies_from_env(
                    path,
                    {"01": {"id": "01", "cookie_env": "HOYO_COOKIE_01"}},
                    {"HOYO_COOKIE_MAIN": "keep-main"},
                )
                stored = load_stored_cookies(path)
        finally:
            if previous is None:
                os.environ.pop("HOYO_COOKIE_01", None)
            else:
                os.environ["HOYO_COOKIE_01"] = previous
        self.assertEqual(saved, ["HOYO_COOKIE_01"])
        self.assertEqual(stored["HOYO_COOKIE_MAIN"], "keep-main")
        self.assertEqual(stored["HOYO_COOKIE_01"], "new-01")


if __name__ == "__main__":
    unittest.main()
