import sys, re, datetime
sys.stdout.reconfigure(encoding='utf-8')
from bs4 import BeautifulSoup

with open('raw_html/berlin_jazz_club.html', 'rb') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

eventlist = soup.find(class_='eventlist--upcoming')
events = eventlist.find_all('article', class_='eventlist-event') if eventlist else []
print(f'Total events: {len(events)}')

dates = []
for ev in events:
    # Start date from <time class="event-date" datetime="YYYY-MM-DD">
    t = ev.find('time', class_='event-date')
    if t:
        dates.append(t.get('datetime', '')[:10])

dates.sort()
print(f'Date range: {dates[0] if dates else "?"} to {dates[-1] if dates else "?"}')

# Show multi-day events
for ev in events:
    classes = ev.get('class', [])
    if 'eventlist-event--multiday' in classes:
        title_a = ev.find('a', class_='eventlist-title-link')
        title = title_a.get_text(strip=True) if title_a else '?'
        # Look for end date tag
        end_div = ev.find(class_='eventlist-datetag-enddate')
        print(f'\nMulti-day: {title}')
        print(f'  end-date div: {end_div}')
        # Check all time elements
        for t in ev.find_all('time'):
            print(f'  <time class={t.get("class")} datetime={t.get("datetime")}> {t.get_text(strip=True)[:40]}')

# In-window count
target_start = datetime.date(2026, 6, 20)
target_end = target_start + datetime.timedelta(days=120)
in_window = [d for d in dates if target_start.isoformat() <= d <= target_end.isoformat()]
print(f'\nEvents in window: {len(in_window)} of {len(dates)}')
print(f'Last event date: {dates[-1] if dates else "?"}')
