# expense-ledger

> どこで何をいくら何で買ったのか — Multi-currency expense ledger

**GitHub manages schema (single source of truth). Google Sheets stores data. Python scripts do the processing.**

## Architecture

```
expense-ledger/
├── README.md              ← This file
├── SCHEMA.md              ← ★ Single source of truth (data model)
├── scripts/
│   ├── record.py          ← Record a transaction
│   ├── query.py           ← Search & aggregate
│   ├── report.py          ← Monthly/project reports
│   ├── exchange_rate.py   ← Fetch exchange rates
│   ├── ocr_receipt.py     ← OCR receipt images (GPT-4o)
│   └── setup_sheets.py    ← Initialize Google Sheets
├── skill/
│   └── SKILL.md           ← OpenClaw skill definition
└── tests/
    └── test_schema.py     ← Schema integrity checks
```

## Google Sheets Structure

| Sheet | Purpose |
|---|---|
| 📝 取引記録 | Raw transaction data (all columns) |
| 📊 月次サマリー | Pivot table |
| 📈 ダッシュボード | Charts & KPIs |
| 🔍 検索ビュー | Dynamic FILTER views |
| ⚙️ 設定 | Category/currency/label master data |

## Design Principles

1. **SCHEMA.md is the single source of truth** — AI reads it fresh from GitHub before every operation
2. **All data processing via code** — Python scripts, not AI ad-hoc operations
3. **Master data lives in ⚙️ 設定 sheet** — dynamic, not hardcoded
4. **Testable** — schema integrity checks prevent drift

---

## Authentication Setup

Scripts authenticate to Google Sheets API via OAuth 2.0 refresh token.

Place a JSON file at `~/.openclaw/openclaw.json`:

```json
{
  "env": {
    "vars": {
      "GOOGLE_CLIENT_ID": "xxx.apps.googleusercontent.com",
      "GOOGLE_CLIENT_SECRET": "GOCSPX-xxx",
      "GOOGLE_REFRESH_TOKEN": "1//xxx"
    }
  }
}
```

The scripts (`query.py`, `record.py`, etc.) read this file automatically. No other config needed.

**Google Sheets ID**: `1Wl3T8dh70Cb9mCH65igZetBdNJpnUUHiumELlyeulAc`

---

## Operating Procedures

### Recording Transactions

**From receipts/images** — Use `ocr_receipt.py`:
```bash
python3 scripts/ocr_receipt.py receipt.png --json
python3 scripts/record.py --date ... --place ... --item ... --amount ... --currency ... --category ... --payment ...
```

**From WeChat Pay / Alipay Excel exports** — Parse the `.xlsx` export, match against existing records by (date, amount, currency), then record new ones:
```bash
python3 scripts/query.py --month 2026-05 --json --limit 100000  # check existing
python3 scripts/record.py ...  # record new only
```

### Duplicate Prevention

- Match key: `(date, amount, currency)` — same date + same amount + same currency = duplicate
- **Always query existing records first** before batch-importing Excel data
- `query.py` default limit is 100000 (effectively unlimited) — use `--limit` only if needed

### Refund Policy

- **Refunded transactions → do NOT record** (skip at import time)
- **If a previously-recorded transaction gets refunded later → DELETE the original record** (not modify, delete)
- **Income** (WeChat red packets, group payments, refunds) → do NOT record (expenses only)
- In Excel exports: transactions marked `已退款` or `已全额退款` are skipped

### Data Quality

- OCR readings are marked with `📷 OCR読み取り`
- AI-inferred fields (date, payment method when unclear) are marked with `⚠️推測`
- Always separate image-extracted vs inferred data in confirmation messages

---

## Quick Start

```bash
# Setup
python scripts/setup_sheets.py

# Record a transaction
python scripts/record.py --date 2026-05-01 --place "セブンイレブン" \
  --item "コーヒー" --amount 150 --currency JPY --category 食費 \
  --payment 現金 --business 私用

# Query
python scripts/query.py --month 2026-05 --category 食費

# Monthly report
python scripts/report.py --month 2026-05
```
