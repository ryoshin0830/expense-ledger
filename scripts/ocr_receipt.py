#!/usr/bin/env python3
"""ocr_receipt.py — Analyze receipt/card-notification images via OpenAI GPT-4o."""

import argparse
import base64
import json
import os
import sys
import urllib.request

CONFIG_PATH = os.path.expanduser("~/.openclaw/openclaw.json")


def get_api_key():
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
    return cfg["env"]["vars"]["OPENAI_API_KEY"]


def analyze_image(image_path, api_key):
    """Send image to GPT-4o for receipt analysis."""
    # Detect MIME type
    ext = image_path.lower().rsplit(".", 1)[-1]
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else "image/png"

    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()

    body = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "この画像は支払いのレシートまたはカード利用通知です。"
                            "以下の情報を正確に抽出し、JSON形式で返してください：\n"
                            "{\n"
                            '  "date": "YYYY-MM-DD または 不明",\n'
                            '  "time": "HH:MM または 不明",\n'
                            '  "store": "店舗名（正確に）",\n'
                            '  "items": [{"name": "商品名", "price": 数字}],\n'
                            '  "total": 合計金額（数字のみ）,'
                            '  "currency": "JPY/USD/CNY等",\n'
                            '  "payment": "現金/クレジット/電子マネー等（不明なら不明）",\n'
                            '  "note": "画像の種類（レシート/カード通知/その他）や特記事項"\n'
                            "}\n"
                            "数字は画像から一字一句正確に読み取ってください。"
                            "推測せず、読めない場合は「不明」としてください。"
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
        "max_tokens": 1000,
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
        if content.endswith("```"):
            content = content.rsplit("\n", 1)[0]
        if content.startswith("json"):
            content = content.split("\n", 1)[1]

    return json.loads(content)


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
    result = analyze_image(args.image, api_key)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"🏪 {result.get('store', '不明')}")
        print(f"📅 {result.get('date', '不明')} {result.get('time', '')}")
        if result.get("items"):
            for item in result["items"]:
                print(f"   {item['name']}: ¥{item['price']:,}")
        total = result.get("total", 0)
        currency = result.get("currency", "JPY")
        print(f"💰 合計: {currency} {total:,.0f}")
        print(f"💳 支払方法: {result.get('payment', '不明')}")
        if result.get("note"):
            print(f"📝 {result['note']}")


if __name__ == "__main__":
    main()
