import datetime
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from .base import BaseParser


class CoCHCookingClassesParser(BaseParser):
    """
    Parser for Cooks of Crocus Hill upcoming classes.
    URL: https://cooksofcrocushill.com/cooking-classes/upcoming-classes/

    This is a BigCommerce e-commerce page. Events are parsed from product card
    elements (<li class="product">) enclosing an <article class="listItem">.
    """

    def _clean(self, text: str) -> str:
        if not text:
            return ''
        import html as _html
        text = _html.unescape(text)
        text = text.replace('\xa0', ' ').replace('\u2011', '-')
        text = text.replace('\u2018', "'").replace('\u2019', "'")
        text = text.replace('\u201c', '"').replace('\u201d', '"')
        text = text.replace('\u202f', ' ')
        return ' '.join(text.split()).strip()

    def parse(self, html_content: bytes, **kwargs) -> List[Dict[str, Any]]:
        """
        Parses raw HTML content of Cooks of Crocus Hill upcoming classes page.

        Args:
            html_content: Raw HTML of the page.
            **kwargs:     Unused.

        Returns:
            List of structured cooking class events.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        products = soup.find_all('article', class_='listItem')
        shows: List[Dict[str, Any]] = []

        month_map = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
            'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }

        for item in products:
            name_raw = item.get('data-name', '')
            if not name_raw:
                continue

            # Split standard format: Title | Date | Location | Time
            parts = [p.strip() for p in name_raw.split('|')]
            if len(parts) >= 3:
                name = parts[0]
                date_str = parts[1]
                location = parts[2]
                time_str = parts[3] if len(parts) > 3 else ''
            else:
                name = name_raw
                date_str = ''
                location = 'Cooks of Crocus Hill'
                time_str = ''

            name = self._clean(name)
            location = self._clean(location)
            time_str = self._clean(time_str)

            # Resolve link
            link_tag = item.find('a', class_='listItem-figure__link')
            link = link_tag.get('href', '') if link_tag else ''

            # Parse Date
            if date_str:
                date_match = re.match(r'([A-Za-z]+)\s+(\d+)', date_str)
                if date_match:
                    m_str = date_match.group(1).lower()
                    month_num = month_map.get(m_str, 1)
                    day_num = int(date_match.group(2))
                else:
                    month_num = 1
                    day_num = 1
            else:
                month_num = 1
                day_num = 1

            # Year resolution
            current_date = datetime.date.today()
            year_num = current_date.year
            if month_num < current_date.month and month_num <= 3:
                year_num = current_date.year + 1

            try:
                event_date = datetime.date(year_num, month_num, day_num)
            except ValueError:
                continue

            # Venue display name
            venue = f"Cooks of Crocus Hill - {location}" if location in ('St. Paul', 'Minneapolis') else 'Cooks of Crocus Hill'

            # Price
            price_raw = item.get('data-product-price', '').strip()
            price_str = f"${price_raw}" if price_raw else ''

            support_str = f"{time_str}  {price_str}".strip() if price_str else time_str

            shows.append({
                'date': event_date.isoformat(),
                'end_date': event_date.isoformat(),
                'venue': venue,
                'title': name,
                'tour': 'Cooking Class',
                'support_raw': support_str,
                'artists': [name],
                'link': link,
            })

        return shows
