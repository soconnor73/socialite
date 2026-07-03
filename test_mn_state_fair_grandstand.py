import datetime
import os
import sys
from parsers.mn_state_fair_grandstand import MNStateFairGrandstandParser

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

filepath = "raw_html/mn_state_fair_grandstand.html"
if not os.path.exists(filepath):
    print(f"Cached file {filepath} not found. Running scrape first...")
    import urllib.request
    import gzip
    url = "https://www.mnstatefair.org/grandstand"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept-Encoding': 'gzip, deflate'
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        content = response.read()
        if response.info().get('Content-Encoding') == 'gzip':
            content = gzip.decompress(content)
        os.makedirs("raw_html", exist_ok=True)
        with open(filepath, "wb") as f:
            f.write(content)

with open(filepath, "rb") as f:
    html = f.read()

parser = MNStateFairGrandstandParser()
shows = parser.parse(html)

print(f"Parsed {len(shows)} shows:")
for show in shows:
    print(f"Date: {show['date']} to {show['end_date']}")
    print(f"Title: {show['title']}")
    print(f"Venue: {show['venue']}")
    print(f"Link: {show['link']}")
    print(f"Support Info: {show['support_raw']}")
    print("-" * 40)
