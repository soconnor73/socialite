import datetime
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from .base import BaseParser

class GrandCasinoArenaParser(BaseParser):
    """
    Parser implementation for Grand Casino Arena (grandcasinoarena.com).
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
        return " ".join(text.split()).strip()

    def _parse_date(self, date_div) -> datetime.date:
        if not date_div:
            return None
            
        # 1. Try single date first
        single = date_div.find(class_='m-date__singleDate')
        if single:
            m_el = single.find(class_='m-date__month')
            d_el = single.find(class_='m-date__day')
            y_el = single.find(class_='m-date__year')
            
            month_str = m_el.get_text(strip=True) if m_el else ""
            day_str = d_el.get_text(strip=True) if d_el else ""
            year_str = y_el.get_text(strip=True) if y_el else ""
            year_str = re.sub(r'[^\d]', '', year_str)
            
            month_num = self.month_map.get(month_str.lower()[:3])
            if month_num and day_str.isdigit() and year_str.isdigit():
                try:
                    return datetime.date(int(year_str), month_num, int(day_str))
                except ValueError:
                    pass
                    
        # 2. Try range date next (e.g. Monster Jam)
        range_first = date_div.find(class_='m-date__rangeFirst')
        range_last = date_div.find(class_='m-date__rangeLast')
        if range_first and range_last:
            m_el = range_first.find(class_='m-date__month')
            d_el = range_first.find(class_='m-date__day')
            y_el = range_last.find(class_='m-date__year')
            
            month_str = m_el.get_text(strip=True) if m_el else ""
            day_str = d_el.get_text(strip=True) if d_el else ""
            year_str = y_el.get_text(strip=True) if y_el else ""
            year_str = re.sub(r'[^\d]', '', year_str)
            
            month_num = self.month_map.get(month_str.lower()[:3])
            if month_num and day_str.isdigit() and year_str.isdigit():
                try:
                    return datetime.date(int(year_str), month_num, int(day_str))
                except ValueError:
                    pass
                    
        # 3. Fallback: parse raw text
        text = date_div.get_text(" ", strip=True)
        match = re.search(r'([A-Za-z]+)\s+(\d+)(?:\s*-\s*\d+)?\s*,\s*(\d{4})', text)
        if match:
            month_str = match.group(1).lower()[:3]
            day_str = match.group(2)
            year_str = match.group(3)
            month_num = self.month_map.get(month_str)
            if month_num:
                try:
                    return datetime.date(int(year_str), month_num, int(day_str))
                except ValueError:
                    pass
                    
        return None

    def parse(self, html_content: bytes, **kwargs) -> List[Dict[str, Any]]:
        """
        Parses Grand Casino Arena events page.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        events_elements = soup.find_all('div', class_='eventItem')
        
        parsed_shows = []
        
        for element in events_elements:
            # Date
            date_div = element.find('div', class_='date')
            show_date = self._parse_date(date_div)
            if not show_date:
                continue
                
            # Venue (implicitly Grand Casino Arena)
            venue = "Grand Casino Arena"
            
            # Title
            title = ""
            link = ""
            title_h3 = element.find('h3', class_='title')
            if title_h3:
                title = self._clean_text(title_h3.get_text(" ", strip=True))
                link_a = title_h3.find('a')
                if link_a:
                    link = link_a.get('href', '')
                    # Resolve relative URL if needed
                    if link.startswith('/'):
                        link = "https://www.grandcasinoarena.com" + link
            
            # Subtitle/Time (Metadata)
            tour = ""
            time_el = element.find('span', class_='start')
            if time_el:
                tour = f"Starts at {self._clean_text(time_el.get_text(strip=True))}"
                
            # Parse artists
            # Clean title of common suffixes or cancellation flags
            clean_title = re.sub(r'\s*-\s*Canceled.*$', '', title, flags=re.IGNORECASE)
            clean_title = re.sub(r':\s+.*$', '', clean_title) # e.g. Teddy Swims: The UGLY Tour -> Teddy Swims
            clean_title = self._clean_text(clean_title)
            
            artists = []
            if ' and ' in clean_title.lower():
                # Split co-headliners (e.g. Lionel Richie and Earth, Wind & Fire)
                parts = re.split(r'\s+and\s+', clean_title, flags=re.IGNORECASE)
                for part in parts:
                    part_clean = self._clean_text(part)
                    if part_clean:
                        artists.append(part_clean)
            elif ' with ' in clean_title.lower():
                parts = re.split(r'\s+with\s+', clean_title, flags=re.IGNORECASE)
                for part in parts:
                    part_clean = self._clean_text(part)
                    if part_clean:
                        artists.append(part_clean)
            else:
                if clean_title:
                    artists.append(clean_title)
                    
            parsed_shows.append({
                'date': show_date.isoformat(),
                'venue': venue,
                'title': title,
                'tour': tour,
                'support_raw': "",
                'artists': artists,
                'link': link
            })
            
        return parsed_shows
