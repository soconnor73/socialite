import datetime
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from .base import BaseParser

class NorthropAuditoriumParser(BaseParser):
    """
    Parser implementation for Northrop Auditorium events (northrop.umn.edu/upcoming-events).
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

    def parse_date(self, month_str: str, day_str: str) -> datetime.date:
        """
        Parses month and day strings to a datetime.date object.
        Resolves year according to the Northrop 2026-27 season (Sep-Dec -> 2026, Jan-Aug -> 2027).
        """
        month = self.month_map.get(month_str.lower().strip())
        if not month:
            return None
        try:
            day = int(day_str.strip())
        except ValueError:
            return None
            
        # Determine year: Northrop season 2026-27
        # September - December is 2026, January - August is 2027
        if month >= 9:
            year = 2026
        else:
            year = 2027
        return datetime.date(year, month, day)

    def parse(self, html_content: bytes, **kwargs) -> List[Dict[str, Any]]:
        """
        Parses Northrop Auditorium events HTML content.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        event_nodes = soup.find_all(class_='node--type-ss-event')
        
        parsed_shows = []
        
        for node in event_nodes:
            # Title & Primary Link
            title_el = node.find('h3')
            if not title_el:
                continue
            title_a = title_el.find('a')
            if not title_a:
                continue
                
            title = self._clean_text(title_a.get_text())
            
            link = title_a.get('href', '')
            if link.startswith('/'):
                link = "https://www.northrop.umn.edu" + link
                
            # Presenter (Support)
            presenter_el = node.find(class_='field--name-field-post')
            support = self._clean_text(presenter_el.get_text()) if presenter_el else ""
            
            # Details (Tour / Info)
            details_el = node.find(class_='field--name-field-display-date-wysiwyg')
            tour = self._clean_text(details_el.get_text()) if details_el else "Northrop Event"
            
            # Extract tickets link if present
            tickets_el = node.find(class_='field--name-field-tickets-link')
            tickets_link = ""
            if tickets_el:
                tickets_a = tickets_el.find('a')
                if tickets_a:
                    tickets_link = tickets_a.get('href', '')
                    
            # Use tickets link as primary link if found
            final_link = tickets_link if tickets_link else link
            
            # Mega Date views
            mega_date_container = node.find(class_='view-event-listing-mega-date')
            dates = []
            if mega_date_container:
                for r in mega_date_container.find_all(class_='views-row'):
                    m_el = r.find(class_='date-month')
                    d_el = r.find(class_='date-day')
                    if m_el and d_el:
                        dates.append((m_el.get_text(strip=True), d_el.get_text(strip=True)))
                        
            if not dates:
                continue
                
            start_date = self.parse_date(dates[0][0], dates[0][1])
            end_date = self.parse_date(dates[-1][0], dates[-1][1])
            
            if not start_date:
                continue
                
            if not end_date:
                end_date = start_date
                
            # Artists split
            artists = []
            if ":" in title:
                artists = [self._clean_text(a) for a in title.split(":")]
            elif " With " in title:
                artists = [self._clean_text(a) for a in title.split(" With ")]
            elif " with " in title:
                artists = [self._clean_text(a) for a in title.split(" with ")]
            else:
                artists = [title]
                
            parsed_shows.append({
                'date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'venue': 'Northrop Auditorium',
                'title': title,
                'tour': tour,
                'support_raw': support,
                'artists': artists,
                'link': final_link
            })
            
        return parsed_shows
