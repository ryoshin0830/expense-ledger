#!/usr/bin/env python3
"""query.py — Search & aggregate expense-ledger transactions."""

import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error

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


def main():
    parser = argparse.ArgumentParser(description="Search & aggregate expense-ledger transactions")
    parser.add_argument("--spreadsheet-id", default=DEFAULT_SHEET_ID)
    parser.add_argument("--month", help="Filter by month (YYYY-MM)")
    parser.add_argument("--category", help="Filter by category")
    parser.add_argument("--business", help="Filter by business type")
    parser.add_argument("--currency", help="Filter by currency")
    parser.add_argument("--place", help="Filter by place (partial match)")
    parser.add_argument("--item", help="Filter by item (partial match)")
    parser.add_argument("--settlement", help="Filter by settlement status")
    parser.add_argument("--project", help="Filter by project")
    parser.add_argument("--direction", choices=["支出", "収入"], help="Filter by transaction direction")
    parser.add_argument("--aggregate", choices=["category", "currency", "business", "month"], help="Aggregate by field")
    parser.add_argument("--limit", type=int, default=100000, help="Max results (default: 100000)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    transactions = read_all_transactions(args.spreadsheet_id)

    # Apply filters
    filtered = transactions
    if args.month:
        filtered = [t for t in filtered if t["日付"].startswith(args.month)]
    if args.category:
        filtered = [t for t in filtered if args.category in t["カテゴリ"]]
    if args.business:
        filtered = [t for t in filtered if args.business in t["事業区分"]]
    if args.currency:
        filtered = [t for t in filtered if t["通貨"] == args.currency]
    if args.place:
        filtered = [t for t in filtered if args.place.lower() in t["場所"].lower()]
    if args.item:
        filtered = [t for t in filtered if args.item.lower() in t["品目"].lower()]
    if args.settlement:
        filtered = [t for t in filtered if t["精算状態"] == args.settlement]
    if args.project:
        filtered = [t for t in filtered if args.project.lower() in (t.get("プロジェクト", "") or "").lower()]
    if args.direction:
        filtered = [t for t in filtered if t.get("収支", "支出") == args.direction]

    if args.aggregate:
        agg = {}
        for t in filtered:
            key = t.get({"category": "カテゴリ", "currency": "通貨", "business": "事業区分", "month": "日付"}[args.aggregate], "")
            if args.aggregate == "month":
                key = key[:7] if key else ""
            if key not in agg:
                agg[key] = {"count": 0, "total": 0}
            try:
                amt = float(t["金額"])
            except (ValueError, TypeError):
                amt = 0
            agg[key]["count"] += 1
            agg[key]["total"] += amt

        if args.json:
            print(json.dumps(agg, indent=2, ensure_ascii=False))
        else:
            print(f"{'Group':20s} | {'Count':>6s} | {'Total':>12s}")
            print("-" * 45)
            for k, v in sorted(agg.items(), key=lambda x: x[1]["total"], reverse=True):
                print(f"{k:20s} | {v['count']:6d} | {v['total']:12,.2f}")
    else:
        filtered = filtered[:args.limit]
        if args.json:
            print(json.dumps(filtered, indent=2, ensure_ascii=False))
        else:
            print(f"Found {len(filtered)} transactions:\n")
            for t in filtered:
                print(f"  {t['日付']} | {t['場所']:20s} | {t['品目']:20s} | {t['金額']:>8s} {t['通貨']} | {t['カテゴリ']}")


if __name__ == "__main__":
    main()
