import json
import datetime
import re
from typing import List, Dict, Any
from .base import BaseParser


class FillmoreMinneapolisParser(BaseParser):
    """
    Parser for Fillmore Minneapolis.
    URL: https://www.fillmoreminneapolis.com/shows
    Extracts structured schema.org JSON-LD elements from the server-rendered Next.js page.
    """

    def parse(self, html_content: bytes, **kwargs) -> List[Dict[str, Any]]:
        try:
            content = html_content.decode('utf-8', errors='ignore')
        except Exception:
            return []

        # Fix backslash escapes inside Next.js data scripts
        fixed_content = content.replace('\\\\\\"', '"').replace('\\\\"', '"').replace('\\"', '"')

        # Since titles can have unescaped nested double quotes (e.g. "Connor Price & Nic D "Iconic Tour""),
        # direct json.loads will fail. Let's extract values with regex instead.
        pattern = r'"@type"\s*:\s*"MusicEvent"\s*,\s*"name"\s*:\s*"([^\"]+)".*?"startDate"\s*:\s*"([^\"]+)".*?"url"\s*:\s*"([^\"]+)"'
        matches = re.findall(pattern, fixed_content)

        shows: List[Dict[str, Any]] = []
        seen_keys = set()

        for name, start_raw, url in matches:
            # First, strip trailing/leading backslashes, quotes, and whitespace so unicode_escape doesn't fail
            name = re.sub(r'[\s\\"]+$', '', name)
            name = re.sub(r'^[\s\\"]+', '', name)

            # Unescape unicode escapes (e.g. \u0026 or \\u0026)
            for _ in range(3):
                if '\\u' not in name:
                    break
                try:
                    name = name.encode('utf-8').decode('unicode_escape')
                except Exception:
                    break

            # Strip again in case unescaping introduced any leading/trailing garbage
            name = re.sub(r'[\s\\"]+$', '', name)
            name = re.sub(r'^[\s\\"]+', '', name)

            # HTML unescape and final strip
            import html
            name = html.unescape(name).strip()

            if not name or not start_raw:
                continue

            try:
                date_str = start_raw[:10]
                datetime.date.fromisoformat(date_str)
            except Exception:
                continue

            time_str = ''
            if len(start_raw) >= 19:
                try:
                    dt = datetime.datetime.fromisoformat(start_raw)
                    hour = dt.hour % 12 or 12
                    ampm = 'AM' if dt.hour < 12 else 'PM'
                    time_str = f"{hour}:{dt.minute:02d} {ampm}"
                except Exception:
                    pass

            if url and not url.startswith('http'):
                url = 'https://www.fillmoreminneapolis.com' + url

            key = (date_str, name.lower())
            if key in seen_keys:
                continue
            seen_keys.add(key)

            shows.append({
                'date': date_str,
                'end_date': date_str,
                'venue': 'The Fillmore Minneapolis',
                'title': name,
                'tour': 'Concert',
                'support_raw': time_str,
                'artists': [name],
                'link': url
            })

        return shows
