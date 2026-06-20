import datetime
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from .base import BaseParser

class FirstAvenueParser(BaseParser):
    """
    Parser implementation for First Avenue shows (first-avenue.com).
    """

    def __init__(self):
        self.month_map = {
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        # Replace non-breaking spaces with standard spaces
        text = text.replace('\xa0', ' ').replace('\u00a0', ' ')
        # Normalize multiple whitespaces
        return " ".join(text.split()).strip()

    def _split_acts(self, text: str) -> List[str]:
        if not text:
            return []
        # Split by " and ", " & ", ", ", " ft. ", " feat. ", " featuring ", " starring ", " • "
        delimiters = [
            r'\s+and\s+', r'\s*&\s*', r'\s*,\s*', r'\s+ft\.\s+', r'\s+feat\.\s+',
            r'\s+featuring\s+', r'\s+starring\s+', r'\s+with\s+', r'\s*•\s*'
        ]
        pattern = '|'.join(delimiters)
        split_list = re.split(pattern, text, flags=re.IGNORECASE)
        return [self._clean_text(act) for act in split_list if self._clean_text(act)]

    def parse(self, html_content: bytes, **kwargs) -> List[Dict[str, Any]]:
        """
        Parses First Avenue shows page.
        
        Args:
            html_content: The raw HTML content (as bytes).
            **kwargs: Requires 'year' (int) representing the year context for these shows.
        """
        year = kwargs.get('year')
        if not year:
            raise ValueError("FirstAvenueParser requires a 'year' keyword argument.")
            
        soup = BeautifulSoup(html_content, 'html.parser')
        shows_elements = soup.find_all('div', class_='show_list_item')
        
        parsed_shows = []
        
        for element in shows_elements:
            # Date extraction
            date_div = element.find('div', class_='date')
            if not date_div:
                continue
            
            month_el = date_div.find('div', class_='month')
            day_el = date_div.find('div', class_='day')
            
            if not month_el or not day_el:
                continue
                
            month_str = month_el.get_text(" ", strip=True).lower()[:3]
            day_str = day_el.get_text(" ", strip=True)
            
            month_num = self.month_map.get(month_str)
            if not month_num or not day_str.isdigit():
                continue
                
            try:
                show_date = datetime.date(year, month_num, int(day_str))
            except ValueError:
                continue
                
            # Venue extraction
            venue = ""
            venue_div = element.find('div', class_='venue_label')
            if venue_div:
                venue_name_div = venue_div.find('div', class_='venue_name')
                if venue_name_div:
                    venue = self._clean_text(venue_name_div.get_text(" ", strip=True))
                    
            # Main Artist / Show Title
            title = ""
            link = ""
            title_h4 = element.find('h4')
            if title_h4:
                title = self._clean_text(title_h4.get_text(" ", strip=True))
                link_a = title_h4.find('a')
                if link_a:
                    link = link_a.get('href')
                    
            # Tour / Subtitle
            tour = ""
            tour_h6 = element.find('h6', class_='mb-3')
            if tour_h6:
                tour = self._clean_text(tour_h6.get_text(" ", strip=True))
                
            # Support Artists
            support = ""
            support_h5 = element.find('h5')
            support_raw_str = ""
            if support_h5:
                support_raw_str = self._clean_text(support_h5.get_text(" ", strip=True))
                support = support_raw_str
                # Remove leading "with", "and", "with host", etc.
                support = re.sub(r'^(with host|with|and|featuring|hosted by)\s+', '', support, flags=re.IGNORECASE)
                
            # Parse individual artists
            artists = []
            
            # Primary Artist from Title
            primary_artist = re.sub(r'^(An Evening with|DJ Keezy presents|ft\.|feat\.)\s+', '', title, flags=re.IGNORECASE)
            primary_artist = self._clean_text(primary_artist)
            
            # Check if the title lists multiple primary headliners separated by comma, dot, or dash
            if ',' in primary_artist or '•' in primary_artist or '⏤' in primary_artist:
                delimiters = [r'\s*,\s*', r'\s*•\s*', r'\s+⏤\s+']
                pattern = '|'.join(delimiters)
                split_primary = re.split(pattern, primary_artist)
                for part in split_primary:
                    part_clean = self._clean_text(part)
                    if part_clean:
                        artists.append(part_clean)
            else:
                if primary_artist:
                    artists.append(primary_artist)

            # Support Artists
            if support:
                split_support = self._split_acts(support)
                for part in split_support:
                    part_clean = self._clean_text(part)
                    if part_clean:
                        artists.append(part_clean)
                        
            # Remove duplicate artists while preserving order
            unique_artists = []
            for a in artists:
                if a not in unique_artists:
                    unique_artists.append(a)
                    
            parsed_shows.append({
                'date': show_date.isoformat(),
                'venue': venue,
                'title': title,
                'tour': tour,
                'support_raw': support_raw_str,
                'artists': unique_artists,
                'link': link
            })
            
        return parsed_shows
