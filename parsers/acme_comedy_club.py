import datetime
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from .base import BaseParser

class AcmeComedyClubParser(BaseParser):
    """
    Parser implementation for ACME Comedy Club (acmecomedycompany.com).
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

    def parse(self, html_content: bytes, **kwargs) -> List[Dict[str, Any]]:
        """
        Parses ACME Comedy Club homepage.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        show_cards = soup.find_all(class_='show-card')
        
        parsed_shows = []
        
        for card in show_cards:
            # Extract year from the ID attribute (e.g. show-06-19-2026-david-cross)
            card_id = card.get('id', '')
            year_match = re.search(r'-(\d{4})-', card_id)
            year = int(year_match.group(1)) if year_match else datetime.datetime.now().year
            
            # Title
            title_el = card.find('h2')
            title = self._clean_text(title_el.get_text(strip=True)) if title_el else ""
            
            # Details Link
            link = ""
            details_a = card.find('a', text=re.compile(r'Details', re.IGNORECASE))
            if details_a:
                link = details_a.get('href', '')
            else:
                # Find any link in card containing /shows/
                shows_a = card.find('a', href=re.compile(r'/shows/'))
                if shows_a:
                    link = shows_a.get('href', '')
            
            if link and not link.startswith('http'):
                link = "https://acmecomedycompany.com" + link
                
            # Tour / Subtitle (if available, e.g. "THIS WEEK" or "June 24-27")
            tour = ""
            tour_el = card.find('p', class_='t--sm')
            if tour_el:
                tour = self._clean_text(tour_el.get_text(strip=True))
                
            # Dates & Times
            # Each show card lists specific date entries
            dates_div = card.find(class_='show-card--dates')
            if not dates_div:
                continue
                
            date_items = dates_div.find_all(class_='show-card--date')
            for item in date_items:
                date_span = item.find('span')
                if not date_span:
                    continue
                date_text = self._clean_text(date_span.get_text(strip=True))
                
                # Parse date text (e.g. "Saturday, June 20")
                date_match = re.search(r'([A-Za-z]+)\s+(\d+)', date_text)
                if not date_match:
                    continue
                    
                month_name = date_match.group(1).lower()[:3]
                day = int(date_match.group(2))
                
                month_num = self.month_map.get(month_name)
                if not month_num:
                    continue
                    
                try:
                    show_date = datetime.date(year, month_num, day)
                except ValueError:
                    continue
                    
                # Time extraction (e.g. "@7:00pm" or "@8:00pm")
                item_text = item.get_text(" ", strip=True)
                time_match = re.search(r'@\s*(\d+(?::\d+)?(?:am|pm)?)', item_text, re.IGNORECASE)
                time_str = time_match.group(1) if time_match else ""
                
                # Venue is ACME Comedy Club
                venue = "ACME Comedy Club"
                
                # Artists is the title comedian
                artists = [title] if title else []
                
                parsed_shows.append({
                    'date': show_date.isoformat(),
                    'venue': venue,
                    'title': title,
                    'tour': f"Show at {time_str}" if time_str else tour,
                    'support_raw': "",
                    'artists': artists,
                    'link': link
                })
                
        return parsed_shows
