import urllib.request, gzip, json, sys, datetime, time
sys.stdout.reconfigure(encoding='utf-8')

def fetch(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/html',
        'Accept-Encoding': 'gzip, deflate',
        'X-Requested-With': 'XMLHttpRequest',
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        content = resp.read()
        if resp.info().get('Content-Encoding') == 'gzip':
            content = gzip.decompress(content)
    return content

# Try Tribe REST API endpoints
test_urls = [
    'https://visitduluth.com/wp-json/tribe/events/v1/events?start_date=2026-07-01&end_date=2026-07-31&per_page=50',
    'https://visitduluth.com/wp-json/tribe/events/v1/events?start_date=2026-08-01&end_date=2026-08-31&per_page=50',
    'https://visitduluth.com/wp-json/tribe/events/v1/events?start_date=2026-09-01&end_date=2026-09-30&per_page=50',
    'https://visitduluth.com/wp-json/tribe/events/v1/events?start_date=2026-10-01&end_date=2026-10-18&per_page=50',
]

for url in test_urls:
    try:
        content = fetch(url)
        data = json.loads(content)
        events = data.get('events', [])
        total = data.get('total', '?')
        print(f'\nAPI URL: {url[:80]}')
        print(f'  Total: {total} | Returned: {len(events)}')
        if events:
            print(f'  First: {events[0].get("start_date","")[:10]} | {events[0].get("title","")}')
            print(f'  Last:  {events[-1].get("start_date","")[:10]} | {events[-1].get("title","")}')
    except Exception as e:
        print(f'ERROR: {url[:80]} -> {e}')
    time.sleep(0.3)
