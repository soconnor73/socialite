import urllib.request
import gzip
import os

url = "https://www.visitsaintpaul.com/events-calendar/"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Encoding': 'gzip, deflate'
}
req = urllib.request.Request(url, headers=headers)
try:
    print(f"Fetching {url}...")
    with urllib.request.urlopen(req) as response:
        html = response.read()
        if response.info().get('Content-Encoding') == 'gzip':
            print("Decoding gzip content...")
            html = gzip.decompress(html)
        os.makedirs("raw_html", exist_ok=True)
        with open("raw_html/visit_stpaul.html", "wb") as f:
            f.write(html)
        print(f"Success! Saved {len(html)} bytes to raw_html/visit_stpaul.html")
except Exception as e:
    print(f"Error: {e}")
