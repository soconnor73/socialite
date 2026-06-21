import json
import datetime
import urllib.request
import gzip
from typing import List, Dict, Any, Optional
from .base import BaseParser

API_BASE = 'https://visitduluth.com/wp-json/tribe/events/v1/events'
PER_PAGE = 50


class VisitDuluthParser(BaseParser):
    """
    Parser for the Visit Duluth events calendar.
    URL: https://visitduluth.com/events/calendar/

    The site uses The Events Calendar (Tribe) WordPress plugin.  The HTML
    calendar page only ever shows the current month and cannot be navigated
    to future months via simple URL parameters.  However, the site exposes
    Tribe's public REST API at:

        /wp-json/tribe/events/v1/events
            ?start_date=YYYY-MM-DD
            &end_date=YYYY-MM-DD
            &per_page=50
            &page=N

    This parser uses that API directly.  The scraper passes pre-fetched JSON
    bytes (one API response page at a time) via ``html_content``, and the
    parser accumulates all events across all API pages.

    Each API event object contains:
      - title            (str)
      - start_date       (YYYY-MM-DD HH:MM:SS)
      - end_date         (YYYY-MM-DD HH:MM:SS)
      - url              (permalink)
      - venue.venue      (venue display name)
      - cost             (string, e.g. "Free", "$10", "10 – 50")
    """

    def _clean(self, text: str) -> str:
        if not text:
            return ''
        import html as _html
        text = _html.unescape(text)
        text = text.replace('\xa0', ' ').replace('\u2011', '-')
        text = text.replace('\u2018', "'").replace('\u2019', "'")
        text = text.replace('\u201c', '"').replace('\u201d', '"')
        return ' '.join(text.split()).strip()

    def _parse_api_event(self, ev: Dict) -> Optional[Dict[str, Any]]:
        """Convert one Tribe REST API event object into a BaseParser show dict."""
        status = ev.get('status', '')
        if status not in ('publish', ''):
            return None

        name = self._clean(ev.get('title', ''))
        if not name:
            return None

        url = ev.get('url', '')

        start_raw = ev.get('start_date', '')   # "2026-07-01 18:00:00"
        end_raw = ev.get('end_date', start_raw)

        try:
            start_date = datetime.date.fromisoformat(start_raw[:10])
            end_date = datetime.date.fromisoformat(end_raw[:10])
        except (ValueError, TypeError):
            return None

        # Show time
        time_str = ''
        try:
            dt = datetime.datetime.strptime(start_raw, '%Y-%m-%d %H:%M:%S')
            hour = dt.hour % 12 or 12
            ampm = 'AM' if dt.hour < 12 else 'PM'
            time_str = f"{hour}:{dt.minute:02d} {ampm}"
        except Exception:
            pass

        # Venue
        venue_info = ev.get('venue', {})
        venue = self._clean(venue_info.get('venue', '')) if isinstance(venue_info, dict) else ''
        if not venue:
            venue = 'Duluth'

        # Cost hint
        cost = self._clean(str(ev.get('cost', '')))
        support_raw = f"{time_str}  {cost}".strip() if cost else time_str

        return {
            'date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'venue': venue,
            'title': name,
            'tour': 'Duluth Event',
            'support_raw': support_raw,
            'artists': [name],
            'link': url,
        }

    def parse(self, html_content: bytes, **kwargs) -> List[Dict[str, Any]]:
        """
        Parse one page of Tribe REST API JSON response.

        Args:
            html_content: Raw bytes of a Tribe REST API response (JSON).
            **kwargs:     Unused.

        Returns:
            List of structured show dicts for the events on this API page.
        """
        try:
            data = json.loads(html_content)
        except (json.JSONDecodeError, TypeError):
            return []

        raw_events = data.get('events', [])
        shows: List[Dict[str, Any]] = []

        for ev in raw_events:
            show = self._parse_api_event(ev)
            if show:
                shows.append(show)

        return shows
