import requests
from datetime import date

dt = date(2025, 6, 20)  # known trading day
url = f"https://nsearchives.nseindia.com/content/indices/ind_close_all_{dt.strftime('%d%m%Y')}.csv"
r = requests.get(url, headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://www.nseindia.com/",
}, timeout=10)

print(f"Status: {r.status_code}")
print(f"Is HTML (blocked): {'<html' in r.text[:200].lower()}")
print(f"First line: {r.text.splitlines()[0] if r.status_code == 200 else 'N/A'}")
