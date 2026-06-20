import datetime
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from .base import BaseParser

class OrdwayParser(BaseParser):
    """
    Parser implementation for Ordway Center events (ordway.org/events).
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

    def _parse_dates(self, date_text: str):
        text = self._clean_text(date_text)
        text = text.replace('–', '-').strip()
        
        # Try Format 3: Range crossing months, e.g. "August 12 - September 6, 2026"
        match3 = re.match(r'^([A-Za-z]+)\s+(\d+)\s*-\s*([A-Za-z]+)\s+(\d+),\s*(\d{4})$', text)
        if match3:
            m1_str, d1_str, m2_str, d2_str, y_str = match3.groups()
            y = int(y_str)
            m1 = self.month_map.get(m1_str.lower())
            m2 = self.month_map.get(m2_str.lower())
            d1 = int(d1_str)
            d2 = int(d2_str)
            if m1 and m2:
                return datetime.date(y, m1, d1), datetime.date(y, m2, d2)
                
        # Try Format 2: Range within same month, e.g. "June 17 - 28, 2026"
        match2 = re.match(r'^([A-Za-z]+)\s+(\d+)\s*-\s*(\d+),\s*(\d{4})$', text)
        if match2:
            m_str, d1_str, d2_str, y_str = match2.groups()
            y = int(y_str)
            m = self.month_map.get(m_str.lower())
            d1 = int(d1_str)
            d2 = int(d2_str)
            if m:
                return datetime.date(y, m, d1), datetime.date(y, m, d2)
                
        # Try Format 1: Single date, e.g. "June 20, 2026"
        match1 = re.match(r'^([A-Za-z]+)\s+(\d+),\s*(\d{4})$', text)
        if match1:
            m_str, d_str, y_str = match1.groups()
            y = int(y_str)
            m = self.month_map.get(m_str.lower())
            d = int(d_str)
            if m:
                dt = datetime.date(y, m, d)
                return dt, dt
                
        return None, None

    def parse(self, html_content: bytes, **kwargs) -> List[Dict[str, Any]]:
        """
        Parses Ordway events HTML content.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        event_nodes = soup.find_all(class_='event-item')
        
        parsed_shows = []
        
        for node in event_nodes:
            # Title & Link
            title_el = node.find('h4', class_='title')
            if not title_el:
                continue
            title_a = title_el.find('a')
            if not title_a:
                continue
                
            title = self._clean_text(title_a.get_text())
            
            link = title_a.get('href', '')
            if link.startswith('/'):
                link = "https://ordway.org" + link
                
            # Presenter (Support)
            presenter_el = node.find(class_='label')
            support = self._clean_text(presenter_el.get_text()) if presenter_el else ""
            
            # Genre / Category
            genre_el = node.find(class_='genre')
            genre = self._clean_text(genre_el.get_text()) if genre_el else "Performance"
            
            # Subtitle (contains Date and sub-venue)
            sub_title_el = node.find(class_='sub-title')
            date_text = ""
            venue = "Ordway Theater"
            
            if sub_title_el:
                strong_el = sub_title_el.find('strong')
                if strong_el:
                    date_text = self._clean_text(strong_el.get_text())
                    
                spans = sub_title_el.find_all('span')
                for s in spans:
                    val = self._clean_text(s.get_text())
                    if val and val != "" and ('Theater' in val or 'Hall' in val or 'Ordway' in val):
                        venue = val
                        break
                        
            if not date_text:
                continue
                
            start_date, end_date = self._parse_dates(date_text)
            if not start_date:
                continue
                
            # Use button link if present for Tickets link, else default to page link
            tickets_link = link
            btn_container = node.find(class_='button-container')
            if btn_container:
                btn_a = btn_container.find('a')
                if btn_a:
                    btn_href = btn_a.get('href', '')
                    if btn_href:
                        if btn_href.startswith('/'):
                            tickets_link = "https://ordway.org" + btn_href
                        else:
                            tickets_link = btn_href
                            
            # Artists split
            artists = []
            if " & " in title:
                artists = [self._clean_text(a) for a in title.split(" & ")]
            elif " and " in title:
                artists = [self._clean_text(a) for a in title.split(" and ")]
            elif ":" in title:
                artists = [self._clean_text(a) for a in title.split(":")]
            else:
                artists = [title]
                
            parsed_shows.append({
                'date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'venue': venue,
                'title': title,
                'tour': genre,
                'support_raw': support,
                'artists': artists,
                'link': tickets_link
            })
            
        return parsed_shows
