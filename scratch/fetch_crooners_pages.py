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

def get_events(soup):
    events = []
    for s in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(s.string or '')
            items = data if isinstance(data, list) else data.get('@graph', [data])
            for item in items:
                if isinstance(item, dict) and item.get('@type') == 'Event':
                    events.append(item)
        except:
            pass
    return events

target_end = datetime.date(2026, 10, 18)
shortcode = '8da1da53'
os.makedirs('raw_html', exist_ok=True)

for page in range(2, 31):
    url = f'https://www.croonersmn.com/events/list/page/{page}/?shortcode={shortcode}'
    print(f'Fetching page {page}...')
    try:
        html = fetch(url)
    except Exception as e:
        print(f'  Error: {e}')
        break

    filepath = f'raw_html/crooners_page_{page}.html'
    with open(filepath, 'wb') as f:
        f.write(html)

    soup = BeautifulSoup(html, 'html.parser')
    events = get_events(soup)
    dates = sorted(ev.get('startDate', '')[:10] for ev in events)
    first_d = dates[0] if dates else 'none'
    last_d = dates[-1] if dates else 'none'
    print(f'  {len(events)} events | {first_d} to {last_d}')

    if not events:
        print('  No events — stopping.')
        break

    last_date = datetime.date.fromisoformat(last_d) if last_d != 'none' else None
    if last_date and last_date > target_end:
        print(f'  Past target {target_end} — stopping.')
        break

    next_link = soup.find('a', rel=lambda r: r and 'next' in r)
    if not next_link:
        print('  No next page — done.')
        break

    time.sleep(0.5)

print('Finished.')
