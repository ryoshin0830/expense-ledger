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

## ⚠️ CRITICAL: Image Analysis

**DeepSeek V4-Pro is TEXT-ONLY — it cannot see images.** When a user sends a receipt/notification image, NEVER use the `read` or `image` tool with DeepSeek. It will hallucinate numbers.

**Always use OpenAI GPT-5.4-mini (latest multimodal, fast & cheap) for image analysis:**

```bash
python3 scripts/ocr_receipt.py <image_path>
python3 scripts/ocr_receipt.py <image_path> --json  # for programmatic use
```

The script:
1. Sends the image to OpenAI GPT-4o (multimodal, high detail)
2. Extracts: date, time, store, items, prices, total, currency, payment method
3. Returns structured JSON for record.py

## Mandatory Pre-Flight

**Before EVERY operation:**
1. Fetch SCHEMA.md from GitHub: `curl -s https://raw.githubusercontent.com/ryoshin0830/expense-ledger/main/SCHEMA.md`
2. If user sent an image: **always** run `python3 scripts/ocr_receipt.py <image>` first — never interpret images directly

## Workflow for AI

1. **Image received? →** `python3 scripts/ocr_receipt.py <image>` (MANDATORY, use OpenAI)
2. **Fetch SCHEMA.md** from GitHub
3. **Read 設定 sheet** for valid master data values
4. Parse details from OCR output or user message
5. **Fill missing fields by inference** — when OCR can't read 日付/支払方法/カテゴリ etc., infer from context (message time, typical patterns). **Always mark inferred values prominently** in the confirmation message with a clear indicator like ⚠️推測 or 📝推定
6. Run `scripts/record.py` with extracted data
7. Confirm recording — clearly separate **OCR読み取り** (from image) vs **推測** (inferred by AI)

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
