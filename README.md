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

For a temporary PowerShell session:

```powershell
$env:HOYO_COOKIE_MAIN = 'ltuid_v2=...; ltoken_v2=...'
$env:HOYO_COOKIE_ALT = 'ltuid_v2=...; ltoken_v2=...'
python fetch_notes.py --config config.json
```

Cookie requirements vary by endpoint and may change. Do not paste credentials into GitHub, issues, screenshots or shared logs. Configuration, cookie files and output files are gitignored; environment variables here are a first-stage test mechanism, not a permanent encrypted credential store.

## Expected output

A JSON object with a `profiles` array. Each configured profile contains `name`, `account`, `game`, `uid`, `fetched_at`, `ok`, and either raw parsed `data` or an `error_type`. Failures of one profile do not block other profiles. For now output is printed to stdout; **avoid sharing it publicly** because game account details may be private.

## Acceptance checklist

- [ ] Auth works for two independent HoYoLAB overseas logins
- [ ] Read Genshin real-time notes for two chosen UIDs
- [ ] Read Star Rail real-time notes for selected UID on shared account
- [ ] Read ZZZ real-time notes for selected UID on shared account
- [ ] Confirm returned fields and document real API errors (without tokens)
- [ ] Add credential storage, retries, tests and a normalized state schema

Implementation uses [genshin.py](https://github.com/seriaati/genshin.py), an unofficial API wrapper; no official service availability guarantee. It has **not yet been verified against live user credentials**.

## Scope

Phase 1: account configuration, authentication, raw note retrieval, testing and errors.

Phase 2 (separate): local monitoring, normalized API, desktop widget or desktop pet display.
