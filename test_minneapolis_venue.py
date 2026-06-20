from bs4 import BeautifulSoup
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

filepath = "minneapolis_debug.html"

with open(filepath, 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')
cards = soup.find_all('article', class_='card--detail')

# Let's print the entire text of Card 10 (Midsummer Night's Dream, which was Card 14 in previous list)
card = cards[9]
print("--- Text content ---")
print(card.get_text(" | ", strip=True))

print("\n--- Detailed HTML ---")
print(str(card))
