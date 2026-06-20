import datetime
import json
import calendar
import urllib.request
from typing import List, Dict, Any
from .base import BaseParser

class MinnesotaTwinsParser(BaseParser):
    """
    Parser implementation for Minnesota Twins Schedule (mlb.com/twins/schedule).
    Fetches game data from statsapi.mlb.com for the specified year and month.
    """

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = text.replace('\xa0', ' ').replace('\u00a0', ' ')
        text = text.replace('’', "'").replace('‘', "'").replace('”', '"').replace('“', '"')
        return " ".join(text.split()).strip()

    def parse(self, html_content: bytes, **kwargs) -> List[Dict[str, Any]]:
        """
        Parses Twins schedule events.
        Args:
            html_content: Raw HTML page from mlb.com (ignored in favor of MLB Stats API).
            **kwargs: Must contain 'year' and 'month'.
        """
        year = kwargs.get('year', 2026)
        month = kwargs.get('month', 6)
        
        last_day = calendar.monthrange(year, month)[1]
        start_date = f"{year:04d}-{month:02d}-01"
        end_date = f"{year:04d}-{month:02d}-{last_day:02d}"
        
        url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId=142&startDate={start_date}&endDate={end_date}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        parsed_shows = []
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req) as res:
                parsed = json.loads(res.read().decode('utf-8'))
                dates = parsed.get('dates', [])
                for d in dates:
                    for game in d.get('games', []):
                        teams = game.get('teams', {})
                        home_team = teams.get('home', {}).get('team', {})
                        home_team_id = home_team.get('id')
                        
                        # Only keep home games (Twins is home team with ID 142)
                        if home_team_id != 142:
                            continue
                            
                        away_team = teams.get('away', {}).get('team', {})
                        away_name = away_team.get('name', 'Opponent')
                        home_name = home_team.get('name', 'Minnesota Twins')
                        
                        # Normalize text values
                        home_name = self._clean_text(home_name)
                        away_name = self._clean_text(away_name)
                        venue = self._clean_text(game.get('venue', {}).get('name', 'Target Field'))
                        
                        title = f"{home_name} vs. {away_name}"
                        tour = self._clean_text(game.get('seriesDescription', 'Regular Season'))
                        if tour == "Regular Season":
                            tour = "MLB Regular Season"
                            
                        link = f"https://www.mlb.com/gameday/{game.get('gamePk')}"
                        artists = [home_name, away_name]
                        date = game.get('officialDate') # YYYY-MM-DD
                        
                        parsed_shows.append({
                            'date': date,
                            'venue': venue,
                            'title': title,
                            'tour': tour,
                            'support_raw': "",
                            'artists': artists,
                            'link': link
                        })
        except Exception as e:
            print(f"[Twins Parser] Error fetching schedule: {e}")
            
        return parsed_shows
