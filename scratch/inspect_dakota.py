import sys, json, datetime
sys.stdout.reconfigure(encoding='utf-8')
from bs4 import BeautifulSoup

with open('raw_html/dakota_jazz_club.html', 'rb') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

scripts = soup.find_all('script', type='application/ld+json')
all_events = []
for s in scripts:
    try:
        data = json.loads(s.string)
        items = data if isinstance(data, list) else data.get('@graph', [data])
        for item in items:
            if item.get('@type') == 'Event':
                all_events.append(item)
    except:
        pass

print(f'Total JSON-LD events: {len(all_events)}')

# Date range
dates = []
for ev in all_events:
    sd = ev.get('startDate', '')
    if sd:
        dates.append(sd[:10])

dates.sort()
print(f'Earliest: {dates[0] if dates else "none"}')
print(f'Latest:   {dates[-1] if dates else "none"}')

# Show last 5 events
print('\nLast 5 events:')
for ev in all_events[-5:]:
    print(f"  {ev.get('startDate','')[:10]}  {ev.get('name')}")

# Count events in the 120-day window from 2026-06-20
target_start = datetime.date(2026, 6, 20)
target_end = target_start + datetime.timedelta(days=120)
in_window = [e for e in all_events if target_start.isoformat() <= e.get('startDate','')[:10] <= target_end.isoformat()]
print(f'\nEvents in 120-day window ({target_start} to {target_end}): {len(in_window)}')

# Check eventStatus values
statuses = set(ev.get('eventStatus','') for ev in all_events)
print(f'\nEvent statuses: {statuses}')

# Check for any pagination links
pag = soup.find(class_=lambda c: c and 'pagination' in ' '.join(c).lower())
print(f'\nPagination element: {pag.name if pag else "None"}')
next_link = soup.find('a', rel='next')
print(f'Next page link: {next_link}')
