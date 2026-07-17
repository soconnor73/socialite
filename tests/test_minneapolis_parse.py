from bs4 import BeautifulSoup
import re
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

filepath = "minneapolis_debug.html"

with open(filepath, 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

print("Page Title:", soup.title.string if soup.title else "No Title")
print("Total elements:", len(soup.find_all(True)))

classes = set()
for tag in soup.find_all(True):
    if tag.get('class'):
        for c in tag.get('class'):
            classes.add(c)
            
print("\nAll classes containing event/item/show/list/grid/card/page/pagination:")
for c in sorted(list(classes)):
    if any(x in c.lower() for x in ['event', 'item', 'show', 'list', 'grid', 'card', 'page', 'pagination']):
        print("  ", c)

# Let's search for lists or grids that could contain the 12 events
# Let's count elements matching common classes
for c in ['event-card', 'event-item', 'eventItem', 'card', 'grid-item', 'list-item', 'search-result', 'calendar-item']:
    tags = soup.find_all(class_=c)
    if tags:
        print(f"Class '{c}': found {len(tags)} tags")

# Let's print out all divs with event in their class names
event_tags = []
for tag in soup.find_all(True):
    cls = tag.get('class', [])
    if any('event' in c.lower() for c in cls):
        event_tags.append((tag.name, cls, tag.get('id', '')))
        
print(f"\nFound {len(event_tags)} tags with 'event' in class. First 20:")
for name, cls, eid in event_tags[:20]:
    print(f"  <{name} class={cls} id={eid}>")

# Let's look for link hrefs with page numbers to find pagination pattern
print("\nPagination links search:")
links = soup.find_all('a')
for l in links:
    href = l.get('href', '')
    cls = l.get('class', [])
    text = l.get_text(strip=True)
    if 'page' in href.lower() or 'pg' in href.lower() or any('page' in c.lower() for c in cls) or text.isdigit():
        print(f"  Link: href='{href}' class={cls} text='{text}'")
