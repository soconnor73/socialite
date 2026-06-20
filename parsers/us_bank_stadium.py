import datetime
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from .base import BaseParser

class USBankStadiumParser(BaseParser):
    """
    Parser implementation for U.S. Bank Stadium events (usbankstadium.com/events).
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

    def parse(self, html_content: bytes, **kwargs) -> List[Dict[str, Any]]:
        """
        Parses U.S. Bank Stadium events HTML content.
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
                    link = "https://www.usbankstadium.com" + link
                    
            # Tagline (Opener / Support)
            tagline_el = item.find('h4', class_='tagline')
            support = self._clean_text(tagline_el.get_text(strip=True)) if tagline_el else ""
            
            # Date Parsing
            date_div = item.find('div', class_='date')
            if not date_div:
                continue
                
            start_date = None
            end_date = None
            
            single_date_el = date_div.find('span', class_='m-date__singleDate')
            range_first_el = date_div.find('span', class_='m-date__rangeFirst')
            range_last_el = date_div.find('span', class_='m-date__rangeLast')
            
            if single_date_el:
                month_el = single_date_el.find('span', class_='m-date__month')
                day_el = single_date_el.find('span', class_='m-date__day')
                year_el = single_date_el.find('span', class_='m-date__year')
                
                if month_el and day_el:
                    month_str = month_el.get_text(strip=True).lower().replace('.', '')
                    day_str = day_el.get_text(strip=True)
                    year_str = year_el.get_text(strip=True) if year_el else ""
                    
                    month = self.month_map.get(month_str) or self.month_map.get(month_str[:3])
                    day = int(re.sub(r'\D', '', day_str))
                    year = int(re.sub(r'\D', '', year_str)) if re.sub(r'\D', '', year_str) else 2026
                    
                    if month and day:
                        try:
                            start_date = datetime.date(year, month, day)
                        except ValueError:
                            pass
            elif range_first_el and range_last_el:
                # Range date
                # First element month & day
                first_month_el = range_first_el.find('span', class_='m-date__month')
                first_day_el = range_first_el.find('span', class_='m-date__day')
                
                # Last element month, day & year
                last_month_el = range_last_el.find('span', class_='m-date__month')
                last_day_el = range_last_el.find('span', class_='m-date__day')
                last_year_el = range_last_el.find('span', class_='m-date__year')
                
                last_year_str = last_year_el.get_text(strip=True) if last_year_el else ""
                year = int(re.sub(r'\D', '', last_year_str)) if re.sub(r'\D', '', last_year_str) else 2026
                
                # First date month
                f_month = None
                if first_month_el:
                    first_month_str = first_month_el.get_text(strip=True).lower().replace('.', '')
                    f_month = self.month_map.get(first_month_str) or self.month_map.get(first_month_str[:3])
                
                # Last date month
                l_month = None
                if last_month_el:
                    last_month_str = last_month_el.get_text(strip=True).lower().replace('.', '')
                    l_month = self.month_map.get(last_month_str) or self.month_map.get(last_month_str[:3])
                    
                # Cross-fallback
                if f_month is None:
                    f_month = l_month
                if l_month is None:
                    l_month = f_month
                
                l_day_str = last_day_el.get_text(strip=True) if last_day_el else ""
                l_day = int(re.sub(r'\D', '', l_day_str)) if re.sub(r'\D', '', l_day_str) else None
                
                f_day_str = first_day_el.get_text(strip=True) if first_day_el else ""
                f_day = int(re.sub(r'\D', '', f_day_str)) if re.sub(r'\D', '', f_day_str) else None
                
                if f_month and f_day:
                    try:
                        start_date = datetime.date(year, f_month, f_day)
                    except ValueError:
                        pass
                if l_month and l_day:
                    try:
                        end_date = datetime.date(year, l_month, l_day)
                    except ValueError:
                        pass
                        
            if not start_date:
                continue
                
            # Extract Time / Tour Info
            time_el = item.find('h5', class_='time')
            time_str = ""
            if time_el:
                start_el = time_el.find('span', class_='start')
                if start_el:
                    time_str = self._clean_text(start_el.get_text(strip=True))
                else:
                    time_str = self._clean_text(time_el.get_text(strip=True))
                    
            # Artists split
            artists = []
            if " v. " in title:
                artists = [self._clean_text(a) for a in title.split(" v. ")]
            elif " vs. " in title:
                artists = [self._clean_text(a) for a in title.split(" vs. ")]
            elif " & " in title:
                artists = [self._clean_text(a) for a in title.split(" & ")]
            else:
                artists = [title]
                
            # If no end_date was parsed, default to start_date
            if not end_date:
                end_date = start_date
                
            tour = time_str if time_str else "U.S. Bank Stadium Event"
            
            parsed_shows.append({
                'date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'venue': 'U.S. Bank Stadium',
                'title': title,
                'tour': tour,
                'support_raw': support,
                'artists': artists,
                'link': link
            })
            
        return parsed_shows
