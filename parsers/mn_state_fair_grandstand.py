import datetime
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from .base import BaseParser


class MNStateFairGrandstandParser(BaseParser):
    """
    Parser for Minnesota State Fair Grandstand shows.
    URL: https://www.mnstatefair.org/grandstand
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

    def parse(self, html_content: bytes, **kwargs) -> List[Dict[str, Any]]:
        """
        Parses raw HTML content of Minnesota State Fair Grandstand page.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        excerpts = soup.find_all(class_='grandstand_excerpt')
        shows: List[Dict[str, Any]] = []

        for item in excerpts:
            desc_div = item.find('div', class_='description')
            if not desc_div:
                continue

            # Title
            title_el = desc_div.find('h3')
            if not title_el:
                continue
            title = self._clean(title_el.get_text(strip=True))
            if not title:
                continue

            # Link
            link_a = desc_div.find('a', href=True)
            link = link_a.get('href', '') if link_a else ''
            if link.startswith('/'):
                link = 'https://www.mnstatefair.org' + link

            # Date and Time
            # Found in a paragraph under description
            p_tags = desc_div.find_all('p')
            date_time_str = ""
            for p in p_tags:
                p_text = p.get_text(strip=True)
                if '202' in p_text and ('pm' in p_text.lower() or 'am' in p_text.lower() or 'noon' in p_text.lower()):
                    date_time_str = self._clean(p_text)
                    break

            start_date = None
            time_str = ""
            if date_time_str:
                # e.g., "Thursday, Aug. 27, 2026 · 7:00 pm"
                # split by dot/bullet/dot-like character
                parts = [p.strip() for p in re.split(r'·|•|\-', date_time_str)]
                if parts:
                    date_part = parts[0]
                    time_str = parts[1] if len(parts) > 1 else ""

                    # Parse Date: e.g. "Thursday, Aug. 27, 2026"
                    m = re.search(r'([A-Za-z]+)\.?\s+(\d+),\s*(\d{4})', date_part)
                    if m:
                        m_str = m.group(1).lower()[:3]
                        # Fix sept vs sep
                        if m_str == 'sep' or m_str == 'sep.':
                            month_num = 9
                        else:
                            month_num = self.MONTH_MAP.get(m_str, 1)
                        day_num = int(m.group(2))
                        year_num = int(m.group(3))
                        try:
                            start_date = datetime.date(year_num, month_num, day_num)
                        except ValueError:
                            pass

            if not start_date:
                continue

            # Prices
            prices_div = desc_div.find(class_='prices')
            prices_str = ""
            if prices_div:
                # Remove nested brs/newlines and join clean text
                prices_str = self._clean(prices_div.get_text(" ", strip=True))

            support_parts = []
            if time_str:
                support_parts.append(time_str)
            if prices_str:
                support_parts.append(prices_str)
            support_raw = " • ".join(support_parts)

            shows.append({
                'date': start_date.isoformat(),
                'end_date': start_date.isoformat(),
                'venue': 'State Fair Grandstand',
                'title': title,
                'tour': 'Grandstand Concert Series',
                'support_raw': support_raw,
                'artists': [title],
                'link': link
            })

        return shows
