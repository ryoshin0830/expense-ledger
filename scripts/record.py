#!/usr/bin/env python3
"""record.py — Record a transaction to expense-ledger Google Sheets."""

import argparse
import json
import os
import sys
import uuid
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone

CONFIG_PATH = os.path.expanduser("~/.hermes/auth.json")
DEFAULT_SHEET_ID = "1Wl3T8dh70Cb9mCH65igZetBdNJpnUUHiumELlyeulAc"


def get_token():
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
    data = urllib.parse.urlencode({
        "client_id": cfg["GOOGLE_CLIENT_ID"],
        "client_secret": cfg["GOOGLE_CLIENT_SECRET"],
        "refresh_token": cfg["GOOGLE_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return json.loads(urllib.request.urlopen(req).read())["access_token"]


def sheets_api(token, spreadsheet_id, path, method="GET", body=None):
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}{path}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read()) if resp.status != 204 else {}
    except urllib.error.HTTPError as e:
        print(f"API Error: {e.code} - {e.read().decode()[:300]}", file=sys.stderr)
        raise


def get_exchange_rate(currency):
    """Fetch exchange rate to JPY."""
    if currency == "JPY":
        return 1.0
    try:
        url = f"https://api.frankfurter.app/latest?from={currency}&to=JPY"
        resp = urllib.request.urlopen(url, timeout=10)
        data = json.loads(resp.read())
        return data["rates"]["JPY"]
    except Exception:
        # Fallback rates (approximate)
        fallbacks = {"USD": 150.0, "CNY": 20.5, "KRW": 0.11, "EUR": 162.0, "TWD": 4.6, "HKD": 19.2, "GBP": 190.0, "AUD": 98.0, "SGD": 112.0}
        return fallbacks.get(currency, 1.0)


def main():
    parser = argparse.ArgumentParser(description="Record an expense transaction")
    parser.add_argument("--spreadsheet-id", default=DEFAULT_SHEET_ID)
    parser.add_argument("--date", required=True, help="Date (YYYY-MM-DD)")
    parser.add_argument("--place", required=True, help="Store/location name")
    parser.add_argument("--item", required=True, help="Item description")
    parser.add_argument("--amount", type=float, required=True, help="Amount in original currency")
    parser.add_argument("--currency", default="JPY", help="Currency code (default: JPY)")
    parser.add_argument("--category", required=True, help="Expense category")
    parser.add_argument("--payment", required=True, help="Payment method")
    parser.add_argument("--business", default="私用", help="Business category (default: 私用)")
    parser.add_argument("--expense-type", default="私用", help="Expense type (default: 私用)")
    parser.add_argument("--settlement", default="不要", help="Settlement status (default: 不要)")
    parser.add_argument("--project", default="", help="Project name")
    parser.add_argument("--note", default="", help="Notes")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    # Fetch exchange rate
    rate = get_exchange_rate(args.currency)

    # Generate UUID and timestamp
    record_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Build row (JPY換算 is a formula, not a value)
    row = [
        record_id,
        args.date,
        args.place,
        args.item,
        args.amount,
        args.currency,
        "",  # JPY換算 — formula set by sheet template
        rate,
        args.payment,
        args.category,
        args.business,
        args.expense_type,
        args.settlement,
        args.project,
        args.note,
        timestamp,
    ]

    # Append to sheet
    token = get_token()
    range_enc = urllib.parse.quote("取引記録!A:P")
    body = {"values": [row]}
    result = sheets_api(token, args.spreadsheet_id, f"/values/{range_enc}:append?valueInputOption=USER_ENTERED&insertDataOption=INSERT_ROWS",
                        method="POST", body=body)

    if args.json:
        output = {
            "id": record_id,
            "date": args.date,
            "place": args.place,
            "item": args.item,
            "amount": args.amount,
            "currency": args.currency,
            "rate": rate,
            "jpy_equivalent": round(args.amount * rate, 2),
            "category": args.category,
            "business": args.business,
            "settlement": args.settlement,
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        jpy_eq = round(args.amount * rate, 2)
        print(f"✅ Recorded: {args.date} | {args.place} | {args.item}")
        print(f"   {args.amount} {args.currency} (≈¥{jpy_eq:,.0f}) | {args.category} | {args.payment}")
        print(f"   ID: {record_id}")


if __name__ == "__main__":
    main()
