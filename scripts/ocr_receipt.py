#!/usr/bin/env python3
"""ocr_receipt.py — Analyze receipt/card-notification images via OpenAI GPT-4o."""

import argparse
import base64
import json
import os
import sys
import urllib.request

def get_api_key():
    return os.environ["OPENAI_API_KEY"]


def analyze_image(image_path, api_key):
    """Send image to GPT-4o for receipt analysis."""
    # Detect MIME type
    ext = image_path.lower().rsplit(".", 1)[-1]
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else "image/png"

    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()

    body = {
        "model": "gpt-5.4-mini",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "この画像は支払いのレシート、またはカード/決済アプリの取引一覧通知です。\n"
                            "\n"
                            "【最重要】画像内に複数の取引が表示されている場合、"
                            "すべての取引を漏れなく抽出してください。"
                            "カード通知や決済アプリのスクリーンショットでは、"
                            "1枚の画像に複数の取引履歴がリスト表示されていることがよくあります。\n"
                            "\n"
                            "各取引を以下のJSON配列形式で返してください：\n"
                            "[\n"
                            "  {\n"
                            '    "date": "YYYY-MM-DD または 不明",\n'
                            '    "time": "HH:MM または 不明",\n'
                            '    "store": "店舗名（正確に）",\n'
                            '    "items": [{"name": "商品名", "price": 数字}],\n'
                            '    "total": 合計金額（数字のみ）,\n'
                            '    "currency": "JPY/USD/CNY等",\n'
                            '    "payment": "現金/クレジット/電子マネー等（不明なら不明）",\n'
                            '    "note": "画像の種類（レシート/カード通知/その他）や特記事項"\n'
                            "  }\n"
                            "]\n"
                            "\n"
                            "数字は画像から一字一句正確に読み取ってください。"
                            "推測せず、読めない場合は「不明」としてください。"
                            "画面に表示されている取引は、小さくても、スクロールの途中でも、すべて抽出してください。"
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime};base64,{img_b64}",
                            "detail": "high",
                        },
                    },
                ],
            }
        ],
        "max_completion_tokens": 1000,
        "temperature": 0,
    }

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    resp = json.loads(urllib.request.urlopen(req).read())
    content = resp["choices"][0]["message"]["content"]

    # Extract JSON from response (strip markdown code fences if present)
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        if content.rstrip().endswith("```"):
            content = content.rsplit("\n", 1)[0]
        else:
            content = content.rstrip("`")
        if content.startswith("json"):
            content = content.split("\n", 1)[1]

    result = json.loads(content)
    # Normalize: always return a list of transactions
    if isinstance(result, dict):
        result = [result]
    return result


def main():
    parser = argparse.ArgumentParser(description="Analyze receipt images via OpenAI GPT-4o")
    parser.add_argument("image", help="Path to receipt/card-notification image")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--summary", action="store_true", help="Output human-readable summary")
    args = parser.parse_args()

    if not os.path.exists(args.image):
        print(f"File not found: {args.image}", file=sys.stderr)
        sys.exit(1)

    api_key = get_api_key()
    transactions = analyze_image(args.image, api_key)

    if args.json:
        print(json.dumps(transactions, indent=2, ensure_ascii=False))
    else:
        print(f"📊 Found {len(transactions)} transaction(s):")
        for i, txn in enumerate(transactions, 1):
            print(f"\n--- Transaction {i} ---")
            print(f"🏪 {txn.get('store', '不明')}")
            print(f"📅 {txn.get('date', '不明')} {txn.get('time', '')}")
            if txn.get("items"):
                for item in txn["items"]:
                    print(f"   {item['name']}: ¥{item['price']:,}")
            total = txn.get("total", 0)
            currency = txn.get("currency", "JPY")
            print(f"💰 合計: {currency} {total:,.0f}")
            print(f"💳 支払方法: {txn.get('payment', '不明')}")
            if txn.get("note"):
                print(f"📝 {txn['note']}")


if __name__ == "__main__":
    main()
