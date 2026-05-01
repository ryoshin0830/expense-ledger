#!/usr/bin/env python3
"""exchange_rate.py — Fetch exchange rates for expense-ledger."""

import argparse
import json
import sys
import urllib.request


def fetch_rates(base="JPY"):
    """Fetch rates from a free API (no key needed).
    Uses frankfurter.app for ECB rates, falls back to open.er-api.com."""
    urls = [
        f"https://api.frankfurter.app/latest?from={base}",
        f"https://open.er-api.com/v6/latest/{base}",
    ]
    for url in urls:
        try:
            resp = urllib.request.urlopen(url, timeout=10)
            data = json.loads(resp.read())
            return data["rates"]
        except Exception as e:
            print(f"  Failed {url}: {e}", file=sys.stderr)
            continue
    raise RuntimeError("All rate providers failed")


def main():
    parser = argparse.ArgumentParser(description="Fetch exchange rates for expense-ledger")
    parser.add_argument("--base", default="JPY", help="Base currency (default: JPY)")
    parser.add_argument("--currency", nargs="*", help="Specific currencies to show")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    rates = fetch_rates(args.base)

    if args.json:
        print(json.dumps(rates, indent=2, ensure_ascii=False))
    else:
        currencies = args.currency if args.currency else ["USD", "CNY", "KRW", "EUR", "TWD"]
        print(f"Exchange rates (base: {args.base}):")
        for ccy in sorted(rates):
            if not args.currency or ccy in args.currency:
                # Invert: if base is JPY, show JPY per unit
                rate = 1 / rates[ccy] if args.base == "JPY" else rates[ccy]
                print(f"  {ccy}: {rate:.4f}")


if __name__ == "__main__":
    main()
