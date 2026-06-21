import datetime
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from .base import BaseParser


class MNCBAWorkshopsParser(BaseParser):
    """
    Parser for the Minnesota Center for Book Arts (MNCBA) Workshops calendar.
    URL: https://mnbookarts.org/category/adult-workshops

    This is a Squarespace site using a Summary Block to list upcoming workshops.
    Events are parsed from elements with class 'summary-item'.
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
        Parses raw HTML content of MNCBA Workshops page.

        Args:
            html_content: Raw HTML bytes.
            **kwargs:     Unused.

        Returns:
            List of structured workshop events.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        summary_items = soup.find_all(class_=lambda x: x and 'summary-item' in str(x))
        shows: List[Dict[str, Any]] = []

        month_map = {
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }

        # Tracks added event links to prevent duplicates
        seen_links = set()

        for item in summary_items:
            title_a = item.find('a', class_='summary-title-link')
            if not title_a:
                continue

            name = self._clean(title_a.get_text(strip=True))
            if not name:
                continue

            link = title_a.get('href', '')
            if not link:
                continue
            if link.startswith('/'):
                link = 'https://mnbookarts.org' + link

            # De-duplicate identical workshop cards
            if link in seen_links:
                continue
            seen_links.add(link)

            # Dates
            month_tag = item.find(class_='summary-thumbnail-event-date-month')
            day_tag = item.find(class_='summary-thumbnail-event-date-day')
            if not month_tag or not day_tag:
                continue

            month_str = self._clean(month_tag.get_text(strip=True)).lower()[:3]
            month_num = month_map.get(month_str, 1)
            try:
                day_num = int(self._clean(day_tag.get_text(strip=True)))
            except ValueError:
                continue

            # Resolve Year: Try extracting 4-digit year from URL, else default to current/next year logic
            year_match = re.search(r'202\d', link)
            if year_match:
                year_num = int(year_match.group(0))
            else:
                current_date = datetime.date.today()
                year_num = current_date.year
                if month_num < current_date.month and month_num <= 3:
                    year_num = current_date.year + 1

            try:
                event_date = datetime.date(year_num, month_num, day_num)
            except ValueError:
                continue

            # Support metadata (Categories / Format / Experience Level)
            cat_links = item.find_all('a', href=lambda x: x and '?category=' in x)
            cats = [self._clean(c.get_text(strip=True)) for c in cat_links]
            unique_cats = []
            for c in cats:
                if c not in unique_cats:
                    unique_cats.append(c)
            support_str = ", ".join(unique_cats)

            shows.append({
                'date': event_date.isoformat(),
                'end_date': event_date.isoformat(),
                'venue': 'MNCBA',
                'title': name,
                'tour': 'MNCBA Workshop',
                'support_raw': support_str,
                'artists': [name],
                'link': link,
            })

        return shows
