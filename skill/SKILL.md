---
name: expense-ledger
description: Multi-currency expense tracking via Google Sheets. Record, query, and report on transactions — どこで何をいくら何で買ったのか. Use when the user sends expense screenshots (receipts, payment confirmations), WeChat Pay / Alipay Excel exports (.xlsx), mentions spending money, wants to record a transaction, search expenses, or generate monthly reports. Triggers on 記帳, 記録, 支出, 経費, expense, receipt, レシート, 領収書, report, レポート, 月次, or any spending/payment recording. Also handles exchange rate lookups and multi-currency conversion to JPY.
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

1. **Image received? →** `python3 scripts/ocr_receipt.py <image> --json` (MANDATORY, use OpenAI)
2. **Check transaction count** — ocr_receipt.py now returns a JSON array. If it returns more than 1 transaction, you MUST record ALL of them. Never stop at the first one.
3. **Fetch SCHEMA.md** from GitHub
4. **Read 設定 sheet** for valid master data values
5. Parse details from OCR output or user message
6. **Fill missing fields by inference** — when OCR can't read 日付/支払方法/カテゴリ etc., infer from context (message time, typical patterns). **Always mark inferred values prominently** in the confirmation message with a clear indicator like ⚠️推測 or 📝推定
7. Run `scripts/record.py` with extracted data for EACH transaction
8. Confirm recording — clearly separate **📷 OCR読み取り** (from image) vs **⚠️ 推測** (inferred by AI)

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
python3 scripts/query.py --month 2026-05 --json  # programmatic use — always pass --limit 100000 for multi-month exports
python3 scripts/query.py --category 食費 --aggregate category
python3 scripts/query.py --place "セブン"
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

## ⚙️ Config Setup (Google Credentials)

The query/record scripts read Google OAuth credentials from `~/.openclaw/openclaw.json`. This file may not exist by default — the credentials live in `~/.hermes/.env`.

**If scripts fail with `FileNotFoundError: openclaw.json`**, create the config:

```bash
mkdir -p ~/.openclaw
# Extract GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN from ~/.hermes/.env
# and create ~/.openclaw/openclaw.json with env.vars containing all three
```

## Batch Import from Payment Platform Exports

When user sends an Excel/CSV export from WeChat Pay (微信支付) or Alipay:

### Workflow

1. **Parse the file** — use system `python3` via subprocess (NOT execute_code — sandbox lacks openpyxl):
   ```python
   subprocess.run(["/usr/bin/python3", "-c", "..."], ...)
   ```
2. **Fetch SCHEMA.md** from GitHub
3. **Query existing records** for the date range: `python3 scripts/query.py --month YYYY-MM --json`
4. **Deduplicate** — match by `(date, amount, currency)` tuple. If date+amount+currency matches, it's a duplicate.
5. **Present summary** to user — show matched (skip), new expenses, refunded, income. Ask for confirmation before recording.
6. **Record new expenses** via `scripts/record.py` for each non-duplicate expense.
   - For **10+ transactions**: use **2-3 sub-agents** via `delegate_task` to record in parallel (split evenly, ~12-13 per agent). Each sub-agent runs `record.py` sequentially with all commands explicitly listed. This cuts total time from ~4 min to ~2 min.
7. **Verify** — run `query.py --month YYYY-MM --json --limit 100000` to confirm total count = (previous count + new records). If count is off, a sub-agent may have missed some. Check `/subagents log <id>` for errors.

### Handling Special Transaction Types

| Type | 微信支付 Status | Action |
|---|---|---|
| Normal expense | 支付成功 | Record normally |
| Refunded expense | 已退款(¥X) / 已全额退款 | **Skip — do NOT record.** Refunded transactions are excluded. |
| Income (red packet) | 已存入零钱 | **Skip — income is not tracked** (expenses only) |
| Income (group collect) | 已存入零钱 | **Skip — income is not tracked** |
| Income (merchant refund) | 已退款¥X | **Skip — it's a reversal, not new money** |

### Refund Policy (DEFINITIVE)

- **Refunded transactions in payment exports → skip entirely** (do not record)
- **Income of any kind** (red packets, group collections, merchant refunds) → **do not record** (expenses-only tracking)
- **If a previously-recorded transaction gets refunded later → DELETE the original record** (do not modify/amend — delete it)

Memory note: this policy is also stored in agent memory under `expense-ledger返金ポリシー`.

### WeChat Pay Export Format

Columns: 交易时间 | 交易类型 | 交易对方 | 商品 | 收/支 | 金额(元) | 支付方式 | 当前状态 | 交易单号 | 商户单号 | 备注

Payment methods in export: 零钱=WeChat balance, 工商银行储蓄卡(4982)=ICBC debit card

See `references/wechat-pay-export.md` for format details.

## ⚠️ Pitfalls

- **Sandbox Python ≠ system Python**: `execute_code` runs in a sandbox without openpyxl/pandas. Always use `/usr/bin/python3` via subprocess for Excel parsing.
- **Config file location**: Scripts expect `~/.openclaw/openclaw.json`, not `~/.hermes/.env`. Create the file if missing.
- **Refunds in export**: 微信支付 exports include both the original charge AND the refund as separate rows. The charge shows `已退款(¥X)`, the refund shows as an 收入 row. Both are skipped per refund policy.
- **Timestamp timezone**: 微信支付 export times are UTC+08:00 (China time). Convert dates to the date column (YYYY-MM-DD) carefully.
- **query.py default limit**: Older versions default to `--limit 50`. When importing a month with 50+ transactions, always pass `--limit 100000` to get all records. The default was updated in the repo but local copies may be stale.
- **DeepSeek V4-Pro cannot read images**: Never use `read` or `image` tools for receipt OCR — always route through `ocr_receipt.py` which uses OpenAI.
