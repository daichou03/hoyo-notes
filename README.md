# hoyo-notes

Data acquisition only (Phase 1): read **HoYoLAB overseas** real-time notes for explicitly selected Genshin Impact, Honkai: Star Rail, and Zenless Zone Zero game UIDs across multiple independent HoYoverse login accounts.

No desktop widget or pet integration is in scope for this phase.

## Setup (Windows PowerShell)

Requires Python 3.10+.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item config.example.json config.json
```

Edit `config.json`: replace example UIDs with real game UIDs. Each account refers to its own environment variable containing **the Cookie header string** from the corresponding logged-in `hoyolab.com` browser session. The same account can be reused for multiple games.

Sign in once through a separate browser profile for each account. The profile stays on disk, and the script copies the HoYoLAB cookie into `cookies.json`.

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH = "$pwd\.browser\playwright"
python -m playwright install chromium
python login_browser.py --config config.json --account main
python login_browser.py --config config.json --account 05
python login_browser.py --config config.json --account 06
python login_browser.py --config config.json --account 01
```

You can still set a cookie in PowerShell and save it with `--save-cookies`. A variable set in the current window overrides `cookies.json`.

```powershell
$env:HOYO_COOKIE_MAIN = 'ltuid_v2=...; ltoken_v2=...'
$env:HOYO_COOKIE_ALT = 'ltuid_v2=...; ltoken_v2=...'
$env:HOYO_COOKIE_06 = 'ltuid_v2=...; ltoken_v2=...'
$env:HOYO_COOKIE_01 = 'ltuid_v2=...; ltoken_v2=...'
python fetch_notes.py --config config.json --save-cookies
```

`cookies.json` is plain text on this machine and is gitignored. Do not paste credentials into GitHub, issues, screenshots or shared logs. This is not an encrypted credential store.

## Expected output

A JSON object with a `profiles` array. Each configured profile contains `name`, `account`, `game`, `uid`, `fetched_at`, `ok`, and either raw parsed `data` or an `error_type`. Failures of one profile do not block other profiles. For now output is printed to stdout; **avoid sharing it publicly** because game account details may be private.

## Acceptance checklist

- [ ] Auth works for independent HoYoLAB overseas logins
- [ ] Read Genshin real-time notes for the main UID and alts 05, 06, and 01
- [ ] Read Star Rail real-time notes for selected UID on shared account
- [ ] Read ZZZ real-time notes for selected UID on shared account
- [ ] Confirm returned fields and document real API errors (without tokens)
- [ ] Add credential storage, retries, tests and a normalized state schema

Implementation uses [genshin.py](https://github.com/seriaati/genshin.py), an unofficial API wrapper; no official service availability guarantee. It has **not yet been verified against live user credentials**.

## Scope

Phase 1: account configuration, authentication, raw note retrieval, testing and errors.

Phase 2 (separate): local monitoring, normalized API, desktop widget or desktop pet display.
