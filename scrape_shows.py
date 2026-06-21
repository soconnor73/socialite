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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
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

def get_month_windows(start_date, end_date):
    windows = []
    curr = start_date
    while curr <= end_date:
        if curr.month == 12:
            next_month = datetime.date(curr.year + 1, 1, 1)
        else:
            next_month = datetime.date(curr.year, curr.month + 1, 1)
        month_end = next_month - datetime.timedelta(days=1)
        range_end = min(month_end, end_date)
        windows.append((curr.strftime('%Y-%m-%d'), range_end.strftime('%Y-%m-%d')))
        curr = next_month
    return windows

def get_month_strings(start_date, end_date):
    months = []
    curr = datetime.date(start_date.year, start_date.month, 1)
    while curr <= end_date:
        months.append(curr.strftime('%Y-%m'))
        if curr.month == 12:
            curr = datetime.date(curr.year + 1, 1, 1)
        else:
            curr = datetime.date(curr.year, curr.month + 1, 1)
    return months

def get_first_avenue_months(start_date, end_date):
    months = []
    curr = datetime.date(start_date.year, start_date.month, 1)
    while curr <= end_date:
        months.append((curr.year, curr.month, curr.strftime('%Y%m01')))
        if curr.month == 12:
            curr = datetime.date(curr.year + 1, 1, 1)
        else:
            curr = datetime.date(curr.year, curr.month + 1, 1)
    return months

def get_twins_months(start_date, end_date):
    months = []
    curr = datetime.date(start_date.year, start_date.month, 1)
    while curr <= end_date:
        months.append((curr.year, curr.month, curr.strftime('%Y-%m')))
        if curr.month == 12:
            curr = datetime.date(curr.year + 1, 1, 1)
        else:
            curr = datetime.date(curr.year, curr.month + 1, 1)
    return months

def scrape_site(site_name, start_date, end_date):
    print(f"\n--- Scraping {site_name} from {start_date} to {end_date} ---")
    
    try:
        parser = get_parser(site_name)
    except Exception as e:
        print(f"Failed to load parser for {site_name}: {e}")
        return

    all_shows = []

    if site_name == 'first_avenue':
        months_to_query = get_first_avenue_months(start_date, end_date)
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
        months_to_query = get_twins_months(start_date, end_date)
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

    elif site_name == 'visit_stpaul':
        filepath = "raw_html/visit_stpaul.html"
        html = None
        if os.path.exists(filepath):
            print(f"Using cached file: {filepath}")
            with open(filepath, 'rb') as f:
                html = f.read()
        else:
            url = "https://www.visitsaintpaul.com/events-calendar/"
            html = get_page_content(url)
            if html:
                os.makedirs("raw_html", exist_ok=True)
                with open(filepath, "wb") as f:
                    f.write(html)
                time.sleep(1)
        if html:
            shows = parser.parse(html)
            print(f"Parsed {len(shows)} shows from visitsaintpaul.com")
            all_shows.extend(shows)

    elif site_name == 'dakota_jazz_club':
        # Dakota uses a monthly calendar view
        months_to_fetch = get_month_strings(start_date, end_date)
        for month_str in months_to_fetch:
            filepath = f"raw_html/dakota_jazz_club_{month_str}.html"
            html = None
            if os.path.exists(filepath):
                print(f"Using cached file: {filepath}")
                with open(filepath, 'rb') as f:
                    html = f.read()
            else:
                url = f"https://www.dakotacooks.com/events/month/{month_str}/"
                html = get_page_content(url)
                if html:
                    os.makedirs("raw_html", exist_ok=True)
                    with open(filepath, "wb") as f:
                        f.write(html)
                    time.sleep(1)
            if html:
                shows = parser.parse(html)
                print(f"Parsed {len(shows)} shows from dakotacooks.com ({month_str})")
                all_shows.extend(shows)

    elif site_name == 'berlin_jazz_club':
        filepath = "raw_html/berlin_jazz_club.html"
        html = None
        if os.path.exists(filepath):
            print(f"Using cached file: {filepath}")
            with open(filepath, 'rb') as f:
                html = f.read()
        else:
            url = "https://www.berlinmpls.com/calendar"
            html = get_page_content(url)
            if html:
                os.makedirs("raw_html", exist_ok=True)
                with open(filepath, "wb") as f:
                    f.write(html)
                time.sleep(1)
        if html:
            shows = parser.parse(html)
            print(f"Parsed {len(shows)} shows from berlinmpls.com")
            all_shows.extend(shows)

    elif site_name == 'crooners':
        # Crooners uses Tribe monthly calendar view
        months_to_fetch = get_month_strings(start_date, end_date)
        for month_str in months_to_fetch:
            filepath = f"raw_html/crooners_month_{month_str}.html"
            html = None
            if os.path.exists(filepath):
                print(f"Using cached file: {filepath}")
                with open(filepath, 'rb') as f:
                    html = f.read()
            else:
                url = f"https://www.croonersmn.com/events/month/{month_str}/"
                html = get_page_content(url)
                if html:
                    os.makedirs("raw_html", exist_ok=True)
                    with open(filepath, "wb") as f:
                        f.write(html)
                    time.sleep(1)
            if html:
                shows = parser.parse(html)
                print(f"Parsed {len(shows)} shows from croonersmn.com ({month_str})")
                all_shows.extend(shows)

    elif site_name == 'visit_duluth':
        # Visit Duluth uses Tribe REST API — HTML month pages require JS navigation
        # Fetch paginated API responses for each month in the target window
        api_base = 'https://visitduluth.com/wp-json/tribe/events/v1/events'
        month_windows = get_month_windows(start_date, end_date)
        for (w_start, w_end) in month_windows:
            page = 1
            while True:
                cache_key = f"{w_start}_{w_end}_p{page}"
                filepath = f"raw_html/visit_duluth_{cache_key}.json"
                raw = None
                if os.path.exists(filepath):
                    print(f"Using cached file: {filepath}")
                    with open(filepath, 'rb') as f:
                        raw = f.read()
                else:
                    url = (f"{api_base}?start_date={w_start}&end_date={w_end}"
                           f"&per_page=50&page={page}")
                    raw = get_page_content(url)
                    if raw:
                        os.makedirs("raw_html", exist_ok=True)
                        with open(filepath, 'wb') as f:
                            f.write(raw)
                        time.sleep(0.5)
                if not raw:
                    break
                shows = parser.parse(raw)
                print(f"Parsed {len(shows)} shows from visitduluth.com ({w_start} p{page})")
                all_shows.extend(shows)
                # Check if more pages exist
                try:
                    import json as _json
                    data = _json.loads(raw)
                    total = int(data.get('total', 0))
                    fetched_so_far = (page - 1) * 50 + len(shows)
                    if fetched_so_far >= total:
                        break
                except Exception:
                    break
                page += 1

    elif site_name == 'luminary_arts_center':
        # Luminary Arts Center uses Tribe REST API
        api_base = 'https://luminaryartscenter.com/wp-json/tribe/events/v1/events'
        month_windows = get_month_windows(start_date, end_date)
        for (w_start, w_end) in month_windows:
            page = 1
            while True:
                cache_key = f"{w_start}_{w_end}_p{page}"
                filepath = f"raw_html/luminary_arts_center_{cache_key}.json"
                raw = None
                if os.path.exists(filepath):
                    print(f"Using cached file: {filepath}")
                    with open(filepath, 'rb') as f:
                        raw = f.read()
                else:
                    url = (f"{api_base}?start_date={w_start}&end_date={w_end}"
                           f"&per_page=50&page={page}")
                    raw = get_page_content(url)
                    if raw:
                        os.makedirs("raw_html", exist_ok=True)
                        with open(filepath, 'wb') as f:
                            f.write(raw)
                        time.sleep(0.5)
                if not raw:
                    break
                shows = parser.parse(raw)
                print(f"Parsed {len(shows)} shows from luminaryartscenter.com ({w_start} p{page})")
                all_shows.extend(shows)
                # Check if more pages exist
                try:
                    import json as _json
                    data = _json.loads(raw)
                    total = int(data.get('total', 0))
                    fetched_so_far = (page - 1) * 50 + len(shows)
                    if fetched_so_far >= total:
                        break
                except Exception:
                    break
                page += 1

    elif site_name == 'utepils_brewery':
        # Utepils Brewery uses Tribe REST API
        api_base = 'https://www.utepilsbrewing.com/wp-json/tribe/events/v1/events'
        month_windows = get_month_windows(start_date, end_date)
        for (w_start, w_end) in month_windows:
            page = 1
            while True:
                cache_key = f"{w_start}_{w_end}_p{page}"
                filepath = f"raw_html/utepils_brewery_{cache_key}.json"
                raw = None
                if os.path.exists(filepath):
                    print(f"Using cached file: {filepath}")
                    with open(filepath, 'rb') as f:
                        raw = f.read()
                else:
                    url = (f"{api_base}?start_date={w_start}&end_date={w_end}"
                           f"&per_page=50&page={page}")
                    raw = get_page_content(url)
                    if raw:
                        os.makedirs("raw_html", exist_ok=True)
                        with open(filepath, 'wb') as f:
                            f.write(raw)
                        time.sleep(0.5)
                if not raw:
                    break
                shows = parser.parse(raw)
                print(f"Parsed {len(shows)} shows from utepilsbrewing.com ({w_start} p{page})")
                all_shows.extend(shows)
                # Check if more pages exist
                try:
                    import json as _json
                    data = _json.loads(raw)
                    total = int(data.get('total', 0))
                    fetched_so_far = (page - 1) * 50 + len(shows)
                    if fetched_so_far >= total:
                        break
                except Exception:
                    break
                page += 1

    elif site_name == 'pryes_brewing':
        filepath = "raw_html/pryes_brewing.html"
        html = None
        if os.path.exists(filepath):
            print(f"Using cached file: {filepath}")
            with open(filepath, 'rb') as f:
                html = f.read()
        else:
            url = "https://www.pryesbrewing.com/events"
            html = get_page_content(url)
            if html:
                os.makedirs("raw_html", exist_ok=True)
                with open(filepath, "wb") as f:
                    f.write(html)
                time.sleep(1)
        if html:
            shows = parser.parse(html)
            print(f"Parsed {len(shows)} shows from pryesbrewing.com")
            all_shows.extend(shows)

    elif site_name == 'mncba_workshops':
        filepath = "raw_html/mncba_workshops.html"
        html = None
        if os.path.exists(filepath):
            print(f"Using cached file: {filepath}")
            with open(filepath, 'rb') as f:
                html = f.read()
        else:
            url = "https://mnbookarts.org/category/adult-workshops"
            html = get_page_content(url)
            if html:
                os.makedirs("raw_html", exist_ok=True)
                with open(filepath, "wb") as f:
                    f.write(html)
                time.sleep(1)
        if html:
            shows = parser.parse(html)
            print(f"Parsed {len(shows)} shows from mnbookarts.org")
            all_shows.extend(shows)

    elif site_name == 'coch_cooking_classes':
        filepath = "raw_html/coch_cooking_classes.html"
        html = None
        if os.path.exists(filepath):
            print(f"Using cached file: {filepath}")
            with open(filepath, 'rb') as f:
                html = f.read()
        else:
            url = "https://cooksofcrocushill.com/cooking-classes/upcoming-classes/"
            html = get_page_content(url)
            if html:
                os.makedirs("raw_html", exist_ok=True)
                with open(filepath, "wb") as f:
                    f.write(html)
                time.sleep(1)
        if html:
            shows = parser.parse(html)
            print(f"Parsed {len(shows)} shows from cooksofcrocushill.com")
            all_shows.extend(shows)

    elif site_name == 'dame_errant_clay':
        filepath = "raw_html/dame_errant_clay.html"
        html = None
        if os.path.exists(filepath):
            print(f"Using cached file: {filepath}")
            with open(filepath, 'rb') as f:
                html = f.read()
        else:
            url = "https://www.dameerrant.com/workshopsandevents"
            html = get_page_content(url)
            if html:
                os.makedirs("raw_html", exist_ok=True)
                with open(filepath, "wb") as f:
                    f.write(html)
                time.sleep(1)
        if html:
            shows = parser.parse(html)
            print(f"Parsed {len(shows)} shows from dameerrant.com")
            all_shows.extend(shows)

    elif site_name == 'mpls_parks':
        # Minneapolis Parks uses Tribe REST API
        api_base = 'https://www.minneapolisparks.org/wp-json/tribe/events/v1/events'
        month_windows = get_month_windows(start_date, end_date)
        for (w_start, w_end) in month_windows:
            page = 1
            while True:
                cache_key = f"{w_start}_{w_end}_p{page}"
                filepath = f"raw_html/mpls_parks_{cache_key}.json"
                raw = None
                if os.path.exists(filepath):
                    print(f"Using cached file: {filepath}")
                    with open(filepath, 'rb') as f:
                        raw = f.read()
                else:
                    # Filter by category 316 (Events- All)
                    url = (f"{api_base}?start_date={w_start}&end_date={w_end}"
                           f"&categories=316&per_page=50&page={page}")
                    raw = get_page_content(url)
                    if raw:
                        os.makedirs("raw_html", exist_ok=True)
                        with open(filepath, 'wb') as f:
                            f.write(raw)
                        time.sleep(0.5)
                if not raw:
                    break
                shows = parser.parse(raw)
                print(f"Parsed {len(shows)} shows from minneapolisparks.org ({w_start} p{page})")
                all_shows.extend(shows)
                # Check if more pages exist
                try:
                    import json as _json
                    data = _json.loads(raw)
                    total = int(data.get('total', 0))
                    fetched_so_far = (page - 1) * 50 + len(shows)
                    if fetched_so_far >= total:
                        break
                except Exception:
                    break
                page += 1

    elif site_name == 'trylon_cinema':
        filepath = "raw_html/trylon_cinema.ics"
        html = None
        if os.path.exists(filepath):
            print(f"Using cached file: {filepath}")
            with open(filepath, 'rb') as f:
                html = f.read()
        else:
            url = "https://calendar.google.com/calendar/ical/htl8o9ddvffma2gqn5m0e5clis%40group.calendar.google.com/public/basic.ics"
            html = get_page_content(url)
            if html:
                os.makedirs("raw_html", exist_ok=True)
                with open(filepath, "wb") as f:
                    f.write(html)
                time.sleep(1)
        if html:
            shows = parser.parse(html)
            print(f"Parsed {len(shows)} shows from trylon.org (via Google Calendar ICS)")
            all_shows.extend(shows)

    elif site_name == 'parkway_theater':
        filepath = "raw_html/parkway_theater.json"
        html = None
        if os.path.exists(filepath):
            print(f"Using cached file: {filepath}")
            with open(filepath, 'rb') as f:
                html = f.read()
        else:
            url = "https://theparkwaytheater.com/all-events?format=json"
            html = get_page_content(url)
            if html:
                os.makedirs("raw_html", exist_ok=True)
                with open(filepath, "wb") as f:
                    f.write(html)
                time.sleep(1)
        if html:
            shows = parser.parse(html)
            print(f"Parsed {len(shows)} shows from theparkwaytheater.com (Squarespace API)")
            all_shows.extend(shows)

    elif site_name == 'fillmore_minneapolis':
        filepath = "raw_html/fillmore_minneapolis.html"
        html = None
        if os.path.exists(filepath):
            print(f"Using cached file: {filepath}")
            with open(filepath, 'rb') as f:
                html = f.read()
        else:
            url = "https://www.fillmoreminneapolis.com/shows"
            html = get_page_content(url)
            if html:
                os.makedirs("raw_html", exist_ok=True)
                with open(filepath, "wb") as f:
                    f.write(html)
                time.sleep(1)
        if html:
            shows = parser.parse(html)
            print(f"Parsed {len(shows)} shows from fillmoreminneapolis.com (JSON-LD)")
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
    # Set target timeframe: 120 days starting today
    start_date = datetime.date.today()
    end_date = start_date + datetime.timedelta(days=120)
    
    # List of sites to scrape
    sites_to_scrape = ['first_avenue', 'grand_casino_arena', 'acme_comedy_club', 'guthrie_theater', 'minneapolis', 'mn_united_fc', 'minnesota_twins', 'target_center', 'minnesota_orchestra', 'hennepin_arts', 'us_bank_stadium', 'northrop_auditorium', 'ordway_theater', 'visit_stpaul', 'dakota_jazz_club', 'berlin_jazz_club', 'crooners', 'visit_duluth', 'luminary_arts_center', 'utepils_brewery', 'pryes_brewing', 'mncba_workshops', 'coch_cooking_classes', 'dame_errant_clay', 'mpls_parks', 'trylon_cinema', 'parkway_theater', 'fillmore_minneapolis']
    
    for site in sites_to_scrape:
        scrape_site(site, start_date, end_date)

if __name__ == "__main__":
    main()
