# Socialite 📅

Socialite is a Twin Cities and Duluth event aggregator of upcoming shows, concerts, classes, and sports matches from multiple local venues into a unified interactive feed.

---

## 🚀 Getting Started

### 1. Run the Scrapers & Aggregator
To crawl all configured venues and refresh the consolidated database:

```bash
# Run the scraper (pulls events for the next 120 days dynamically)
python scrape_shows.py

# Aggregate all individual venue outputs into a unified events.json
python aggregate_events.py
```

### 2. Launch the Web Application
Since the front-end is built with vanilla HTML, modern HSL CSS variables, and native ES6 Javascript, you can run it using any simple local HTTP server:

```bash
# Serve the directory locally
python -m http.server 8000
```
Open `http://localhost:8000` in your web browser to interact with the application.

---

## 🎨 Front-end Features

- **Dynamic Navigation Toggles**: Swap between a grid calendar and a chronological list feed.
- **Advanced Filtering**: Filter events instantly by date range, textual search queries, and specific source venues.
- **Aesthetic Premium Styling**: Crafted with rich colors, glassmorphism, responsive grids, custom typography (Google Fonts - Outfit), and subtle micro-animations.

---

## 🛠️ Application Structure

### Scraper System
- **[scrape_shows.py](file:///C:/Users/oconn/Documents/Code/Socialite/scrape_shows.py)**: The main runner for site scraping. Dynamically calculates month windows relative to the run date, executes requests, caches responses under `raw_html/` to minimize remote load, and outputs site-specific JSON lists.
- **[aggregate_events.py](file:///C:/Users/oconn/Documents/Code/Socialite/aggregate_events.py)**: Traverses individual venue JSON lists and merges them into `events.json` with de-duplication.

### Parser Architecture
All parsers inherit from `BaseParser` in `parsers/base.py` and are registered in `parsers/__init__.py`. They fall into three primary categories:

1. **WordPress Tribe REST API Parsers**:
   - *Venues*: Visit Duluth, Luminary Arts Center, Utepils Brewery, Minneapolis Parks & Rec.
   - *Design*: Fetch clean JSON responses from WordPress Tribe Calendar REST endpoints, parsing paginated collections.
2. **Squarespace Layout Parsers**:
   - *Venues*: Pryes Brewing (Event Lists), MNCBA Workshops (Summary Blocks), Dame Errant Clay (Event Lists).
   - *Design*: Parse Squarespace-specific HTML layouts using BeautifulSoup.
3. **Custom HTML Layout Parsers**:
   - *Venues*: First Avenue, Guthrie Theater, Dakota Jazz Club, Crooners, Hennepin Arts, etc.
   - *Design*: Custom tag selectors tailored to the specific raw layouts of those websites.

---

## 📍 Configured Sources

| Key Name | Venue Title | Color Token | Color Hint |
| :--- | :--- | :--- | :--- |
| `first_avenue` | First Avenue | `#e11d48` | Rose Red |
| `grand_casino_arena` | Grand Casino Arena | `#84cc16` | Lime Green |
| `acme_comedy_club` | Acme Comedy Club | `#3b82f6` | Royal Blue |
| `guthrie_theater` | Guthrie Theater | `#ea580c` | Deep Orange |
| `minneapolis` | Minneapolis.org | `#8b5cf6` | Violet |
| `mn_united_fc` | MN United FC | `#06b6d4` | Cyan |
| `minnesota_twins` | Minnesota Twins | `#ef4444` | Red |
| `target_center` | Target Center | `#f43f5e` | Rose |
| `minnesota_orchestra` | Minnesota Orchestra | `#10b981` | Emerald |
| `hennepin_arts` | Hennepin Arts | `#f59e0b` | Yellow/Amber |
| `us_bank_stadium` | U.S. Bank Stadium | `#eab308` | Gold |
| `northrop_auditorium` | Northrop Auditorium | `#991b1b` | Crimson |
| `ordway_theater` | Ordway Theater | `#0d9488` | Teal |
| `visit_stpaul` | Visit Saint Paul | `#2563eb` | Blue |
| `dakota_jazz_club` | Dakota Jazz Club | `#d97706` | Amber |
| `berlin_jazz_club` | Berlin Jazz Club | `#7c3aed` | Purple |
| `crooners` | Crooners Supper Club | `#be185d` | Pink |
| `visit_duluth` | Visit Duluth | `#0891b2` | Cyan/Lake Teal |
| `luminary_arts_center` | Luminary Arts Center | `#f97316` | Bright Orange |
| `utepils_brewery` | Utepils Brewery | `#16a34a` | Forest Green |
| `pryes_brewing` | Pryes Brewing | `#b45309` | Copper/Bronze |
| `mncba_workshops` | MNCBA Workshops | `#dc2626` | MCBA Crimson |
| `coch_cooking_classes` | CoCH Cooking Classes | `#9a3412` | Terracotta |
| `dame_errant_clay` | Dame Errant Clay | `#a21caf` | Fuchsia Clay |
| `mpls_parks` | MPLS Parks & Rec | `#059669` | Emerald Green |
