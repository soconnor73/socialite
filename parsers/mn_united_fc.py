import datetime
import json
import re
import urllib.request
import urllib.parse
from typing import List, Dict, Any
from .base import BaseParser

class MNUnitedFCParser(BaseParser):
    """
    Parser implementation for MN United FC Schedule (mnufc.com/schedule).
    Loads match details dynamically from Deltatre Forge DAPI.
    """

    def __init__(self):
        # Defensive fallbacks in case dynamic loading fails
        self.club_fallbacks = {
            'MLS-CLU-00000L': 'Minnesota United FC',
            'MLS-CLU-00001D': 'MNUFC2',
            'MLS-CLU-00000A': 'Atlanta United FC',
            'MLS-CLU-00000R': 'Real Salt Lake',
            'MLS-CLU-00000Y': 'Sporting Kansas City',
            'MLS-CLU-00000C': 'Vancouver Whitecaps FC',
            'MLS-CLU-00001G': 'St. Louis CITY SC 2',
            'MLS-CLU-000018': 'Colorado Rapids 2',
            'MLS-CLU-00000S': 'Seattle Sounders FC',
            'MLS-CLU-00000G': 'LA Galaxy',
            'MLS-CLU-000001': 'Los Angeles Football Club',
            'MLS-CLU-00001U': 'Los Angeles Football Club 2',
            'MLS-CLU-00001P': 'Sacramento Republic FC',
            'MLS-CLU-000015': 'North Texas SC',
            'MLS-CLU-000012': 'Portland Timbers 2',
            'MLS-CLU-00000K': 'Sporting Kansas City',
            'MLS-CLU-00001Q': 'Austin FC II',
            'MLS-CLU-00001B': 'Houston Dynamo 2',
            'MLS-CLU-00000X': 'Tacoma Defiance',
            'MLS-CLU-0000B5': 'Club León',
            'MLS-CLU-00002N': 'FC Juárez',
            'MLS-CLU-000065': 'San Diego FC',
            'MLS-CLU-0000B7': 'Atlante FC',
            'MLS-CLU-00002V': 'Tigres UANL',
            'MLS-CLU-000013': 'Town Club'
        }
        
        self.venue_fallbacks = {
            'MLS-STA-00000L': 'Allianz Field',
            'MLS-STA-000015': 'National Sports Center Stadium',
            'MLS-STA-00000R': 'America First Field',
            'MLS-STA-00000K': "Children's Mercy Park",
            'MLS-STA-000018': 'Q2 Stadium',
            'MLS-STA-00000Y': 'Shell Energy Stadium',
            'MLS-STA-000026': 'Swope Soccer Village',
            'MLS-STA-00006T': 'USC - Rawlinson Stadium',
            'MLS-STA-00001I': 'SeatGeek Stadium'
        }

        self.competition_fallbacks = {
            'MLS-COM-000001': 'mls-regular-season',
            'MLS-COM-000006': 'leagues-cup',
            'MLS-COM-000034': 'mls-preseason-friendlies'
        }

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = text.replace('\xa0', ' ').replace('\u00a0', ' ')
        text = text.replace('’', "'").replace('‘', "'").replace('”', '"').replace('“', '"')
        return " ".join(text.split()).strip()

    def _fetch_json(self, url: str) -> Dict[str, Any]:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read().decode('utf-8'))

    def parse(self, html_content: bytes, **kwargs) -> List[Dict[str, Any]]:
        """
        Parses the MN United FC page.
        Extracts base API URLs from HTML variables, loads team/stadium/match directories,
        and returns match show objects.
        """
        html_str = html_content.decode('utf-8', errors='ignore')
        
        # 1. Extract API bases from HTML
        club_dapi_base = "https://dapi.mnufc.com/v2"
        league_dapi_base = "https://dapi.mlssoccer.com/v2"
        
        match_club = re.search(r'forgeDAPI:\s*"([^"]+)"', html_str)
        if match_club:
            club_dapi_base = match_club.group(1).rstrip('/')
            
        match_league = re.search(r'leagueForgeDAPIv1:\s*"([^"]+)"', html_str)
        if match_league:
            # Substitute v1 with v2 if appropriate or use as is
            league_dapi_base = match_league.group(1).rstrip('/')
            
        print(f"[MNUFC Parser] Resolved club DAPI: {club_dapi_base}")
        print(f"[MNUFC Parser] Resolved league DAPI: {league_dapi_base}")

        # 2. Build maps dynamically with paging
        club_map = dict(self.club_fallbacks)
        venue_map = dict(self.venue_fallbacks)
        comp_map = dict(self.competition_fallbacks)

        # Query clubs (page-by-page since capped)
        try:
            skip = 0
            limit = 100
            loaded_clubs = 0
            # Fetch up to 4 pages of clubs (400 items) to cover MLS Next Pro and Leagues Cup opponents
            for page in range(4):
                clubs_url = f"{league_dapi_base.replace('/v1', '/v2')}/content/en-us/clubs?$skip={skip}&$limit={limit}"
                clubs_data = self._fetch_json(clubs_url)
                items = clubs_data.get('items', [])
                if not items:
                    break
                for c in items:
                    fields = c.get('fields', {})
                    name = fields.get('name')
                    sp_id = fields.get('sportecId')
                    opt_id = fields.get('optaId')
                    if name:
                        if sp_id: club_map[sp_id] = name
                        if opt_id: club_map[opt_id] = name
                loaded_clubs += len(items)
                if len(items) < limit:
                    break
                skip += limit
            print(f"[MNUFC Parser] Dynamically loaded {loaded_clubs} clubs.")
        except Exception as ex:
            print(f"[MNUFC Parser] Warning: Dynamic club load failed: {ex}. Using fallbacks.")

        # Query venues (page-by-page since capped at 25)
        try:
            skip = 0
            limit = 100
            loaded_venues = 0
            # Fetch up to 4 pages of venues (400 items) to cover active MLS stadiums
            for page in range(4):
                venues_url = f"{league_dapi_base.replace('/v1', '/v2')}/content/en-us/venues?$skip={skip}&$limit={limit}"
                venues_data = self._fetch_json(venues_url)
                items = venues_data.get('items', [])
                if not items:
                    break
                for v in items:
                    fields = v.get('fields', {})
                    name = fields.get('name')
                    sp_id = fields.get('sportecId')
                    opt_id = fields.get('optaId')
                    if name:
                        if sp_id: venue_map[sp_id] = name
                        if opt_id: venue_map[opt_id] = name
                loaded_venues += len(items)
                if len(items) < limit:
                    break
                skip += limit
            print(f"[MNUFC Parser] Dynamically loaded {loaded_venues} venues.")
        except Exception as ex:
            print(f"[MNUFC Parser] Warning: Dynamic venue load failed: {ex}. Using fallbacks.")

        # Query competitions
        try:
            comp_url = f"{league_dapi_base.replace('/v1', '/v2')}/content/en-us/competitions?$limit=100"
            comp_data = self._fetch_json(comp_url)
            for c in comp_data.get('items', []):
                fields = c.get('fields', {})
                sp_id = fields.get('sportecId')
                slug = c.get('slug')
                if slug and sp_id:
                    comp_map[sp_id] = slug
            print(f"[MNUFC Parser] Dynamically loaded {len(comp_data.get('items', []))} competitions.")
        except Exception as ex:
            print(f"[MNUFC Parser] Warning: Dynamic competition load failed: {ex}. Using fallbacks.")

        # 3. Target ranges
        # Target dates are June 20, 2026 to August 19, 2026
        target_start = datetime.date(2026, 6, 20)
        target_end = datetime.date(2026, 8, 19)

        # 4. Fetch and page matches
        all_matches = []
        skip = 0
        limit = 25
        while True:
            matches_url = f"{club_dapi_base}/content/en-us/matches?$skip={skip}&$limit={limit}"
            try:
                matches_data = self._fetch_json(matches_url)
                items = matches_data.get('items', [])
                if not items:
                    break
                all_matches.extend(items)
                
                # Check the date of the last item to stop paging
                last_dt_str = items[-1].get('fields', {}).get('matchDateTime')
                if last_dt_str:
                    last_utc_dt = datetime.datetime.fromisoformat(last_dt_str.replace('Z', '+00:00'))
                    last_local_date = (last_utc_dt - datetime.timedelta(hours=5)).date()
                    if last_local_date < target_start:
                        break
                skip += limit
            except Exception as ex:
                print(f"[MNUFC Parser] Match fetch page failed: {ex}")
                break

        print(f"[MNUFC Parser] Fetched {len(all_matches)} matches in total. Filtering by date range...")

        parsed_shows = []
        for match in all_matches:
            fields = match.get('fields', {})
            dt_str = fields.get('matchDateTime')
            if not dt_str:
                continue

            # Parse datetime and shift to Central Time (UTC -5 hours)
            utc_dt = datetime.datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            local_dt = utc_dt - datetime.timedelta(hours=5)
            match_date = local_dt.date()

            # Filter to 60-day window
            if target_start <= match_date <= target_end:
                h_id = fields.get('homeClubSportecId')
                a_id = fields.get('awayClubSportecId')
                v_id = fields.get('venueSportecId')
                comp_id = fields.get('competitionSportecId')
                season_year = fields.get('seasonOptaId') or 2026

                home_name = club_map.get(h_id) or self.club_fallbacks.get(h_id) or f"Club {h_id}"
                away_name = club_map.get(a_id) or self.club_fallbacks.get(a_id) or f"Club {a_id}"
                venue_name = venue_map.get(v_id) or self.venue_fallbacks.get(v_id) or "Allianz Field"
                comp_slug = comp_map.get(comp_id) or self.competition_fallbacks.get(comp_id) or "mls-regular-season"

                # Filter: Only keep events at Allianz Field
                if venue_name != "Allianz Field":
                    continue

                # Standardize home/away display
                title = f"{home_name} vs. {away_name}"
                title = self._clean_text(title)
                
                # Link format
                slug = match.get('slug') or f"match-{match_date.isoformat()}"
                link = f"https://www.mnufc.com/competitions/{comp_slug}/{season_year}/matches/{slug}"

                # Artists: list home and away clubs
                artists = [home_name, away_name]

                # Tour info
                tour = fields.get('leagueMatchTitle') or fields.get('matchType') or "MLS Match"
                tour = self._clean_text(tour)

                # Support/Sponsor raw info
                support = ""
                sponsor_info = fields.get('promotionalSponsor', {})
                if sponsor_info and sponsor_info.get('displayText'):
                    support = self._clean_text(sponsor_info.get('displayText'))

                parsed_shows.append({
                    'date': match_date.isoformat(),
                    'venue': venue_name,
                    'title': title,
                    'tour': tour,
                    'support_raw': support,
                    'artists': artists,
                    'link': link
                })

        print(f"[MNUFC Parser] Extracted {len(parsed_shows)} matches inside range.")
        return parsed_shows
