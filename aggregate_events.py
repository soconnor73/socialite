import os
import json
import glob
import datetime

def aggregate():
    print("Aggregating event files...")
    event_files = glob.glob("*-events.json")
    
    all_shows = []
    seen_keys = set()
    
    for filepath in event_files:
        if filepath == "events.json":
            continue
        try:
            filename = os.path.basename(filepath)
            source = filename.replace("-events.json", "").replace("-", "_")
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                shows = data.get('shows', [])
                print(f"  Loaded {len(shows)} shows from {filepath} (source: {source})")
                for show in shows:
                    # Deduplicate based on date, title, and venue
                    date = show.get('date', '')
                    title = show.get('title', '')
                    venue = show.get('venue', '')
                    
                    key = (date, title.lower(), venue.lower())
                    if key not in seen_keys:
                        seen_keys.add(key)
                        show['source'] = source
                        all_shows.append(show)
        except Exception as e:
            print(f"  Error reading {filepath}: {e}")
            
    # Sort chronologically by date
    all_shows.sort(key=lambda s: s.get('date', ''))
    
    # Save the consolidated output
    output_filename = "events.json"
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'total_aggregated': len(all_shows),
                'aggregated_at': datetime.datetime.now().isoformat(),
                'venues_included': sorted(list(set(s.get('venue') for s in all_shows)))
            },
            'shows': all_shows
        }, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully aggregated {len(all_shows)} unique events into {output_filename}")

if __name__ == "__main__":
    aggregate()
