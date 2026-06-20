import datetime
import time
import json
import urllib.parse
import urllib.request
import os
import gzip

from parsers import get_parser

def get_page_content(url, use_cloudscraper=False):
    print(f"Fetching: {url}")
    if use_cloudscraper:
        try:
            import cloudscraper
            scraper = cloudscraper.create_scraper()
            response = scraper.get(url)
            return response.content
        except Exception as e:
            print(f"Cloudscraper fetch failed: {e}. Falling back to standard fetch.")
            
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Encoding': 'gzip, deflate'
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            content = response.read()
            if response.info().get('Content-Encoding') == 'gzip':
                content = gzip.decompress(content)
            return content
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def scrape_site(site_name, start_date, end_date):
    print(f"\n--- Scraping {site_name} from {start_date} to {end_date} ---")
    
    try:
        parser = get_parser(site_name)
    except Exception as e:
        print(f"Failed to load parser for {site_name}: {e}")
        return

    all_shows = []

    if site_name == 'first_avenue':
        # June, July, August 2026
        months_to_query = [
            (2026, 6, "20260601"),
            (2026, 7, "20260701"),
            (2026, 8, "20260801")
        ]
        for year, month, start_date_str in months_to_query:
            filepath = f"raw_html/shows_{start_date_str}.html"
            html = None
            if os.path.exists(filepath):
                print(f"Using cached file: {filepath}")
                with open(filepath, 'rb') as f:
                    html = f.read()
            else:
                url = f"https://first-avenue.com/shows?post_type=event&start_date={start_date_str}"
                html = get_page_content(url)
                if html:
                    os.makedirs("raw_html", exist_ok=True)
                    with open(filepath, "wb") as f:
                        f.write(html)
                    time.sleep(1)
            if html:
                shows = parser.parse(html, year=year)
                print(f"Parsed {len(shows)} shows from {start_date_str}")
                all_shows.extend(shows)
                
    elif site_name == 'grand_casino_arena':
        filepath = "raw_html/grand_casino_events.html"
        html = None
        if os.path.exists(filepath):
            print(f"Using cached file: {filepath}")
            with open(filepath, 'rb') as f:
                html = f.read()
        else:
            url = "https://www.grandcasinoarena.com/events"
            html = get_page_content(url)
            if html:
                os.makedirs("raw_html", exist_ok=True)
                with open(filepath, "wb") as f:
                    f.write(html)
                time.sleep(1)
        if html:
            shows = parser.parse(html)
            print(f"Parsed {len(shows)} shows from grandcasinoarena.com")
            all_shows.extend(shows)

    elif site_name == 'acme_comedy_club':
        filepath = "raw_html/acme_comedy_club.html"
        html = None
        if os.path.exists(filepath):
            print(f"Using cached file: {filepath}")
            with open(filepath, 'rb') as f:
                html = f.read()
        else:
            url = "https://acmecomedycompany.com/"
            html = get_page_content(url)
            if html:
                os.makedirs("raw_html", exist_ok=True)
                with open(filepath, "wb") as f:
                    f.write(html)
                time.sleep(1)
        if html:
            shows = parser.parse(html)
            print(f"Parsed {len(shows)} shows from acmecomedycompany.com")
            all_shows.extend(shows)

    elif site_name == 'guthrie_theater':
        filepath = "raw_html/guthrie_theater.html"
        html = None
        if os.path.exists(filepath):
            print(f"Using cached file: {filepath}")
            with open(filepath, 'rb') as f:
                html = f.read()
        else:
            url = "https://www.guthrietheater.org/"
            html = get_page_content(url, use_cloudscraper=True)
            if html:
                os.makedirs("raw_html", exist_ok=True)
                with open(filepath, "wb") as f:
                    f.write(html)
                time.sleep(1)
        if html:
            shows = parser.parse(html)
            print(f"Parsed {len(shows)} shows from guthrietheater.org")
            all_shows.extend(shows)

    elif site_name == 'minneapolis':
        page = 1
        max_pages = 100 # Increased safeguard page limit to support the full 60-day window
        
        while page <= max_pages:
            filepath = f"raw_html/minneapolis_page_{page}.html"
            html = None
            if os.path.exists(filepath):
                print(f"Using cached file: {filepath}")
                with open(filepath, 'rb') as f:
                    html = f.read()
            else:
                url = f"https://www.minneapolis.org/calendar/?page={page}&"
                html = get_page_content(url)
                if html:
                    os.makedirs("raw_html", exist_ok=True)
                    with open(filepath, "wb") as f:
                        f.write(html)
                    time.sleep(1)
                    
            if not html:
                break
                
            shows = parser.parse(html)
            print(f"Parsed {len(shows)} shows from page {page}")
            if not shows:
                break
                
            all_shows.extend(shows)
            
            # Check if all shows on this page start after the target end_date
            all_past_target = True
            for show in shows:
                show_start = datetime.date.fromisoformat(show['date'])
                if show_start <= end_date:
                    all_past_target = False
                    break
                    
            if all_past_target:
                print(f"Stopping pagination: all shows on page {page} start after {end_date}")
                break
                
            page += 1

    elif site_name == 'mn_united_fc':
        filepath = "raw_html/mnufc_schedule.html"
        html = None
        if os.path.exists(filepath):
            print(f"Using cached file: {filepath}")
            with open(filepath, 'rb') as f:
                html = f.read()
        else:
            url = "https://www.mnufc.com/schedule/"
            html = get_page_content(url)
            if html:
                os.makedirs("raw_html", exist_ok=True)
                with open(filepath, "wb") as f:
                    f.write(html)
                time.sleep(1)
        if html:
            shows = parser.parse(html)
            print(f"Parsed {len(shows)} shows from mnufc.com")
            all_shows.extend(shows)

    elif site_name == 'minnesota_twins':
        # June, July, August 2026
        months_to_query = [
            (2026, 6, "2026-06"),
            (2026, 7, "2026-07"),
            (2026, 8, "2026-08")
        ]
        for year, month, date_str in months_to_query:
            filepath = f"raw_html/twins_schedule_{date_str}.html"
            html = None
            if os.path.exists(filepath):
                print(f"Using cached file: {filepath}")
                with open(filepath, 'rb') as f:
                    html = f.read()
            else:
                url = f"https://www.mlb.com/twins/schedule/{date_str}"
                html = get_page_content(url)
                if html:
                    os.makedirs("raw_html", exist_ok=True)
                    with open(filepath, "wb") as f:
                        f.write(html)
                    time.sleep(1)
            if html:
                shows = parser.parse(html, year=year, month=month)
                print(f"Parsed {len(shows)} shows from {date_str}")
                all_shows.extend(shows)

    elif site_name == 'target_center':
        filepath = "raw_html/target_center_events.html"
        html = None
        if os.path.exists(filepath):
            print(f"Using cached file: {filepath}")
            with open(filepath, 'rb') as f:
                html = f.read()
        else:
            url = "https://www.targetcenter.com/events"
            html = get_page_content(url)
            if html:
                os.makedirs("raw_html", exist_ok=True)
                with open(filepath, "wb") as f:
                    f.write(html)
                time.sleep(1)
        if html:
            shows = parser.parse(html)
            print(f"Parsed {len(shows)} shows from targetcenter.com")
            all_shows.extend(shows)

    elif site_name == 'minnesota_orchestra':
        filepath = "raw_html/orchestra_calendar.html"
        html = None
        if os.path.exists(filepath):
            print(f"Using cached file: {filepath}")
            with open(filepath, 'rb') as f:
                html = f.read()
        else:
            url = "https://www.minnesotaorchestra.org/tickets/calendar"
            html = get_page_content(url)
            if html:
                os.makedirs("raw_html", exist_ok=True)
                with open(filepath, "wb") as f:
                    f.write(html)
                time.sleep(1)
        if html:
            shows = parser.parse(html)
            print(f"Parsed {len(shows)} shows from minnesotaorchestra.org")
            all_shows.extend(shows)

    elif site_name == 'hennepin_arts':
        filepath = "raw_html/hennepin_arts.html"
        html = None
        if os.path.exists(filepath):
            print(f"Using cached file: {filepath}")
            with open(filepath, 'rb') as f:
                html = f.read()
        else:
            url = "https://hennepinarts.org/whats-on/event-calendar"
            html = get_page_content(url)
            if html:
                os.makedirs("raw_html", exist_ok=True)
                with open(filepath, "wb") as f:
                    f.write(html)
                time.sleep(1)
        if html:
            shows = parser.parse(html)
            print(f"Parsed {len(shows)} shows from hennepinarts.org")
            all_shows.extend(shows)

    elif site_name == 'us_bank_stadium':
        filepath = "raw_html/us_bank_stadium.html"
        html = None
        if os.path.exists(filepath):
            print(f"Using cached file: {filepath}")
            with open(filepath, 'rb') as f:
                html = f.read()
        else:
            url = "https://www.usbankstadium.com/events"
            html = get_page_content(url)
            if html:
                os.makedirs("raw_html", exist_ok=True)
                with open(filepath, "wb") as f:
                    f.write(html)
                time.sleep(1)
        if html:
            shows = parser.parse(html)
            print(f"Parsed {len(shows)} shows from usbankstadium.com")
            all_shows.extend(shows)

    elif site_name == 'northrop_auditorium':
        filepath = "raw_html/northrop_auditorium.html"
        html = None
        if os.path.exists(filepath):
            print(f"Using cached file: {filepath}")
            with open(filepath, 'rb') as f:
                html = f.read()
        else:
            url = "https://www.northrop.umn.edu/upcoming-events"
            html = get_page_content(url)
            if html:
                os.makedirs("raw_html", exist_ok=True)
                with open(filepath, "wb") as f:
                    f.write(html)
                time.sleep(1)
        if html:
            shows = parser.parse(html)
            print(f"Parsed {len(shows)} shows from northrop.umn.edu")
            all_shows.extend(shows)

    elif site_name == 'ordway_theater':
        filepath = "raw_html/ordway.html"
        html = None
        if os.path.exists(filepath):
            print(f"Using cached file: {filepath}")
            with open(filepath, 'rb') as f:
                html = f.read()
        else:
            url = "https://ordway.org/events/"
            html = get_page_content(url)
            if html:
                os.makedirs("raw_html", exist_ok=True)
                with open(filepath, "wb") as f:
                    f.write(html)
                time.sleep(1)
        if html:
            shows = parser.parse(html)
            print(f"Parsed {len(shows)} shows from ordway.org")
            all_shows.extend(shows)

    # Filter shows to target 60-day window
    # Supports both single dates and date range checks
    filtered_shows = []
    for show in all_shows:
        s_date = datetime.date.fromisoformat(show['date'])
        # If show doesn't have an end_date, fall back to start date
        e_date = datetime.date.fromisoformat(show['end_date']) if show.get('end_date') else s_date
        
        # Check if the show's date range [s_date, e_date] overlaps with the target [start_date, end_date]
        if s_date <= end_date and e_date >= start_date:
            filtered_shows.append(show)

    print(f"Total shows collected: {len(all_shows)}")
    print(f"Total shows in 60-day window: {len(filtered_shows)}")

    # Name of the output file reflects the parser
    output_filename = f"{site_name.replace('_', '-')}-events.json"
    
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'site': site_name,
                'scraping_time': datetime.datetime.now().isoformat(),
                'start_date_range': start_date.isoformat(),
                'end_date_range': end_date.isoformat(),
                'total_shows_extracted': len(filtered_shows)
            },
            'shows': filtered_shows
        }, f, indent=2, ensure_ascii=False)

    print(f"Structured data saved to {output_filename}")

def main():
    # Set target timeframe: 120 days starting 2026-06-20
    start_date = datetime.date(2026, 6, 20)
    end_date = start_date + datetime.timedelta(days=120)
    
    # List of sites to scrape
    sites_to_scrape = ['first_avenue', 'grand_casino_arena', 'acme_comedy_club', 'guthrie_theater', 'minneapolis', 'mn_united_fc', 'minnesota_twins', 'target_center', 'minnesota_orchestra', 'hennepin_arts', 'us_bank_stadium', 'northrop_auditorium', 'ordway_theater']
    
    for site in sites_to_scrape:
        scrape_site(site, start_date, end_date)

if __name__ == "__main__":
    main()
