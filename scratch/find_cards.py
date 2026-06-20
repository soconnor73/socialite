from bs4 import BeautifulSoup

with open("raw_html/visit_stpaul.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

wl = soup.find(class_='card__website')
if wl:
    partner_name = wl.find('a').get('data-dms-partner-name') if wl.find('a') else "No Name"
    print(f"Tracing parents for website link of '{partner_name}':")
    curr = wl
    for i in range(6):
        if not curr:
            break
        print(f"Level {i}: Tag={curr.name} | Classes={curr.get('class')} | ID={curr.get('id')}")
        curr = curr.parent
else:
    print("No card__website link found.")
