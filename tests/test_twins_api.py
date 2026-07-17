import urllib.request
import urllib.parse
import json

url = "https://statsapi.mlb.com/api/v1/schedule"
params = {
    'sportId': 1,
    'teamId': 142,
    'startDate': '2026-06-20',
    'endDate': '2026-08-19'
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

query_str = urllib.parse.urlencode(params)
full_url = f"{url}?{query_str}"
print(f"Fetching from: {full_url}")

req = urllib.request.Request(full_url, headers=headers)
try:
    with urllib.request.urlopen(req) as res:
        data = res.read()
        parsed = json.loads(data.decode('utf-8'))
        print("Success! Keys in response:", parsed.keys())
        print(f"totalGames: {parsed.get('totalGames')}")
        
        dates = parsed.get('dates', [])
        print(f"Number of dates with games: {len(dates)}")
        if dates:
            first_date = dates[0]
            print("\nFirst date details:")
            print("  date:", first_date.get('date'))
            games = first_date.get('games', [])
            print(f"  Number of games on this date: {len(games)}")
            if games:
                first_game = games[0]
                print("\nFirst game details keys:", first_game.keys())
                print("\nFirst game details:")
                print(json.dumps(first_game, indent=2))
                
                # Check venue, teams, home/away details
                print("\nInspect teams details:")
                teams = first_game.get('teams', {})
                for side in ['home', 'away']:
                    side_info = teams.get(side, {})
                    team_info = side_info.get('team', {})
                    print(f"  {side}: ID={team_info.get('id')}, Name={team_info.get('name')}, isHome={side_info.get('isHome')}")
                
                print(f"  Venue: ID={first_game.get('venue', {}).get('id')}, Name={first_game.get('venue', {}).get('name')}")
                
except Exception as e:
    print("Error:", e)
