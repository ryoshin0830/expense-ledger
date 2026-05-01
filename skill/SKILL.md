# expense-ledger Skill

Multi-currency expense tracking via Google Sheets. Records "where, what, how much, with what" for every transaction.

## Architecture

```
GitHub (ryoshin0830/expense-ledger) — Schema & scripts (single source of truth)
  └── SCHEMA.md  ← ALWAYS fetch fresh from GitHub before any operation
Google Sheets — Data storage
Python scripts — All data processing
```

## Setup

Ensure `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN` are in OpenClaw config.

Google Sheets URL: `https://docs.google.com/spreadsheets/d/1Wl3T8dh70Cb9mCH65igZetBdNJpnUUHiumELlyeulAc/edit`

## Mandatory Pre-Flight

**Before EVERY operation, fetch SCHEMA.md from GitHub:**

```bash
curl -s https://raw.githubusercontent.com/ryoshin0830/expense-ledger/main/SCHEMA.md
```

This ensures you always use the latest schema. Never rely on memory or cached versions.

## Recording a Transaction

Use `scripts/record.py`:

```bash
python3 scripts/record.py \
  --date 2026-05-01 \
  --place "セブンイレブン" \
  --item "コーヒーとおにぎり" \
  --amount 450 \
  --currency JPY \
  --category 食費 \
  --payment 現金 \
  --business 私用
```

### Required Fields
- `--date` (YYYY-MM-DD)
- `--place` (store/location name)
- `--item` (purchase description)
- `--amount` (number)
- `--category` (from ⚙️ 設定 sheet)
- `--payment` (from ⚙️ 設定 sheet)

### Optional Fields
- `--currency` (default: JPY)
- `--business` (default: 私用) — 私用/個人事業主/法人(合同会社)/正社員(会社名)
- `--expense-type` (default: 私用) — 事業/私用/按分
- `--settlement` (default: 不要) — 不要/申請前/申請中/精算済
- `--project` (project name)
- `--note` (free text)

## Querying Transactions

Use `scripts/query.py`:

```bash
# All transactions this month
python3 scripts/query.py --month 2026-05

# By category
python3 scripts/query.py --category 食費

# Aggregate by category
python3 scripts/query.py --month 2026-05 --aggregate category

# Search by place
python3 scripts/query.py --place "セブン"

# JSON output
python3 scripts/query.py --month 2026-05 --json
```

## Monthly Reports

Use `scripts/report.py`:

```bash
python3 scripts/report.py --month 2026-05
python3 scripts/report.py --month 2026-05 --business 個人事業主
python3 scripts/report.py --month 2026-05 --json
```

## Exchange Rates

Use `scripts/exchange_rate.py`:

```bash
python3 scripts/exchange_rate.py
python3 scripts/exchange_rate.py --currency USD CNY
```

## AI Workflow

When a user sends an expense screenshot or message:

1. **Fetch SCHEMA.md** from GitHub (mandatory)
2. **Read ⚙️ 設定 sheet** for valid categories/payment methods
3. Parse the expense details from the message/image
4. Run `scripts/record.py` with extracted data
5. Confirm the recording with JPY equivalent

## Master Data

All selectable values live in `⚙️ 設定` sheet. Always read them from the sheet before validating — never hardcode.

## Schema Validation

```bash
python3 tests/test_schema.py
```

Checks:
- All required columns present
- Master data consistency
- Sheet structure integrity
