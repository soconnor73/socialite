import datetime
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from .base import BaseParser


class DameErrantClayParser(BaseParser):
    """
    Parser for Dame Errant Clay workshops and events.
    URL: https://www.dameerrant.com/workshopsandevents

    This is a Squarespace site. Events are listed within article elements with
    class 'eventlist-event'.
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
        Parses raw HTML content of Squarespace events page for Dame Errant Clay.

        Args:
            html_content: Raw HTML of the page.
            **kwargs:     Unused.

        Returns:
            List of structured workshop events.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        event_articles = soup.find_all(class_=lambda x: x and 'eventlist-event' in str(x))
        shows: List[Dict[str, Any]] = []

        for ev in event_articles:
            # Title & Link
            title_a = ev.find(class_='eventlist-title-link')
            if not title_a:
                continue
            name = self._clean(title_a.get_text(strip=True))
            if not name:
                continue

            link = title_a.get('href', '')
            if link.startswith('/'):
                link = 'https://www.dameerrant.com' + link

            # Dates
            date_tags = ev.find_all('time', class_='event-date')
            if not date_tags:
                continue
            
            try:
                start_date_str = date_tags[0]['datetime']
                start_date = datetime.date.fromisoformat(start_date_str)
            except (ValueError, KeyError, IndexError):
                continue

            try:
                end_date_str = date_tags[1]['datetime']
                end_date = datetime.date.fromisoformat(end_date_str)
            except (ValueError, KeyError, IndexError):
                end_date = start_date

            # Times
            start_time_tag = ev.find(class_='event-time-localized-start')
            end_time_tag = ev.find(class_='event-time-localized-end')
            
            start_time_str = self._clean(start_time_tag.get_text(strip=True)) if start_time_tag else ''
            end_time_str = self._clean(end_time_tag.get_text(strip=True)) if end_time_tag else ''

            time_str = start_time_str
            if start_time_str and end_time_str:
                time_str = f"{start_time_str} - {end_time_str}"

            # Location / Venue
            addr_tag = ev.find(class_='eventlist-meta-address')
            venue = 'Dame Errant Clay'
            if addr_tag:
                addr_text = self._clean(addr_tag.get_text(strip=True))
                # remove (map) text
                if addr_text.endswith('(map)'):
                    addr_text = addr_text[:-5].strip()
                if addr_text:
                    if 'dame errant' in addr_text.lower():
                        venue = 'Dame Errant Clay'
                    else:
                        venue = f"Dame Errant Clay - {addr_text}"

            shows.append({
                'date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'venue': venue,
                'title': name,
                'tour': 'Clay Workshop',
                'support_raw': time_str,
                'artists': [name],
                'link': link,
            })

        return shows
