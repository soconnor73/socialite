import datetime
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from .base import BaseParser

class TargetCenterParser(BaseParser):
    """
    Parser implementation for Target Center events (targetcenter.com/events).
    """

    def __init__(self):
        self.month_map = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
            'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = text.replace('\xa0', ' ').replace('\u00a0', ' ')
        text = text.replace('’', "'").replace('‘', "'").replace('”', '"').replace('“', '"')
        return " ".join(text.split()).strip()

    def _parse_date(self, date_text: str):
        # Match "Sat, June 20, 2026"
        match = re.search(r'([A-Za-z]+),\s+([A-Za-z]+)\s+(\d+),\s+(\d{4})', date_text)
        if match:
            month_str = match.group(2).lower()
            day = int(match.group(3))
            year = int(match.group(4))
            
            month = self.month_map.get(month_str) or self.month_map.get(month_str[:3])
            if month:
                try:
                    return datetime.date(year, month, day)
                except ValueError:
                    pass
        return None

    def parse(self, html_content: bytes, **kwargs) -> List[Dict[str, Any]]:
        """
        Parses Target Center events HTML content.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        event_items = soup.find_all('div', class_='eventItem')
        
        parsed_shows = []
        
        for item in event_items:
            # Title & Link
            title_el = item.find('h3', class_='title')
            if not title_el:
                continue
            title = self._clean_text(title_el.get_text(strip=True))
            
            link_a = title_el.find('a')
            link = ""
            if link_a:
                link = link_a.get('href', '')
                if link.startswith('/'):
                    link = "https://www.targetcenter.com" + link
                    
            # Tagline (Opener / Support)
            tagline_el = item.find('h4', class_='tagline')
            support = self._clean_text(tagline_el.get_text(strip=True)) if tagline_el else ""
            
            # Date and Time
            date_div = item.find('div', class_='date')
            date_text = " ".join(date_div.get_text().split()).strip() if date_div else ""
            
            start_date = self._parse_date(date_text)
            if not start_date:
                continue
                
            # Extract Time
            time_str = "TBD"
            parts = date_text.split('-')
            if len(parts) > 1:
                time_str = self._clean_text(parts[1])
                
            # Artists split
            artists = []
            if " vs. " in title:
                artists = [self._clean_text(a) for a in title.split(" vs. ")]
            elif " vs " in title:
                artists = [self._clean_text(a) for a in title.split(" vs ")]
            else:
                artists = [title]
                
            # Category / Tour
            tour = time_str if time_str else "Target Center Event"
            
            parsed_shows.append({
                'date': start_date.isoformat(),
                'venue': 'Target Center',
                'title': title,
                'tour': tour,
                'support_raw': support,
                'artists': artists,
                'link': link
            })
            
        return parsed_shows
