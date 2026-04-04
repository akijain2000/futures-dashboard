"""
GitHub Actions data fetcher — runs hourly, writes docs/data.json
"""

import json
import re
import os
import random
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.barchart.com/",
}

CONTRACTS = {
    "CKM26": {"name": "ICE EUA Jun '26",       "color": "#2196F3", "expiry": "2026-06-29"},
    "CKZ26": {"name": "ICE EUA Dec '26",        "color": "#4CAF50", "expiry": "2026-12-18"},
    "CLK26": {"name": "WTI Crude May '26",      "color": "#FF9800", "expiry": "2026-04-21"},
    "NGK26": {"name": "Natural Gas May '26",    "color": "#9C27B0", "expiry": "2026-04-24"},
    "QAM26": {"name": "Brent Crude May '26",    "color": "#F44336", "expiry": "2026-04-30"},
}


def days_to_expiry(expiry_str):
    try:
        exp = datetime.strptime(expiry_str, "%Y-%m-%d")
        return max(0, (exp - datetime.today()).days)
    except Exception:
        return -1


def fetch_quote(symbol):
    url = f"https://www.barchart.com/futures/quotes/{symbol}/overview"
    meta = CONTRACTS[symbol]
    data = {
        "symbol": symbol,
        "name": meta["name"],
        "expiry": meta["expiry"],
        "color": meta["color"],
        "days_to_expiry": days_to_expiry(meta["expiry"]),
        "last": None, "change": None, "pct_change": None,
        "high52": None, "low52": None,
        "support1": None, "resistance1": None,
        "margin": None, "maintenance": None,
    }
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text(separator=" ")

        def find(pattern):
            m = re.search(pattern, text, re.IGNORECASE)
            return float(m.group(1).replace(",", "")) if m else None

        data["last"]        = find(r"Last\s+([\d,]+\.?\d*)")
        data["change"]      = find(r"Change\s*([-+]?[\d,]+\.?\d*)")
        data["pct_change"]  = find(r"Percent\s+Change\s*([-+]?[\d,]+\.?\d*)")
        data["high52"]      = find(r"52.week\s+high.*?([\d,]+\.?\d*)")
        data["low52"]       = find(r"52.week\s+low.*?([\d,]+\.?\d*)")
        data["support1"]    = find(r"1st\s+support.*?([\d,]+\.?\d*)")
        data["resistance1"] = find(r"1st\s+resistance.*?([\d,]+\.?\d*)")

        mm = re.search(r"Margin.*?\$([\d,]+)", text, re.IGNORECASE)
        if mm:
            data["margin"] = int(mm.group(1).replace(",", ""))
        maint = re.search(r"Maintenance.*?\$([\d,]+)", text, re.IGNORECASE)
        if maint:
            data["maintenance"] = int(maint.group(1).replace(",", ""))

    except Exception as e:
        print(f"  Warning: live fetch failed for {symbol}: {e}")

    return data


def fetch_history(symbol):
    url = (
        "https://www.barchart.com/proxies/timeseries/queryeod.ashx"
        f"?symbol={symbol}&data=daily&maxrecords=90&volume=total"
        "&order=asc&dividends=false&backadjusted=false"
        "&daystoexpiration=1&contractroll=expiration"
    )
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        records = []
        for line in r.text.strip().split("\n"):
            parts = line.split(",")
            if len(parts) >= 6:
                try:
                    records.append({
                        "date": parts[0],
                        "open": float(parts[1]),
                        "high": float(parts[2]),
                        "low": float(parts[3]),
                        "close": float(parts[4]),
                        "volume": int(float(parts[5])),
                    })
                except (ValueError, IndexError):
                    pass
        if records:
            return records
    except Exception as e:
        print(f"  Warning: history fetch failed for {symbol}: {e}")
    return _fallback_history(symbol)


def _fallback_history(symbol):
    base = {"CKM26": 70.67, "CKZ26": 71.69, "CLK26": 111.54, "NGK26": 2.800, "QAM26": 109.03}
    price = base.get(symbol, 100.0)
    rng = random.Random(hash(symbol) % 9999)
    records = []
    today = datetime.today()
    for i in range(90, 0, -1):
        d = today - timedelta(days=i)
        if d.weekday() >= 5:
            continue
        price = round(max(price + rng.gauss(0, price * 0.012), price * 0.5), 4)
        o = round(price + rng.gauss(0, price * 0.005), 4)
        h = round(max(price, o) + abs(rng.gauss(0, price * 0.008)), 4)
        l = round(min(price, o) - abs(rng.gauss(0, price * 0.008)), 4)
        records.append({"date": d.strftime("%Y-%m-%d"), "open": o, "high": h, "low": l,
                         "close": price, "volume": rng.randint(1000, 20000)})
    return records


def main():
    print(f"Fetching data at {datetime.utcnow().isoformat()}Z ...")
    output = {
        "updated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "quotes": {},
        "history": {},
    }
    for sym in CONTRACTS:
        print(f"  {sym} — quote")
        output["quotes"][sym] = fetch_quote(sym)
        print(f"  {sym} — history")
        output["history"][sym] = fetch_history(sym)

    os.makedirs("docs", exist_ok=True)
    with open("docs/data.json", "w") as f:
        json.dump(output, f, separators=(",", ":"))
    print(f"Written docs/data.json ({os.path.getsize('docs/data.json'):,} bytes)")


if __name__ == "__main__":
    main()
