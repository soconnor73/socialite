import datetime
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from .base import BaseParser

class GuthrieTheaterParser(BaseParser):
    """
    Parser implementation for Guthrie Theater (guthrietheater.org).
    """

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = text.replace('\xa0', ' ').replace('\u00a0', ' ')
        # Clean smart quotes and other typography
        text = text.replace('’', "'").replace('‘', "'").replace('”', '"').replace('“', '"')
        return " ".join(text.split()).strip()

    def parse(self, html_content: bytes, **kwargs) -> List[Dict[str, Any]]:
        """
        Parses Guthrie Theater homepage.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        rows = soup.find_all('section', class_='c-construkt-row')
        
        parsed_shows = []
        current_section = "Show" # Default section category
        
        for row in rows:
            # 1. Detect if this row sets a section heading
            h2 = row.find('h2', class_='c-heading')
            if h2:
                header_text = h2.get_text(strip=True).upper()
                if "NOW PLAYING" in header_text:
                    current_section = "Now Playing"
                elif "ONSTAGE SOON" in header_text:
                    current_section = "Onstage Soon"
                    
            # 2. Extract c-event-card elements in this row
            cards = row.find_all(class_='c-event-card')
            for card in cards:
                # Title
                title_el = card.find(class_='c-event-card__title')
                if not title_el:
                    continue
                title = self._clean_text(title_el.get_text(strip=True))
                
                # Link
                link = ""
                link_a = card.find('a', class_='c-event-card__cover-link')
                if link_a:
                    link = link_a.get('href', '')
                    if link.startswith('/'):
                        link = "https://www.guthrietheater.org" + link
                        
                # Date Range
                # The page uses datetime attribute on <time> tags
                time_wrapper = card.find(class_='c-event-card__time')
                start_date = None
                end_date = None
                
                if time_wrapper:
                    times = time_wrapper.find_all('time')
                    if len(times) >= 1:
                        dt_str = times[0].get('datetime', '')
                        if dt_str:
                            try:
                                start_date = datetime.date.fromisoformat(dt_str)
                            except ValueError:
                                pass
                    if len(times) >= 2:
                        dt_str = times[1].get('datetime', '')
                        if dt_str:
                            try:
                                end_date = datetime.date.fromisoformat(dt_str)
                            except ValueError:
                                pass
                
                if not start_date:
                    continue
                    
                # Venue/Stage
                stage = ""
                venue_el = card.find(class_='c-event-card__venue')
                if venue_el:
                    stage = self._clean_text(venue_el.get_text(strip=True))
                    
                venue_name = "Guthrie Theater"
                if stage:
                    venue_name = f"Guthrie Theater - {stage}"
                    
                # Artists (for theater plays, the play itself is the main artistic unit)
                artists = [title]
                
                parsed_shows.append({
                    'date': start_date.isoformat(),
                    'end_date': end_date.isoformat() if end_date else start_date.isoformat(),
                    'venue': venue_name,
                    'title': title,
                    'tour': current_section,
                    'support_raw': "",
                    'artists': artists,
                    'link': link
                })
                
        return parsed_shows
