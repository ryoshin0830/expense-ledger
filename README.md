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
