import urllib.request
import re

url = "https://www.targetcenter.com/events"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req) as response:
        raw_data = response.read()
        import gzip
        if raw_data.startswith(b'\x1f\x8b'):
            print("Response is gzip compressed. Decompressing...")
            raw_data = gzip.decompress(raw_data)
        html = raw_data.decode('utf-8', errors='ignore')
    print(f"Successfully fetched {len(html)} bytes")
    
    # Save raw html
    import os
    os.makedirs("raw_html", exist_ok=True)
    with open("raw_html/target_center_events.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Saved to raw_html/target_center_events.html")

    # Search for common class indicators
    print("\n--- Searching for event markup tags ---")
    for term in ["class=\"event", "class=\"list", "event-card", "item", "title", "date"]:
        matches = [m.start() for m in re.finditer(re.escape(term), html)]
        print(f"Occurrences of '{term}': {len(matches)}")
        for m in matches[:2]:
            print(f"  snippet at {m}: {html[max(0, m-50):min(len(html), m+150)]}")

except Exception as e:
    print(f"Error: {e}")
