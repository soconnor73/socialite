import urllib.request, gzip, json, sys, datetime, time, os
sys.stdout.reconfigure(encoding='utf-8')
from bs4 import BeautifulSoup

def fetch(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept-Encoding': 'gzip, deflate',
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        content = resp.read()
        if resp.info().get('Content-Encoding') == 'gzip':
            content = gzip.decompress(content)
    return content

os.makedirs('raw_html', exist_ok=True)

# Try month-based URLs
months = ['2026-06', '2026-07', '2026-08', '2026-09', '2026-10']
for m in months:
    url = f'https://www.croonersmn.com/events/month/{m}/'
    try:
        html = fetch(url)
        soup = BeautifulSoup(html, 'html.parser')
        events = []
        for s in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(s.string or '')
                items = data if isinstance(data, list) else data.get('@graph', [data])
                for item in items:
                    if isinstance(item, dict) and item.get('@type') == 'Event':
                        events.append(item)
            except: pass
        dates = sorted(ev.get('startDate','')[:10] for ev in events)
        print(f'Month {m}: {len(events)} events | {dates[0] if dates else "?"} to {dates[-1] if dates else "?"}')
        # save it
        filepath = f'raw_html/crooners_month_{m}.html'
        with open(filepath, 'wb') as f:
            f.write(html)
        print(f'  Saved {len(html):,} bytes to {filepath}')
    except Exception as e:
        print(f'ERROR {m}: {e}')
    time.sleep(0.5)
