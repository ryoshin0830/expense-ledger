#!/usr/bin/env python3
"""test_schema.py — Validate expense-ledger schema integrity."""

import json
import os
import sys
import urllib.request
import urllib.parse

CONFIG_PATH = os.path.expanduser("~/.openclaw/openclaw.json")
SHEET_ID = "1Wl3T8dh70Cb9mCH65igZetBdNJpnUUHiumELlyeulAc"


def get_token():
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
    env = cfg["env"]["vars"]
    data = urllib.parse.urlencode({
        "client_id": env["GOOGLE_CLIENT_ID"],
        "client_secret": env["GOOGLE_CLIENT_SECRET"],
        "refresh_token": env["GOOGLE_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token", data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return json.loads(urllib.request.urlopen(req).read())["access_token"]


def sheets_api(token, path, body=None):
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}{path}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers)
    return json.loads(urllib.request.urlopen(req).read())


def main():
    token = get_token()
    errors = []

    # Check sheet structure
    meta = sheets_api(token, "")
    sheet_names = {s["properties"]["title"] for s in meta["sheets"]}
    expected_sheets = {"取引記録", "月次サマリー", "ダッシュボード", "検索ビュー", "設定"}
    missing = expected_sheets - sheet_names
    if missing:
        errors.append(f"Missing sheets: {missing}")
    extra = sheet_names - expected_sheets
    if extra:
        print(f"⚠️  Extra sheets: {extra}")

    # Check headers
    headers_resp = sheets_api(token, f"/values/{urllib.parse.quote('取引記録!A1:P1')}")
    headers = headers_resp.get("values", [[]])[0]
    expected_headers = [
        "id", "日付", "場所", "品目", "金額", "通貨", "JPY換算", "為替レート",
        "支払方法", "カテゴリ", "事業区分", "経費区分", "精算状態",
        "プロジェクト", "備考", "作成日時"
    ]
    if headers != expected_headers:
        errors.append(f"Header mismatch:\n  Expected: {expected_headers}\n  Got: {headers}")

    # Check 設定 sheet
    settings_resp = sheets_api(token, f"/values/{urllib.parse.quote('設定!A1:G20')}")
    settings = settings_resp.get("values", [])
    if settings:
        setting_headers = settings[0]
        if "カテゴリ" not in setting_headers:
            errors.append("設定 sheet: missing カテゴリ column")
        if "事業区分" not in setting_headers:
            errors.append("設定 sheet: missing 事業区分 column")
        if "通貨" not in setting_headers:
            errors.append("設定 sheet: missing 通貨 column")

    if errors:
        print(f"\n❌ {len(errors)} validation error(s):\n")
        for e in errors:
            print(f"  • {e}")
        sys.exit(1)
    else:
        print("✅ All schema checks passed")
        print(f"  Sheets: {len(sheet_names)} ({', '.join(sorted(sheet_names))})")
        print(f"  Headers: {len(headers)} columns OK")
        print(f"  Settings: master data present")


if __name__ == "__main__":
    main()
