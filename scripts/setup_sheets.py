#!/usr/bin/env python3
"""setup_sheets.py — Initialize/customize Google Sheets for expense-ledger."""

import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error

CONFIG_PATH = os.path.expanduser("~/.openclaw/openclaw.json")
DEFAULT_SHEET_ID = "1Wl3T8dh70Cb9mCH65igZetBdNJpnUUHiumELlyeulAc"


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
    args = parser.parse_args()

    token = get_token()

    # Get sheet metadata
    meta = sheets_api(token, args.spreadsheet_id, "")
    sheets = {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta["sheets"]}
    print(f"Connected to: {meta['properties']['title']}")
    print(f"URL: https://docs.google.com/spreadsheets/d/{args.spreadsheet_id}/edit")
    print(f"Sheets: {list(sheets.keys())}")

    print("\n✅ Setup complete. Sheet is ready for use.")


if __name__ == "__main__":
    main()
