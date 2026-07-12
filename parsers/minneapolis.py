import datetime
import re
import urllib.request
import gzip
import os
import html
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from .base import BaseParser

class MinneapolisParser(BaseParser):
    """
    Parser implementation for Meet Minneapolis calendar (minneapolis.org/calendar).
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
        return " ".join(text.split()).strip()

    def _parse_dates(self, label: str):
        if not label:
            return None, None
            
        # 1. Match "From MMM DD, YYYY to MMM DD, YYYY"
        range_match = re.search(
            r'From\s+([A-Za-z]+)\s+(\d+),\s+(\d{4})\s+to\s+([A-Za-z]+)\s+(\d+),\s+(\d{4})',
            label, re.IGNORECASE
        )
        if range_match:
            s_month_str = range_match.group(1).lower()[:3]
            s_day = int(range_match.group(2))
            s_year = int(range_match.group(3))
            
            e_month_str = range_match.group(4).lower()[:3]
            e_day = int(range_match.group(5))
            e_year = int(range_match.group(6))
            
            s_month = self.month_map.get(s_month_str)
            e_month = self.month_map.get(e_month_str)
            
            if s_month and e_month:
                try:
                    start_date = datetime.date(s_year, s_month, s_day)
                    end_date = datetime.date(e_year, e_month, e_day)
                    return start_date, end_date
                except ValueError:
                    pass

        # 2. Match single date "MMM DD, YYYY"
        single_match = re.search(r'([A-Za-z]+)\s+(\d+),\s+(\d{4})', label, re.IGNORECASE)
        if single_match:
            month_str = single_match.group(1).lower()[:3]
            day = int(single_match.group(2))
            year = int(single_match.group(3))
            
            month = self.month_map.get(month_str)
            if month:
                try:
                    start_date = datetime.date(year, month, day)
                    return start_date, start_date
                except ValueError:
                    pass
                    
        return None, None

    def parse(self, html_content: bytes, **kwargs) -> List[Dict[str, Any]]:
        """
        Parses Minneapolis.org calendar page.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        cards = soup.find_all('article', class_='card--detail')
        
        parsed_shows = []
        
        for card in cards:
            # Title
            title_el = card.find(class_='card__heading')
            if not title_el:
                continue
            title = self._clean_text(title_el.get_text(strip=True))
            
            # Details Link
            link = ""
            link_a = title_el.find('a')
            if link_a:
                link = link_a.get('href', '')
                if link.startswith('/'):
                    link = "https://www.minneapolis.org" + link
                    
            # Date Parsing via aria-label on cal-date elements
            cal_date = card.find(class_='cal-date')
            label = cal_date.get('aria-label', '') if cal_date else ""
            start_date, end_date = self._parse_dates(label)
            
            if not start_date:
                continue
                
            # Venue Extraction from map summary Address / Event Location
            venue = "Minneapolis"
            address = ""
            map_summary = card.find(class_='map-infowindow__summary')
            if map_summary:
                lines = [self._clean_text(line) for line in map_summary.get_text('\n').split('\n') if self._clean_text(line)]
                if lines:
                    first_line = lines[0]
                    # Check if the first line starts with a digit (street address)
                    if re.match(r'^\d+', first_line):
                        venue = "Minneapolis"
                        address = ", ".join(lines)
                    else:
                        venue = first_line
                        address = ", ".join(lines[1:]) if len(lines) > 1 else ""
            
            # Resolve venue from detail page Event Location if venue defaults to Minneapolis
            if venue == "Minneapolis" and link:
                detail_venue = self._get_detail_venue(link)
                if detail_venue:
                    venue = detail_venue
                
            # Artists (for generic city events, title is the event artist representation)
            artists = [title]
            
            # Categories (Tours / Subtitles)
            categories = [t.get_text(strip=True) for t in card.find_all(class_='card__tag')]
            tour_info = ", ".join(categories) if categories else "Calendar Event"
            
            parsed_shows.append({
                'date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'venue': venue,
                'title': title,
                'tour': tour_info,
                'support_raw': address, # Save full address in support field as extra metadata
                'artists': artists,
                'link': link
            })
            
        return parsed_shows

    def _get_detail_venue(self, url: str) -> str:
        if not url:
            return ""
        
        slug_match = re.search(r'/calendar/([^/]+)/?$', url)
        slug = slug_match.group(1) if slug_match else "temp"
        
        cache_dir = "raw_html/minneapolis_details"
        os.makedirs(cache_dir, exist_ok=True)
        cache_path = os.path.join(cache_dir, f"{slug}.html")
        
        content_text = ""
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    content_text = f.read()
            except Exception:
                pass
        
        if not content_text:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'Accept-Encoding': 'gzip, deflate'
            }
            req = urllib.request.Request(url, headers=headers)
            try:
                with urllib.request.urlopen(req) as response:
                    content = response.read()
                    if response.info().get('Content-Encoding') == 'gzip':
                        content = gzip.decompress(content)
                    content_text = content.decode('utf-8', errors='ignore')
                    with open(cache_path, 'w', encoding='utf-8') as f:
                        f.write(content_text)
                    import time
                    time.sleep(0.1) # Small delay to avoid hammering the server
            except Exception:
                return ""
                
        if content_text:
            try:
                soup = BeautifulSoup(content_text, 'html.parser')
                h3 = soup.find('h3', string=re.compile(r'Event Location', re.IGNORECASE))
                if h3:
                    p = h3.find_next('p')
                    if p:
                        import html as _html
                        return self._clean_text(_html.unescape(p.get_text(strip=True)))
            except Exception:
                pass
        return ""
