import datetime
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from .base import BaseParser


class PryesBrewingParser(BaseParser):
    """
    Parser for the Pryes Brewing events page.
    URL: https://www.pryesbrewing.com/events

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
        text = text.replace('\u202f', ' ') # clean narrow non-breaking space
        return ' '.join(text.split()).strip()

    def parse(self, html_content: bytes, **kwargs) -> List[Dict[str, Any]]:
        """
        Parses raw HTML content of Squarespace events page.

        Args:
            html_content: Raw HTML of the events page.
            **kwargs:     Unused.

        Returns:
            List of structured event dictionaries.
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
                link = 'https://www.pryesbrewing.com' + link

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
            time_tags = ev.find_all('time', class_='event-time-12hr')
            start_time_str = self._clean(time_tags[0].get_text(strip=True)) if time_tags else ''
            end_time_str = self._clean(time_tags[1].get_text(strip=True)) if len(time_tags) > 1 else ''

            time_str = start_time_str
            if start_time_str and end_time_str:
                time_str = f"{start_time_str} - {end_time_str}"

            shows.append({
                'date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'venue': 'Pryes Brewing',
                'title': name,
                'tour': 'Pryes Brewing Event',
                'support_raw': time_str,
                'artists': [name],
                'link': link,
            })

        return shows
