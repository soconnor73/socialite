import json
import datetime
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from .base import BaseParser


class DakotaJazzClubParser(BaseParser):
    """
    Parser for the Dakota Jazz Club events calendar.
    URL: https://www.dakotacooks.com/events

    The site is powered by The Events Calendar (Tribe) WordPress plugin and
    renders a monthly calendar view. Each page embeds a JSON-LD <script> block
    containing an array of Schema.org Event objects — this is the cleanest data
    source available and is used exclusively.

    Because the calendar is paginated by month, the scraper fetches multiple
    monthly pages (passed in via html_pages kwarg) and this parser processes
    each one.
    """

    def _clean(self, text: str) -> str:
        if not text:
            return ''
        text = text.replace('\xa0', ' ').replace('\u2011', '-')
        text = text.replace('\u2018', "'").replace('\u2019', "'")
        text = text.replace('\u201c', '"').replace('\u201d', '"')
        return ' '.join(text.split()).strip()

    def _extract_events_from_html(self, html_content: bytes) -> List[Dict[str, Any]]:
        """Extract all Schema.org Event objects from JSON-LD in a single HTML page."""
        soup = BeautifulSoup(html_content, 'html.parser')
        events = []
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string or '')
                # Data may be a list or a dict with @graph
                items = data if isinstance(data, list) else data.get('@graph', [data])
                for item in items:
                    if isinstance(item, dict) and item.get('@type') == 'Event':
                        events.append(item)
            except (json.JSONDecodeError, AttributeError):
                continue
        return events

    def _parse_event(self, event: Dict) -> Optional[Dict[str, Any]]:
        """Convert a single JSON-LD Event dict into the BaseParser show dict."""
        # Skip cancelled events
        status = event.get('eventStatus', '')
        if 'Cancelled' in status or 'Postponed' in status:
            return None

        name = self._clean(event.get('name', ''))
        if not name:
            return None

        url = event.get('url', '')

        # startDate is ISO 8601 with timezone: "2026-06-20T19:00:00-05:00"
        start_raw = event.get('startDate', '')
        end_raw = event.get('endDate', start_raw)

        if not start_raw:
            return None

        try:
            start_date = datetime.date.fromisoformat(start_raw[:10])
            end_date = datetime.date.fromisoformat(end_raw[:10])
        except ValueError:
            return None

        # Extract time for the support_raw field (human-readable)
        time_str = ''
        try:
            dt = datetime.datetime.fromisoformat(start_raw)
            time_str = dt.strftime('%-I:%M %p').lstrip('0') if hasattr(dt, 'strftime') else ''
        except Exception:
            pass
        # Windows-compatible time formatting
        try:
            dt = datetime.datetime.fromisoformat(start_raw)
            hour = dt.hour % 12 or 12
            minute = dt.minute
            ampm = 'AM' if dt.hour < 12 else 'PM'
            time_str = f"{hour}:{minute:02d} {ampm}"
        except Exception:
            time_str = ''

        # Categories from event description / performer tags
        # The article classes like 'tribe_events_cat-jazz' exist in the HTML
        # but not in JSON-LD. We use the generic 'Live Music' label here.
        category = 'Live Music'

        # Artists: Dakota is a music venue so the event name IS the act
        artists = [name]

        return {
            'date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'venue': 'Dakota Jazz Club',
            'title': name,
            'tour': category,
            'support_raw': time_str,
            'artists': artists,
            'link': url,
        }

    def parse(self, html_content: bytes, **kwargs) -> List[Dict[str, Any]]:
        """
        Parse Dakota Jazz Club monthly calendar HTML.

        Args:
            html_content: Raw HTML bytes from a single monthly calendar page.
            **kwargs: Unused.

        Returns:
            List of structured show dicts.
        """
        raw_events = self._extract_events_from_html(html_content)
        shows = []
        seen = set()

        for ev in raw_events:
            show = self._parse_event(ev)
            if not show:
                continue
            # Deduplicate by (date, title) — same act can have two sets per night
            key = (show['date'], show['title'].lower())
            if key in seen:
                # Keep the earlier (first) set time; skip duplicate
                continue
            seen.add(key)
            shows.append(show)

        return shows
