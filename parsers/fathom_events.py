import datetime
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from .base import BaseParser

class FathomEventsParser(BaseParser):
    """
    Parser implementation for Fathom Events (fathomentertainment.com).
    """

    def parse(self, html_content: bytes, **kwargs) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html_content, 'html.parser')
        parsed_shows = []
        year = kwargs.get('year', 2026)

        # Map event_id -> date spans from posters carousel (Other Upcoming Releases)
        event_dates = {}
        
        posters = soup.find_all(class_='posters-carousel-item')
        for p in posters:
            event_id = p.get('id')
            if not event_id:
                continue
            date_div = p.find(class_='date-list')
            if date_div:
                spans = [s.get_text(strip=True) for s in date_div.find_all('span')]
                start, end = self._parse_fathom_dates(spans, year)
                if start:
                    event_dates[event_id] = (start, end)

        # Now parse "Playing Near You" section
        playing_near_you_section = soup.find(class_='block-trailers')
        if playing_near_you_section:
            cards = playing_near_you_section.find_all(class_='trailer-card')
            for card in cards:
                event_id = card.get('id')
                h3 = card.find(class_='trailer-card-title') or card.find('h3')
                if not h3:
                    continue
                title = self._clean_text(h3.get_text(strip=True))
                
                pretitle_el = card.find(class_='trailer-card-pretitle')
                pretitle = self._clean_text(pretitle_el.get_text(strip=True)) if pretitle_el else ""
                
                link_el = card.find('a')
                link = link_el.get('href') if link_el else ""
                if not link:
                    btn_el = card.find(class_='video-button')
                    if btn_el:
                        link = btn_el.get('data-button-link', '')
                
                start_date, end_date = event_dates.get(event_id, (None, None))
                if not start_date:
                    start_date = datetime.date(year, 7, 11)
                    end_date = start_date

                parsed_shows.append({
                    'date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'venue': 'Fathom Events',
                    'title': title,
                    'tour': 'Playing Near You',
                    'support_raw': pretitle,
                    'artists': [title],
                    'link': link
                })

        # Now parse "Other Upcoming Releases" section
        posters_section = soup.find(class_='wp-block-posters')
        if posters_section:
            items = posters_section.find_all(class_='posters-carousel-item')
            for item in items:
                h3 = item.find(class_='headline') or item.find('h3')
                if not h3:
                    continue
                title = self._clean_text(h3.get_text(strip=True))
                
                preheadline_el = item.find(class_='preheadline')
                preheadline = self._clean_text(preheadline_el.get_text(strip=True)) if preheadline_el else ""
                
                link = item.get('href', '')
                event_id = item.get('id')
                start_date, end_date = event_dates.get(event_id, (None, None))
                if not start_date:
                    start_date = datetime.date(year, 7, 11)
                    end_date = start_date

                parsed_shows.append({
                    'date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'venue': 'Fathom Events',
                    'title': title,
                    'tour': 'Other Upcoming Releases',
                    'support_raw': preheadline,
                    'artists': [title],
                    'link': link
                })

        return parsed_shows

    def _parse_fathom_dates(self, spans: List[str], year: int) -> tuple:
        months = {
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        
        def parse_single_date(s: str):
            s = s.strip()
            m = re.search(r'([a-zA-Z]+)\s+(\d+)', s)
            if m:
                mon_str = m.group(1).lower()[:3]
                day = int(m.group(2))
                mon = months.get(mon_str)
                if mon:
                    return datetime.date(year, mon, day)
            return None

        all_dates = []
        for s in spans:
            s = s.replace('\u2014', '-').replace('\u2013', '-').replace('\u2011', '-')
            if '-' in s:
                parts = s.split('-')
                for part in parts:
                    parsed = parse_single_date(part)
                    if parsed:
                        all_dates.append(parsed)
            else:
                parsed = parse_single_date(s)
                if parsed:
                    all_dates.append(parsed)
                    
        if not all_dates:
            return None, None
            
        all_dates.sort()
        return all_dates[0], all_dates[-1]

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = text.replace('\xa0', ' ').replace('\u00a0', ' ')
        text = text.replace('’', "'").replace('‘', "'").replace('”', '"').replace('“', '"')
        return " ".join(text.split()).strip()
