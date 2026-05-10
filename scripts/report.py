#!/usr/bin/env python3
"""report.py — Generate monthly/project expense reports."""

import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime
from collections import defaultdict

DEFAULT_SHEET_ID = "1Wl3T8dh70Cb9mCH65igZetBdNJpnUUHiumELlyeulAc"


def get_token():
    data = urllib.parse.urlencode({
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
        "refresh_token": os.environ["GOOGLE_REFRESH_TOKEN"],
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


def read_all_transactions(spreadsheet_id):
    token = get_token()
    range_enc = urllib.parse.quote("取引記録!A2:Q")
    result = sheets_api(token, spreadsheet_id, f"/values/{range_enc}")
    rows = result.get("values", [])

    headers = [
        "id", "日付", "場所", "品目", "金額", "通貨", "JPY換算", "為替レート",
        "支払方法", "カテゴリ", "事業区分", "経費区分", "精算状態",
        "プロジェクト", "備考", "作成日時", "収支"
    ]

    transactions = []
    for row in rows:
        if not row or not row[0]:
            continue
        entry = {}
        for i, h in enumerate(headers):
            entry[h] = row[i] if i < len(row) else ""
        transactions.append(entry)
    return transactions


def format_jpy(val):
    """Format as JPY with commas."""
    return f"¥{val:,.0f}"


def main():
    parser = argparse.ArgumentParser(description="Generate expense reports")
    parser.add_argument("--spreadsheet-id", default=DEFAULT_SHEET_ID)
    parser.add_argument("--month", help="Month to report (YYYY-MM)")
    parser.add_argument("--project", help="Filter by project")
    parser.add_argument("--business", help="Filter by business type")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    transactions = read_all_transactions(args.spreadsheet_id)

    if not transactions:
        print("No transactions found.")
        return

    # Filters
    if args.month:
        transactions = [t for t in transactions if t["日付"].startswith(args.month)]
    if args.project:
        transactions = [t for t in transactions if args.project.lower() in (t.get("プロジェクト", "") or "").lower()]
    if args.business:
        transactions = [t for t in transactions if t["事業区分"] == args.business]

    if not transactions:
        print(f"No transactions match filters.")
        return

    # Compute aggregates
    total_expense_jpy = 0
    total_income_jpy = 0
    by_category = defaultdict(float)
    by_business = defaultdict(float)
    by_currency = defaultdict(lambda: {"count": 0, "total": 0})
    count_private = 0
    count_business = 0
    count_income = 0
    count_expense = 0

    for t in transactions:
        direction = t.get("収支", "支出")
        # Use JPY換算 if available, else compute
        try:
            jpy_val = float(t["JPY換算"])
        except (ValueError, TypeError, KeyError):
            try:
                amt = float(t["金額"])
                rate = float(t.get("為替レート", 1) or 1)
                jpy_val = amt * rate
            except (ValueError, TypeError):
                jpy_val = 0

        if direction == "収入":
            total_income_jpy += jpy_val
            count_income += 1
        else:
            total_expense_jpy += jpy_val
            count_expense += 1
            by_category[t.get("カテゴリ", "不明")] += jpy_val
            by_business[t.get("事業区分", "私用")] += jpy_val
            ccy = t.get("通貨", "JPY")
            by_currency[ccy]["count"] += 1
            try:
                by_currency[ccy]["total"] += float(t["金額"])
            except (ValueError, TypeError):
                pass
            if t.get("経費区分") == "事業":
                count_business += 1
            elif t.get("経費区分") == "私用":
                count_private += 1

    date_range = f"{transactions[0]['日付']} ~ {transactions[-1]['日付']}" if len(transactions) > 1 else transactions[0]["日付"]

    if args.json:
        report = {
            "date_range": date_range,
            "transaction_count": len(transactions),
            "expense_count": count_expense,
            "income_count": count_income,
            "total_expense_jpy": round(total_expense_jpy, 2),
            "total_income_jpy": round(total_income_jpy, 2),
            "net_jpy": round(total_income_jpy - total_expense_jpy, 2),
            "by_category": dict(by_category),
            "by_business": dict(by_business),
            "by_currency": {k: dict(v) for k, v in by_currency.items()},
            "private_count": count_private,
            "business_count": count_business,
        }
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"\n{'='*60}")
        title = f"Expense Report"
        if args.month:
            title += f" — {args.month}"
        print(f"  {title}")
        print(f"{'='*60}")
        print(f"  Period: {date_range}")
        print(f"  Transactions: {len(transactions)} (支出: {count_expense}, 収入: {count_income})")
        if count_income > 0:
            print(f"  Income: +{format_jpy(total_income_jpy)}")
        print(f"  Expense: -{format_jpy(total_expense_jpy)}")
        net = total_income_jpy - total_expense_jpy
        net_sign = "+" if net >= 0 else ""
        print(f"  Net: {net_sign}{format_jpy(net)}")
        print()
        print(f"  --- By Category (Expenses Only) ---")
        for cat, val in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
            pct = val / total_expense_jpy * 100 if total_expense_jpy > 0 else 0
            print(f"  {cat:12s}: {format_jpy(val):>12s} ({pct:5.1f}%)")
        print()
        print(f"  --- By Business Type ---")
        for biz, val in sorted(by_business.items(), key=lambda x: x[1], reverse=True):
            pct = val / total_expense_jpy * 100 if total_expense_jpy > 0 else 0
            print(f"  {biz:12s}: {format_jpy(val):>12s} ({pct:5.1f}%)")
        print()
        print(f"  --- By Currency ---")
        for ccy, info in sorted(by_currency.items()):
            print(f"  {ccy:6s}: {info['count']:4d} txns, {info['total']:12,.2f}")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
