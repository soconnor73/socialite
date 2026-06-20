import sys
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

with open("raw_html/visit_stpaul.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

cards = soup.find_all('article', class_='card')
# Find the first card with class 'card--info'
target_card = None
for card in cards:
    if 'card--info' in card.get('class'):
        target_card = card
        break

if target_card:
    print(target_card.prettify())
else:
    print("No card--info found.")
