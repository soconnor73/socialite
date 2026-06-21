import json
import datetime
from typing import List, Dict, Any, Optional
from .base import BaseParser


class ParkwayTheaterParser(BaseParser):
    """
    Parser for The Parkway Theater event calendar.
    URL: https://theparkwaytheater.com/all-events
    Uses Squarespace's JSON format.
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

    def _parse_event(self, ev: Dict) -> Optional[Dict[str, Any]]:
        title = self._clean(ev.get('title', ''))
        if not title:
            return None

        # Start date
        start_ms = ev.get('startDate')
        if not start_ms:
            return None
        
        try:
            start_dt = datetime.datetime.fromtimestamp(start_ms / 1000.0)
            start_date_iso = start_dt.date().isoformat()
        except (ValueError, OSError, TypeError):
            return None

        # End date
        end_date_iso = start_date_iso
        end_ms = ev.get('endDate')
        if end_ms:
            try:
                end_dt = datetime.datetime.fromtimestamp(end_ms / 1000.0)
                end_date_iso = end_dt.date().isoformat()
            except Exception:
                pass

        # URL
        url = ev.get('fullUrl', '')
        if url and not url.startswith('http'):
            url = 'https://theparkwaytheater.com' + url

        # Time formatting
        time_str = ''
        try:
            hour = start_dt.hour % 12 or 12
            ampm = 'AM' if start_dt.hour < 12 else 'PM'
            time_str = f"{hour}:{start_dt.minute:02d} {ampm}"
        except Exception:
            pass

        return {
            'date': start_date_iso,
            'end_date': end_date_iso,
            'venue': 'The Parkway Theater',
            'title': title,
            'tour': 'Event/Movie',
            'support_raw': time_str,
            'artists': [title],
            'link': url
        }

    def parse(self, html_content: bytes, **kwargs) -> List[Dict[str, Any]]:
        """
        Parses Squarespace JSON response content.
        """
        try:
            data = json.loads(html_content)
        except (json.JSONDecodeError, TypeError):
            return []

        raw_events = data.get('upcoming', [])
        if not raw_events:
            raw_events = data.get('items', [])

        shows: List[Dict[str, Any]] = []
        for ev in raw_events:
            show = self._parse_event(ev)
            if show:
                shows.append(show)

        return shows
