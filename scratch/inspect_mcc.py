import sys, re, datetime
sys.stdout.reconfigure(encoding='utf-8')
from bs4 import BeautifulSoup

with open('raw_html/mpls_convention_center.html', 'rb') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

cards = soup.find_all('article', class_='card')
print(f'Total article.card: {len(cards)}')

# Aria-label date regex (same as Visit Saint Paul)
DATE_RE = re.compile(r'From\s+([A-Za-z]+)\s+(\d+),\s*(\d{4})\s+to\s+([A-Za-z]+)\s+(\d+),\s*(\d{4})', re.IGNORECASE)
MONTH_MAP = {'jan':1,'feb':2,'mar':3,'apr':4,'may':5,'jun':6,'jul':7,'aug':8,'sep':9,'oct':10,'nov':11,'dec':12}

for i, card in enumerate(cards):
    title_el = card.find('h1') or card.find('h2') or card.find('h3')
    title = title_el.get_text(strip=True) if title_el else '?'
    
    link_el = card.find('a', href=True)
    link = link_el['href'] if link_el else ''
    
    cal = card.find(class_='cal-date')
    aria = cal.get('aria-label', '') if cal else ''
    m = DATE_RE.search(aria)
    start_d = end_d = '?'
    if m:
        m1, d1, y1, m2, d2, y2 = m.groups()
        start_d = f'{y1}-{MONTH_MAP.get(m1[:3].lower(),0):02d}-{int(d1):02d}'
        end_d = f'{y2}-{MONTH_MAP.get(m2[:3].lower(),0):02d}-{int(d2):02d}'
    
    print(f'\nCard {i+1}: {title[:70]}')
    print(f'  Dates: {start_d} to {end_d}')
    print(f'  Link: {link[:80]}')

# Check for load-more or API hints in JS
for script in soup.find_all('script'):
    text = script.string or ''
    if 'api' in text.lower() and 'event' in text.lower():
        print(f'\nScript with api+event: {text[:300]}')
        break

# Check for any forms or filter with 'load more' data attributes
load_more = soup.find(class_=lambda c: c and 'load' in ' '.join(c).lower())
print(f'\nLoad more element: {load_more}')
