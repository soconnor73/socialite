import datetime
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from .base import BaseParser


class TrainRideParser(BaseParser):
    """
    Parser for Minnesota Transportation Museum Osceola Train Rides.
    URL: https://trainride.org/all-rides/
    """

    MONTH_MAP = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
    }

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

    def _parse_date_from_title(self, title: str) -> datetime.date:
        months_pat = r'(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'
        m = re.search(months_pat + r'\s+(\d+)(?:st|nd|rd|th)?', title, re.IGNORECASE)
        if m:
            month_str = m.group(1).lower()[:3]
            month_num = self.MONTH_MAP.get(month_str)
            day_num = int(m.group(2))
            if month_num:
                current_year = datetime.date.today().year
                try:
                    dt = datetime.date(current_year, month_num, day_num)
                    # If date is in the past, adjust year if needed
                    # For simplicity, if the parsed date is before today, we can keep it if it is within a reasonable limit, or advance to next year.
                    return dt
                except ValueError:
                    pass
        return None

    def parse(self, html_content: bytes, **kwargs) -> List[Dict[str, Any]]:
        """
        Parses raw HTML content of trainride.org all-rides page.
        """
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')

        if not start_date:
            start_date = datetime.date.today()
        if not end_date:
            end_date = start_date + datetime.timedelta(days=120)

        soup = BeautifulSoup(html_content, 'html.parser')
        cards = soup.find_all('article', class_='activity-single--card')
        shows: List[Dict[str, Any]] = []

        for card in cards:
            title_el = card.find('h4', class_='activity__title')
            title = self._clean(title_el.get_text(strip=True)) if title_el else ""
            if not title:
                continue

            # Skip standard Gift Card or Donations placeholders
            if any(x in title.lower() for x in ['gift card', 'donation']):
                continue

            link_el = card.find('a', href=True)
            link = link_el.get('href', '') if link_el else ""
            if link and not link.startswith('http'):
                link = 'https://trainride.org' + link

            price_el = card.find(class_='activity__price')
            price = self._clean(price_el.get_text(" ", strip=True)) if price_el else ""
            price = price.replace("$ ", "$")

            duration = ""
            location = "Osceola & St. Croix Valley Railway"

            taxonomies = card.find_all('li', class_='taxonomy')
            for tax in taxonomies:
                tax_terms = tax.find(class_='taxonomy-terms')
                if not tax_terms:
                    continue
                term_text = self._clean(tax_terms.get_text(strip=True))
                # Check if it looks like a location
                if 'Depot' in term_text or 'Rd' in term_text or 'Osceola' in term_text:
                    # Keep default location or use it
                    pass
                # Check if it looks like a duration
                elif 'Hour' in term_text or 'Mile' in term_text:
                    duration = term_text

            support_parts = []
            if duration:
                support_parts.append(duration)
            if price:
                support_parts.append(price)
            support_raw = " • ".join(support_parts)

            # Resolve Dates
            specific_date = self._parse_date_from_title(title)
            if specific_date:
                s_date = specific_date
                e_date = specific_date
            else:
                s_date = start_date
                e_date = end_date

            shows.append({
                'date': s_date.isoformat(),
                'end_date': e_date.isoformat(),
                'venue': location,
                'title': title,
                'tour': 'Train Rides',
                'support_raw': support_raw,
                'artists': [title],
                'link': link
            })

        return shows
