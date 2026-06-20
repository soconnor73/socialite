import datetime
import json
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from .base import BaseParser

class HennepinArtsParser(BaseParser):
    """
    Parser implementation for Hennepin Arts (hennepinarts.org).
    """

    def __init__(self):
        pass

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = text.replace('\xa0', ' ').replace('\u00a0', ' ')
        text = text.replace('’', "'").replace('‘', "'").replace('”', '"').replace('“', '"')
        return " ".join(text.split()).strip()

    def _resolve(self, val: Any, data: List[Any], depth: int = 0, visited: set = None) -> Any:
        if depth > 10:
            return val
        if visited is None:
            visited = set()
            
        if isinstance(val, int) and 0 <= val < len(data):
            if val in visited:
                return None
            visited.add(val)
            res = self._resolve(data[val], data, depth + 1, visited)
            visited.remove(val)
            return res
        if isinstance(val, list):
            return [self._resolve(x, data, depth + 1, visited) for x in val]
        if isinstance(val, dict):
            return {k: self._resolve(v, data, depth + 1, visited) for k, v in val.items()}
        return val

    def _format_time(self, iso_time_str: str) -> str:
        if 'T' in iso_time_str:
            time_part = iso_time_str.split('T')[1]
            parts = time_part.split(':')
            if len(parts) >= 2:
                try:
                    hour = int(parts[0])
                    minute = int(parts[1])
                    suffix = "PM" if hour >= 12 else "AM"
                    hour_12 = hour % 12
                    if hour_12 == 0:
                        hour_12 = 12
                    return f"{hour_12}:{minute:02d} {suffix}"
                except ValueError:
                    pass
            return time_part
        return ""

    def _extract_artists(self, title: str) -> List[str]:
        cleaned_title = self._clean_text(title)
        parts = re.split(r'\b(?:and|with)\b|&', cleaned_title, flags=re.IGNORECASE)
        artists = []
        for part in parts:
            p_clean = self._clean_text(part)
            if p_clean:
                artists.append(p_clean)
        if not artists:
            artists = [cleaned_title]
        return artists

    def parse(self, html_content: bytes, **kwargs) -> List[Dict[str, Any]]:
        """
        Parses Hennepin Arts event calendar HTML content.
        """
        soup = BeautifulSoup(html_content, 'html.parser', from_encoding='utf-8')
        
        target_script = None
        for s in soup.find_all('script'):
            if s.get('type') == 'application/json':
                content = s.get_text()
                if len(content) > 100000:
                    target_script = s
                    break
                    
        if not target_script:
            return []
            
        try:
            data = json.loads(target_script.get_text())
        except Exception:
            return []
            
        if not isinstance(data, list):
            return []
            
        # Build name -> slug mapping from the flat payload graph
        slug_map = {}
        for item in data:
            if isinstance(item, dict):
                name = self._resolve(item.get('name'), data) or self._resolve(item.get('entryTitle'), data)
                slug = self._resolve(item.get('slug'), data)
                if name and slug:
                    slug_map[str(name).strip().lower()] = str(slug).strip()
                    
        parsed_shows = []
        seen_events = set()
        
        for item in data:
            if isinstance(item, dict) and 'title' in item and 'startDate' in item:
                title = self._resolve(item.get('title'), data)
                start_date_raw = self._resolve(item.get('startDate'), data)
                
                if not title or not start_date_raw:
                    continue
                    
                # Split title: e.g. "Events > Wicked > July 9, 2026 > Thur eve"
                title_parts = [x.strip() for x in title.split('>')]
                if len(title_parts) >= 2:
                    show_title = title_parts[1]
                else:
                    show_title = title
                    
                show_title = self._clean_text(show_title)
                if not show_title:
                    continue
                    
                # Parse date and format time
                if 'T' in start_date_raw:
                    date_str = start_date_raw.split('T')[0]
                    time_str = self._format_time(start_date_raw)
                else:
                    date_str = start_date_raw
                    time_str = "Hennepin Arts Event"
                    
                # Verify date format is valid
                if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                    continue
                    
                # Link resolution
                link = ""
                show_title_clean = show_title.lower()
                if show_title_clean in slug_map:
                    slug = slug_map[show_title_clean]
                    if '/' in slug:
                        link = "https://hennepinarts.org/" + slug
                    else:
                        link = "https://hennepinarts.org/events/" + slug
                else:
                    tickets_url = self._resolve(item.get('ticketsUrl'), data)
                    if tickets_url:
                        link = tickets_url
                    else:
                        # Fallback: slugify name
                        slug = re.sub(r'[^a-z0-9]+', '-', show_title_clean).strip('-')
                        link = "https://hennepinarts.org/events/" + slug
                        
                # Deduplicate by key
                event_key = (date_str, show_title, time_str, link)
                if event_key in seen_events:
                    continue
                seen_events.add(event_key)
                
                artists = self._extract_artists(show_title)
                
                parsed_shows.append({
                    'date': date_str,
                    'end_date': date_str,
                    'venue': 'Hennepin Arts',
                    'title': show_title,
                    'tour': time_str if time_str else "Hennepin Arts Event",
                    'support_raw': "",
                    'artists': artists,
                    'link': link
                })
                
        return parsed_shows
