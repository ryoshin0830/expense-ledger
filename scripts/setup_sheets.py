#!/usr/bin/env python3
"""setup_sheets.py — Initialize/customize Google Sheets for expense-ledger."""

import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error

DEFAULT_SHEET_ID = "1Wl3T8dh70Cb9mCH65igZetBdNJpnUUHiumELlyeulAc"

HEADERS = [
    "id", "日付", "場所", "品目", "金額", "通貨", "JPY換算", "為替レート",
    "支払方法", "カテゴリ", "事業区分", "経費区分", "精算状態",
    "プロジェクト", "備考", "作成日時", "収支"
]


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
        return json.loads(resp.read()) if resp.status != 204 else None
    except urllib.error.HTTPError as e:
        print(f"API Error: {e.code} - {e.read().decode()[:300]}", file=sys.stderr)
        raise


def main():
    parser = argparse.ArgumentParser(description="Setup/customize expense-ledger Google Sheets")
    parser.add_argument("--spreadsheet-id", default=DEFAULT_SHEET_ID, help="Google Sheets spreadsheet ID")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--init-headers", action="store_true", help="Initialize header row on 取引記録 sheet")
    args = parser.parse_args()

    token = get_token()

    # Get sheet metadata
    meta = sheets_api(token, args.spreadsheet_id, "")
    sheets = {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta["sheets"]}
    print(f"Connected to: {meta['properties']['title']}")
    print(f"URL: https://docs.google.com/spreadsheets/d/{args.spreadsheet_id}/edit")
    print(f"Sheets: {list(sheets.keys())}")

    if args.init_headers:
        range_enc = urllib.parse.quote("取引記録!A1:Q1")
        body = {"values": [HEADERS]}
        if args.dry_run:
            print(f"\n[DRY RUN] Would write headers: {HEADERS}")
        else:
            sheets_api(token, args.spreadsheet_id,
                       f"/values/{range_enc}?valueInputOption=USER_ENTERED",
                       method="PUT", body=body)
            print(f"\n✅ Header row initialized with {len(HEADERS)} columns including 収支")

    print("\n✅ Setup complete. Sheet is ready for use.")


if __name__ == "__main__":
    main()
