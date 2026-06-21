import datetime
from typing import List, Dict, Any
from .base import BaseParser

class TrylonCinemaParser(BaseParser):
    """
    Parser for Trylon Cinema events.
    Fetches the public Google Calendar ICAL feed.
    """

    def parse(self, html_content: bytes, **kwargs) -> List[Dict[str, Any]]:
        """
        Parses the Google Calendar ICS file content and converts VEVENTs to show dicts.
        """
        try:
            content = html_content.decode('utf-8', errors='ignore')
        except Exception:
            return []

        shows: List[Dict[str, Any]] = []
        lines = content.splitlines()
        
        # Unfold lines (ICS lines can be split by CRLF + Space/Tab)
        unfolded_lines = []
        for line in lines:
            if not line:
                continue
            if line.startswith(' ') or line.startswith('\t'):
                if unfolded_lines:
                    unfolded_lines[-1] += line[1:]
            else:
                unfolded_lines.append(line)

        current_event: Dict[str, str] = {}
        in_vevent = False

        for line in unfolded_lines:
            if line.startswith('BEGIN:VEVENT'):
                in_vevent = True
                current_event = {}
            elif line.startswith('END:VEVENT'):
                if in_vevent:
                    show = self._process_vevent(current_event)
                    if show:
                        shows.append(show)
                    in_vevent = False
            elif in_vevent:
                if ':' in line:
                    key_part, val = line.split(':', 1)
                    key = key_part.split(';')[0]
                    current_event[key] = val.strip()

        return shows

    def _process_vevent(self, ev: Dict[str, str]) -> Dict[str, Any] | None:
        summary = ev.get('SUMMARY', '').strip()
        if not summary:
            return None

        dtstart = ev.get('DTSTART', '')
        if not dtstart:
            return None

        date_str = dtstart
        if 'T' in date_str:
            date_str = date_str.split('T')[0]
        
        date_str = ''.join(c for c in date_str if c.isdigit())
        if len(date_str) < 8:
            return None
        
        yyyy = date_str[:4]
        mm = date_str[4:6]
        dd = date_str[6:8]
        
        start_date_iso = f"{yyyy}-{mm}-{dd}"
        
        dtend = ev.get('DTEND', '')
        end_date_iso = start_date_iso
        if dtend:
            if 'T' in dtend:
                dtend = dtend.split('T')[0]
            dtend = ''.join(c for c in dtend if c.isdigit())
            if len(dtend) >= 8:
                try:
                    eyyyy = int(dtend[:4])
                    emm = int(dtend[4:6])
                    edd = int(dtend[6:8])
                    e_date = datetime.date(eyyyy, emm, edd)
                    
                    if 'T' not in ev.get('DTSTART', '') and 'T' not in ev.get('DTEND', ''):
                        e_date = e_date - datetime.timedelta(days=1)
                    
                    end_date_iso = e_date.isoformat()
                except Exception:
                    pass

        title = summary
        venue = 'Trylon Cinema'
        
        title_lower = title.lower()
        if '@heights' in title_lower or 'at heights' in title_lower or 'at the heights' in title_lower:
            venue = 'The Heights Theater'
            for pattern in ('@heights', '@ heights', 'at heights', 'at the heights'):
                idx = title_lower.find(pattern)
                if idx != -1:
                    title = title[:idx] + title[idx+len(pattern):]
                    title_lower = title.lower()
        elif 'at willow creek' in title_lower:
            venue = 'Willow Creek Cinema'
            idx = title_lower.find('at willow creek')
            title = title[:idx] + title[idx+len('at willow creek'):]
            title_lower = title.lower()
        elif '@riverview' in title_lower:
            venue = 'Riverview Theater'
            idx = title_lower.find('@riverview')
            title = title[:idx] + title[idx+len('@riverview'):]
            title_lower = title.lower()

        title = ' '.join(title.split()).strip()
        link = 'https://www.trylon.org/calendar/'

        return {
            'date': start_date_iso,
            'end_date': end_date_iso,
            'venue': venue,
            'title': title,
            'tour': 'Film Screening',
            'support_raw': 'Showtime details on Trylon site',
            'artists': [title],
            'link': link
        }
