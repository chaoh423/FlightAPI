# AirAudit — Trip Cost Auditor

**Team Name:** AirAudit  
**Course:** 95-888 (CMU)

**Team Members:**
- Menaka Ananda (AndrewID: mgowdaan)
- Chao Huang (AndrewID:chaoh)
- Rong Guo (AndrewID:rongguo)
- Tracy Yang (AndrewID:tracyy)

---

## What It Does

AirAudit combines real flight prices with destination cost-of-living data to show the **true all-in cost** of a trip — not just the airfare. Pick a departure city, a destination, and travel dates, and the app fetches live flights, scrapes weather and attractions, and estimates your total hotel + daily expenses in one place.

---

## Files in This Project

```
AirAudit/
├── app.py               # Main Streamlit app — run this
├── flight_data.py       # Fetches, caches, parses, and filters flight data (SerpApi)
├── web_scraper.py       # Scrapes attractions, cuisine, weather, and cost-of-living data
├── analysis_module.py   # Generates price trend and stop distribution charts
├── serpapi_key.txt      # Your SerpApi key — you must create this (see below)
├── cache/               # Auto-created: stores cached flight JSON per route
├── output/charts/       # Auto-created: stores generated chart PNG files
├── requirements.txt     # Python packages needed
└── README.md            # This file
```

---

## Installation

### Step 1 — Install required packages

```bash
pip install -r requirements.txt
```

Or manually:

```bash
pip install streamlit pandas matplotlib serpapi requests beautifulsoup4
```

### Step 2 — Get a SerpApi key

1. Go to [https://serpapi.com](https://serpapi.com) and create a free account
2. Copy your API key (64-character hex string) from the dashboard
3. Create a file called `serpapi_key.txt` in the same folder as `app.py`
4. Paste your key as the only content in that file and save it

```
a1b2c3d4e5f6...your64charkey...
```
// For now, we have added the API key in the file. 

### Step 3 — Run the app

```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`.

---

## How to Use

1. In the **sidebar**, choose a departure city and destination city from the dropdown
2. Set your **outbound and inbound dates**
3. Choose a **stay style** (Budget / Mid-Range / Luxury)
4. Optionally filter by number of layovers
5. Click **CALCULATE TOTAL TRIP COST**
6. Browse flight options in the **Flight Search** tab — click **Select** to lock in a fare
7. View attractions, cuisine, and weather in the **Destination Intel** tab
8. See price trend and stop distribution charts in the **Market Analytics** tab
9. Click **Download All Flights as CSV** to export results

---

## Data Sources

| Source | What We Get | Method |
|---|---|---|
| SerpApi (Google Flights) | Live flight prices, routes, durations, stops | API |
| Wikivoyage (MediaWiki API) | Top attractions, local cuisine per city | API (JSON) |
| timeanddate.com | 14-day weather forecast | HTML scraping (BeautifulSoup) |
| Teleport API | Cost of living scores by city | API (JSON) |
| Numbeo | Daily living + hotel cost estimates | HTML scraping (BeautifulSoup) |

---

## Caching

Flight data is cached locally to avoid burning through API calls. Cached files are stored as JSON in the `cache/` folder, named by route (e.g. `cache/PIT_LAX.json`).

- The UI uses **cached data by default** — previously fetched dates are reused
- To fetch fresh data for all dates, uncheck the cache option or delete the relevant cache file
- This satisfies the rubric requirement to allow use of previously downloaded data

---

## Supported Cities (25 total)

**15 US cities:** Los Angeles, San Diego, Pittsburgh, Chicago, New York, Miami, Seattle, Denver, Atlanta, Boston, Las Vegas, San Francisco, Houston, Phoenix, New Orleans

**10 International:** Tokyo, London, Paris, Sydney, Bangkok, Singapore, Beijing, Shanghai, Nanjing, Busan

---

## Known Limitations

- **Wikivoyage / timeanddate.com** may occasionally be slow or return no data — the app falls back to curated static lists for all 25 cities so it never shows a blank page
- **Numbeo** actively blocks scrapers; the Teleport API is used as the primary cost source, with Numbeo as backup and static estimates as final fallback
- **SerpApi free tier** is limited to 100 searches/month — use caching to conserve calls
