import datetime
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional, Tuple
from .base import BaseParser

BASE_URL = 'https://www.berlinmpls.com'


class BerlinJazzClubParser(BaseParser):
    """
    Parser for the Berlin jazz club events calendar (Squarespace).
    URL: https://www.berlinmpls.com/calendar

    The calendar is rendered as a Squarespace native events list.
    Each event is an <article class="eventlist-event ..."> element inside
    <div class="eventlist eventlist--upcoming">.

    Key data points:
      - Title:      a.eventlist-title-link (text + href)
      - Start date: first <time class="event-date" datetime="YYYY-MM-DD">
      - End date:   second <time class="event-date"> for multi-day shows
                    (late-night shows often cross midnight into the next day)
      - Time:       <time class="event-time-localized-start"> text
      - Excerpt:    div.eventlist-excerpt  (admission info, support acts, etc.)

    The single /calendar page lists all upcoming events — no pagination required.
    """

    def _clean(self, text: str) -> str:
        if not text:
            return ''
        text = text.replace('\xa0', ' ').replace('\u2011', '-')
        text = text.replace('\u2018', "'").replace('\u2019', "'")
        text = text.replace('\u201c', '"').replace('\u201d', '"')
        return ' '.join(text.split()).strip()

    def _parse_event(self, article) -> Optional[Dict[str, Any]]:
        # ── Title & link ─────────────────────────────────────────────────────
        title_a = article.find('a', class_='eventlist-title-link')
        if not title_a:
            return None
        title = self._clean(title_a.get_text())
        if not title:
            return None

        href = title_a.get('href', '')
        link = (BASE_URL + href) if href.startswith('/') else href

        # ── Dates ────────────────────────────────────────────────────────────
        # All <time class="event-date"> elements carry datetime="YYYY-MM-DD".
        # The first is start, the second (if present) is end for multi-day events.
        date_times = article.find_all('time', class_='event-date')
        if not date_times:
            return None
        try:
            start_date = datetime.date.fromisoformat(date_times[0].get('datetime', '')[:10])
        except (ValueError, TypeError):
            return None
        # For multi-day (cross-midnight) shows use the end <time> if available
        if len(date_times) >= 2:
            try:
                end_date = datetime.date.fromisoformat(date_times[-1].get('datetime', '')[:10])
            except (ValueError, TypeError):
                end_date = start_date
        else:
            end_date = start_date

        # ── Show time ────────────────────────────────────────────────────────
        time_el = article.find('time', class_='event-time-localized-start')
        time_str = self._clean(time_el.get_text()) if time_el else ''

        # ── Excerpt / admission info ─────────────────────────────────────────
        excerpt_el = article.find(class_='eventlist-excerpt')
        excerpt = self._clean(excerpt_el.get_text()) if excerpt_el else ''
        # Truncate to a reasonable length for support_raw
        if len(excerpt) > 120:
            excerpt = excerpt[:120].rsplit(' ', 1)[0] + '…'

        support_raw = f"{time_str}  {excerpt}".strip() if excerpt else time_str

        return {
            'date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'venue': 'Berlin Jazz Club',
            'title': title,
            'tour': 'Live Music',
            'support_raw': support_raw,
            'artists': [title],
            'link': link,
        }

    def parse(self, html_content: bytes, **kwargs) -> List[Dict[str, Any]]:
        """
        Parse Berlin Jazz Club calendar page HTML.

        Args:
            html_content: Raw HTML bytes from https://www.berlinmpls.com/calendar
            **kwargs:     Unused.

        Returns:
            List of structured show dicts conforming to the BaseParser contract.
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        # The upcoming events list; fall back to any eventlist container
        container = soup.find(class_='eventlist--upcoming') or soup.find(class_='eventlist')
        if not container:
            return []

        articles = container.find_all('article', class_='eventlist-event')
        shows: List[Dict[str, Any]] = []

        for article in articles:
            show = self._parse_event(article)
            if show:
                shows.append(show)

        return shows
