import json
import datetime
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from .base import BaseParser


class CroonersSupperClubParser(BaseParser):
    """
    Parser for the Crooners Supper Club events calendar.
    URL: https://www.croonersmn.com/calendar/

    The site uses The Events Calendar (Tribe) WordPress plugin with a monthly
    calendar view. Each page embeds JSON-LD Schema.org Event objects — the
    cleanest available data source, used exclusively here.

    The scraper fetches five monthly pages (June–October) to cover the 120-day
    window. Each month page bleeds ~1 week into adjacent months (Tribe renders
    a full calendar grid), so deduplication by (date, title) is applied.

    Crooners runs multiple distinct rooms / stages:
      - The Belvedere at Crooners  (large stage)
      - The Dunsmore Room          (listening room)
      - The Lounge at Crooners     (intimate bar stage)
    The venue name is preserved from each event's location field when available,
    otherwise falls back to 'Crooners Supper Club'.
    """

    def _clean(self, text: str) -> str:
        if not text:
            return ''
        text = text.replace('\xa0', ' ').replace('\u2011', '-')
        text = text.replace('\u2018', "'").replace('\u2019', "'")
        text = text.replace('\u201c', '"').replace('\u201d', '"')
        return ' '.join(text.split()).strip()

    def _extract_events(self, html_content: bytes) -> List[Dict]:
        """Pull all Schema.org Event dicts from JSON-LD blocks in one HTML page."""
        soup = BeautifulSoup(html_content, 'html.parser')
        events = []
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string or '')
                items = data if isinstance(data, list) else data.get('@graph', [data])
                for item in items:
                    if isinstance(item, dict) and item.get('@type') == 'Event':
                        events.append(item)
            except (json.JSONDecodeError, AttributeError):
                continue
        return events

    def _parse_event(self, event: Dict) -> Optional[Dict[str, Any]]:
        """Convert a JSON-LD Event dict into the BaseParser show dict."""
        status = event.get('eventStatus', '')
        if 'Cancelled' in status or 'Postponed' in status:
            return None

        name = self._clean(event.get('name', ''))
        if not name:
            return None

        url = event.get('url', '')

        start_raw = event.get('startDate', '')
        end_raw = event.get('endDate', start_raw)
        if not start_raw:
            return None

        try:
            start_date = datetime.date.fromisoformat(start_raw[:10])
            end_date = datetime.date.fromisoformat(end_raw[:10])
        except ValueError:
            return None

        # Show time (Windows-safe formatting)
        time_str = ''
        try:
            dt = datetime.datetime.fromisoformat(start_raw)
            hour = dt.hour % 12 or 12
            minute = dt.minute
            ampm = 'AM' if dt.hour < 12 else 'PM'
            time_str = f"{hour}:{minute:02d} {ampm}"
        except Exception:
            pass

        # Venue — Crooners has named sub-rooms in the location.name field
        venue = 'Crooners Supper Club'
        loc = event.get('location')
        if isinstance(loc, dict):
            loc_name = self._clean(loc.get('name', ''))
            if loc_name:
                venue = loc_name

        # Offers / price hint for support_raw
        offers = event.get('offers', {})
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        price = ''
        if isinstance(offers, dict):
            price = self._clean(str(offers.get('price', '')))
            currency = offers.get('priceCurrency', '')
            if price and price != '0':
                price = f"${price}" if currency == 'USD' else price
            elif price == '0':
                price = 'Free'

        support_raw = f"{time_str}  {price}".strip() if price else time_str

        return {
            'date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'venue': venue,
            'title': name,
            'tour': 'Live Music',
            'support_raw': support_raw,
            'artists': [name],
            'link': url,
        }

    def parse(self, html_content: bytes, **kwargs) -> List[Dict[str, Any]]:
        """
        Parse a Crooners Supper Club monthly calendar HTML page.

        Args:
            html_content: Raw HTML bytes from one monthly calendar page.
            **kwargs:     Unused.

        Returns:
            List of structured show dicts (deduplicated by date + title).
        """
        raw_events = self._extract_events(html_content)
        shows: List[Dict[str, Any]] = []
        seen: set = set()

        for ev in raw_events:
            show = self._parse_event(ev)
            if not show:
                continue
            key = (show['date'], show['title'].lower())
            if key in seen:
                continue
            seen.add(key)
            shows.append(show)

        return shows
