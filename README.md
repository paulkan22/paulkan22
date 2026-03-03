# Telegram Lead Monitoring & Mutual Ranking System

Production-safe system for collecting leads from Telegram monitor groups, enriching users via mutual chats, ranking by overlap with reference groups, and exporting XLSX reports via Telegram bot controls.

---

## 1) What is implemented now

### `bot_service`
- Aiogram-based Telegram control panel with inline buttons
- Whitelist access control
- Sections: stats, accounts list, groups list, exports (7/30/hot)
- Redis-backed RUNNING/STOPPED state switches (`▶️ Старт`, `🛑 Стоп`)
- Manual balancer commands: `/set_limit`, `/sleep_account`
- Account metadata validation model for onboarding packages
- File-based account onboarding flow via `/upload_account` (`.session` + `.json`)
- XLSX export generation via `openpyxl`

### `core_service`
- Async worker loop for queued mutual tasks
- Cluster-aware account pick (by account status + cluster)
- Adaptive policy primitives: jitter, cooldown/sleep handling, limit growth
- Ranking helpers (`cold/warm/hot/very_hot`, `reference_density`)
- Monitor chatter heuristics module (open members vs hidden members parse strategy)
- Telethon mutual engine mode (`TELETHON_MODE=live`) + safe mock fallback mode
- Background monitor-ingestion loop that enqueues mutual tasks from monitor groups

### Infrastructure
- Docker Compose with `postgres`, `redis`, `bot_service`, `core_service`
- SQL schema for `users`, `groups`, `accounts`, `mutual_tasks`, `audit_logs`, `backup_runs`

---

## 2) What is still pending for full production completion

- Production hardening for live Telethon mode (session health checks, retry matrix, richer flood taxonomies)
- Real monitor collectors for Telegram groups (instead of synthetic source in ingestion loop)
- Automated backup executor (current implementation tracks backup runs in DB)

---

## 3) Repository structure

- `bot_service/src/` — bot handlers, middleware, state, exports, DB access
- `core_service/src/` — worker, balancer, repository, monitor analysis, ranking
- `db/schema.sql` — PostgreSQL schema and indexes
- `docs/TECH_SPEC.md` — normalized technical specification
- `docs/ACCOUNT_DATA_REQUIRED.md` — exact data to provide per Telegram account
- `tests/` — unit tests

---

## 4) Quick start

## 4.1 Prepare environment

1. Copy env template:
   ```bash
   cp .env.example .env
   ```
2. Fill required values in `.env`:
   - `BOT_TOKEN`
   - `BOT_WHITELIST`
   - DB/Redis URLs (defaults are already compose-friendly)

## 4.2 Run services

```bash
docker compose up --build
```

If you run without Docker, install dependencies from both service folders and start each service as a Python module.

---

## 5) Configuration reference (`.env`)

- `BOT_TOKEN` — Telegram bot token
- `BOT_WHITELIST` — comma-separated Telegram user IDs with access
- `DATABASE_URL` — asyncpg SQLAlchemy URL
- `REDIS_URL` — redis URL
- `MONITOR_SCAN_MINUTES_MIN/MAX` — monitor scan interval bounds
- `MUTUAL_JITTER_MIN_SECONDS/MAX` — random pause bounds between mutual operations
- `DYNAMIC_LIMIT_INITIAL/MIN/MAX` — adaptive account limits
- `COOLDOWN_MIN_MINUTES/MAX` — cooldown window for short flood handling
- `WORKER_TICK_SECONDS` — polling tick when queue/state is idle

---

## 6) Data model summary

### `users`
Stores discovered users and enrichment state:
- identity (`user_id`, `username`)
- source / activity (`source_chat`, `monitor_group_count`, `last_seen_category`)
- mutual scoring (`mutual_reference_count`, `mutual_groups_json`, `last_mutual_check`)

### `groups`
Stores monitor/reference groups and cluster mapping.

### `accounts`
Stores Telegram account runtime metadata:
- session path
- proxy
- status (`ACTIVE/COOLDOWN/SLEEP/ERROR`)
- dynamic limits
- trust/sleep state
- cluster assignment

### `mutual_tasks`
Queue for user mutual-check jobs.

---

## 7) Bot controls (current)

Main actions:
- `📊 Статистика`
- `👥 Аккаунты`
- `📂 Группы`
- `📤 Экспорт` (7/30/hot)
- `🧠 Балансировщик` (read view)
- `▶️ Старт` / `🛑 Стоп`

Start/Stop toggles global runtime state in Redis; `core_service` respects this state in loop execution.

---

## 8) Export behavior

Current exports include columns:
- `username`
- `user_id`
- `source_chat`
- `mutual_reference_count`
- `reference_density`
- `monitor_group_count`
- `first_seen`
- `last_seen_category`
- `mutual_groups_list`

### Filtering rules now
- Weekly/custom export: users first seen in period OR updated mutual activity, excluding `mutual=0 && last_seen_category='long time ago'`
- Hot export: `mutual_reference_count >= 2` in selected period

### Sorting
1. `mutual_reference_count DESC`
2. `monitor_group_count DESC`

---

## 9) What data you must provide for each account

> Short answer: **`.session` + account metadata JSON + proxy + cluster assignment**.

Full checklist is in `docs/ACCOUNT_DATA_REQUIRED.md`.

At minimum per account:
1. Telegram `.session` file
2. API credentials (`api_id`, `api_hash`)
3. Device fingerprint fields (`device_model`, `system_version`, `app_version`, `lang_code`, `system_lang_code`)
4. Timezone / locale consistency (`lang_pack`, `tz_offset` optional but recommended)
5. Network route: SOCKS5 proxy (`host`, `port`, optional `username/password`)
6. Internal mapping fields (`cluster_id`, optional account label)

---

## 10) Recommended secure onboarding process

1. Create account package per account (session + json)
2. Validate JSON schema and required keys
3. Attach dedicated SOCKS5 proxy (1 account = 1 proxy)
4. Assign `cluster_id`
5. Insert account into DB with initial safe defaults:
   - `status=ACTIVE`
   - `dynamic_limit=80`
   - `trust_score=0`
6. Add a small set of test tasks and verify no flood errors
7. Gradually increase volume

---

## 11) Testing

Run full local checks:

```bash
python -m compileall bot_service/src core_service/src tests
python -m unittest discover -s tests -p 'test_*.py' -v
```

---

## 12) Next development milestones

1. Implement Telethon adapters in `MutualEngine`
2. Implement monitor group scraping scheduler + message/member collectors
3. Add bot flows for uploading account package files
4. Add manual balancer controls in bot (set sleep/limit)
5. Add observability (structured logs, metrics, alerts)
6. Add daily backup job + restore runbook
