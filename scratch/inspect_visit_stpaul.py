from bs4 import BeautifulSoup

with open("raw_html/visit_stpaul.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

# Search for classes containing event, card, list, item, row
nodes = soup.find_all(class_=lambda c: c and any(x in c for x in ['event', 'item', 'card', 'row', 'entry']))
print(f"Found {len(nodes)} potential event elements.")

# Also let's search for event links
event_links = soup.find_all('a', href=lambda h: h and ('/event/' in h or '/events/' in h))
print(f"Found {len(event_links)} event links:")
seen = set()
for idx, a in enumerate(event_links[:30]):
    href = a.get('href')
    if href in seen:
        continue
    seen.add(href)
    text = " ".join(a.get_text().split())[:80]
    print(f"[{idx+1}] Link: {href} | Text: '{text}' | Parent: {a.parent.name} | Parent Classes: {a.parent.get('class')}")
