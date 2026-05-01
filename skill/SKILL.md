---
name: expense-ledger
description: Multi-currency expense tracking via Google Sheets. Record, query, and report on transactions — どこで何をいくら何で買ったのか. Use when the user sends expense screenshots (receipts, payment confirmations), mentions spending money, wants to record a transaction, search expenses, or generate monthly reports. Triggers on 記帳, 支出, 経費, expense, receipt, レシート, 領収書, report, レポート, 月次, or any spending/payment recording. Also handles exchange rate lookups and multi-currency conversion to JPY.
---

# Expense Ledger

> **どこで何をいくら何で買ったのか**

Multi-currency expense tracking. GitHub holds schema (single source of truth). Google Sheets stores data. Python scripts do all processing.

## Architecture

```
GitHub: ryoshin0830/expense-ledger  → SCHEMA.md (single source of truth)
Google Sheets: https://docs.google.com/spreadsheets/d/1Wl3T8dh70Cb9mCH65igZetBdNJpnUUHiumELlyeulAc/edit
Python scripts: bundled in scripts/
```

## Mandatory Pre-Flight

**Before EVERY operation, fetch SCHEMA.md from GitHub:**

```bash
curl -s https://raw.githubusercontent.com/ryoshin0830/expense-ledger/main/SCHEMA.md
```

Never rely on memory or cached versions.

## Recording a Transaction

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

### Required
- `--date` (YYYY-MM-DD)
- `--place` (store/location)
- `--item` (description)
- `--amount` (number)
- `--category` (from 設定 sheet)
- `--payment` (from 設定 sheet)

### Optional
- `--currency` (default: JPY)
- `--business` (default: 私用) — 私用/個人事業主/法人(合同会社)/正社員(会社名)
- `--expense-type` (default: 私用) — 事業/私用/按分
- `--settlement` (default: 不要) — 不要/申請前/申請中/精算済
- `--project`
- `--note`
- `--json` (JSON output)

## Querying

```bash
python3 scripts/query.py --month 2026-05
python3 scripts/query.py --category 食費 --aggregate category
python3 scripts/query.py --place "セブン"
python3 scripts/query.py --json
```

## Reports

```bash
python3 scripts/report.py --month 2026-05
python3 scripts/report.py --month 2026-05 --business 個人事業主
```

## Exchange Rates

```bash
python3 scripts/exchange_rate.py
python3 scripts/exchange_rate.py --currency USD CNY
```

## Sheet Setup

```bash
python3 scripts/setup_sheets.py
```

## Workflow for AI

1. **Fetch SCHEMA.md** from GitHub (mandatory)
2. **Read 設定 sheet** for valid master data values
3. Parse expense details from user message/image
4. Run `scripts/record.py` with extracted data
5. Confirm recording with JPY equivalent
