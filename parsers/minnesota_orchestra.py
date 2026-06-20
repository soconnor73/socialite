import datetime
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from .base import BaseParser

class MinnesotaOrchestraParser(BaseParser):
    """
    Parser implementation for Minnesota Orchestra (minnesotaorchestra.org).
    """

    def __init__(self):
        self.month_map = {
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = text.replace('\xa0', ' ').replace('\u00a0', ' ')
        text = text.replace('’', "'").replace('‘', "'").replace('”', '"').replace('“', '"')
        text = text.replace('\u2014', '-').replace('\u2013', '-')
        text = text.replace('\ufffd', '-')
        return " ".join(text.split()).strip()

    def _parse_single_date(self, part_str: str, fallback_year: int = None) -> datetime.date:
        part_str = part_str.strip()
        # Find a 4-digit year starting with 20
        year_match = re.search(r'\b(20\d{2})\b', part_str)
        if year_match:
            year = int(year_match.group(1))
            cleaned = part_str.replace(year_match.group(0), "").replace(",", "").strip()
        else:
            year = fallback_year
            cleaned = part_str.replace(",", "").strip()
        
        if not year:
            return None

        # Match month and day at the end of the cleaned string (e.g. "Jul 16")
        match = re.search(r'([A-Za-z]+)\s+(\d+)\s*$', cleaned)
        if match:
            m_str = match.group(1).lower()[:3]
            day = int(match.group(2))
            month = self.month_map.get(m_str)
            if month:
                try:
                    return datetime.date(year, month, day)
                except ValueError:
                    pass
        return None

    def _parse_date_range(self, date_str: str):
        # Normalize dash and space characters
        date_str = date_str.replace('\xa0', ' ').replace('\u00a0', ' ')
        date_str = date_str.replace('\u2014', '-').replace('\u2013', '-')
        date_str = date_str.replace('\ufffd', '-')
        
        parts = date_str.split('-')
        if len(parts) == 1:
            d = self._parse_single_date(parts[0])
            return d, d
        elif len(parts) == 2:
            # Parse end date first to get fallback year
            end_d = self._parse_single_date(parts[1])
            fallback_year = end_d.year if end_d else None
            start_d = self._parse_single_date(parts[0], fallback_year=fallback_year)
            return start_d, end_d or start_d
            
        return None, None

    def _extract_artists(self, title: str) -> List[str]:
        cleaned_title = self._clean_text(title)
        
        # Split on " and " or " with "
        parts = re.split(r'\b(?:and|with)\b', cleaned_title, flags=re.IGNORECASE)
        artists = []
        for part in parts:
            p_clean = self._clean_text(part)
            if p_clean:
                artists.append(p_clean)
        
        if not artists:
            artists = [cleaned_title]
        return artists

    def parse(self, html_content: bytes, **kwargs) -> List[Dict[str, Any]]:
        """
        Parses Minnesota Orchestra events page.
        """
        soup = BeautifulSoup(html_content, 'html.parser', from_encoding='utf-8')
        event_items = soup.find_all('div', class_='event-item')
        
        parsed_shows = []
        seen_events = set()
        
        for item in event_items:
            # Date
            date_el = item.find(class_='event-item__date')
            if not date_el:
                continue
            
            date_str = date_el.get_text(strip=True)
            start_date, end_date = self._parse_date_range(date_str)
            if not start_date or not end_date:
                continue
                
            # Title Building: Prefix + Title + Suffix
            prefix_el = item.find(class_='event-item__prefix')
            title_el = item.find(class_='event-item__title')
            suffix_el = item.find(class_='event-item__suffix')
            
            prefix_str = self._clean_text(prefix_el.get_text(strip=True)) if prefix_el else ""
            title_str = self._clean_text(title_el.get_text(strip=True)) if title_el else ""
            suffix_str = self._clean_text(suffix_el.get_text(strip=True)) if suffix_el else ""
            
            if not title_str:
                continue
                
            full_title = ""
            if prefix_str:
                full_title += prefix_str + " "
            full_title += title_str
            if suffix_str:
                full_title += " " + suffix_str
                
            full_title = self._clean_text(full_title)
            
            # Link extraction
            link = ""
            link_a = item.find('a')
            if link_a:
                link = link_a.get('href', '')
                if link.startswith('/'):
                    link = "https://www.minnesotaorchestra.org" + link
                    
            # Deduplicate by key
            event_key = (start_date.isoformat(), end_date.isoformat(), full_title, link)
            if event_key in seen_events:
                continue
            seen_events.add(event_key)
            
            # Artists split
            artists = self._extract_artists(full_title)
            
            parsed_shows.append({
                'date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'venue': 'Orchestra Hall',
                'title': full_title,
                'tour': prefix_str if prefix_str else "Minnesota Orchestra Event",
                'support_raw': suffix_str,
                'artists': artists,
                'link': link
            })
            
        return parsed_shows
