"""
File: web_scraper.py
Team Name: AirAudit
Team Members:
- Menaka Ananda (AndrewID: mgowdaan)
- Chao Huang (AndrewID: chaoh)
- Rong Guo (AndrewID: rongguo)
- Tracy Yang (AndrewID: tracyy)

Description: 
This module performs web scraping to gather destination insights. It extracts 
top attractions from Wikivoyage (via MediaWiki API — avoids 403 blocks) and 
retrieves 14-day weather forecasts. Cost data uses Teleport API with realistic
city-specific fallbacks.

Imported by: app.py
"""
import re
import requests
from bs4 import BeautifulSoup

# Standard browser headers for HTML scraping
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# Wikivoyage API headers — must identify as a real client to avoid 403
WIKI_API_HEADERS = {
    "User-Agent": "AirAudit/1.0 (CMU student project; contact: chaoh@andrew.cmu.edu)",
    "Accept": "application/json",
}

AIRPORT_TO_CITY = {
    # 15 US cities
    "LAX": "Los Angeles",  "SAN": "San Diego",    "PIT": "Pittsburgh",
    "ORD": "Chicago",      "JFK": "New York",      "MIA": "Miami",
    "SEA": "Seattle",      "DEN": "Denver",        "ATL": "Atlanta",
    "BOS": "Boston",       "LAS": "Las Vegas",     "SFO": "San Francisco",
    "HOU": "Houston",      "PHX": "Phoenix",       "MSY": "New Orleans",
    # 10 international cities
    "NRT": "Tokyo",        "LHR": "London",        "CDG": "Paris",
    "SYD": "Sydney",       "BKK": "Bangkok",       "SIN": "Singapore",
    "PEK": "Beijing",      "SHA": "Shanghai",      "NKG": "Nanjing",
    "PUS": "Busan",
}

WEATHER_PAGE_MAP = {
    "Los Angeles":   ("usa",         "los-angeles"),
    "San Diego":     ("usa",         "san-diego"),
    "Pittsburgh":    ("usa",         "pittsburgh"),
    "Chicago":       ("usa",         "chicago"),
    "New York":      ("usa",         "new-york"),
    "Miami":         ("usa",         "miami"),
    "Seattle":       ("usa",         "seattle"),
    "Denver":        ("usa",         "denver"),
    "Atlanta":       ("usa",         "atlanta"),
    "Boston":        ("usa",         "boston"),
    "Las Vegas":     ("usa",         "las-vegas"),
    "San Francisco": ("usa",         "san-francisco"),
    "Houston":       ("usa",         "houston"),
    "Phoenix":       ("usa",         "phoenix"),
    "New Orleans":   ("usa",         "new-orleans"),
    "Tokyo":         ("japan",       "tokyo"),
    "London":        ("uk",          "london"),
    "Paris":         ("france",      "paris"),
    "Sydney":        ("australia",   "sydney"),
    "Bangkok":       ("thailand",    "bangkok"),
    "Singapore":     ("singapore",   "singapore"),
    "Beijing":       ("china",       "beijing"),
    "Shanghai":      ("china",       "shanghai"),
    "Nanjing":       ("china",       "nanjing"),
    "Busan":         ("south-korea", "busan"),
}

# Per-city realistic fallback costs (used if ALL live sources fail)
CITY_COST_FALLBACKS = {
    "Los Angeles":   {"daily_living": 85.0,  "nightly_hotel": 160.0},
    "San Diego":     {"daily_living": 80.0,  "nightly_hotel": 145.0},
    "Pittsburgh":    {"daily_living": 55.0,  "nightly_hotel": 110.0},
    "Chicago":       {"daily_living": 80.0,  "nightly_hotel": 150.0},
    "New York":      {"daily_living": 105.0, "nightly_hotel": 220.0},
    "Miami":         {"daily_living": 85.0,  "nightly_hotel": 170.0},
    "Seattle":       {"daily_living": 85.0,  "nightly_hotel": 160.0},
    "Denver":        {"daily_living": 70.0,  "nightly_hotel": 140.0},
    "Atlanta":       {"daily_living": 65.0,  "nightly_hotel": 130.0},
    "Boston":        {"daily_living": 90.0,  "nightly_hotel": 180.0},
    "Las Vegas":     {"daily_living": 75.0,  "nightly_hotel": 120.0},
    "San Francisco": {"daily_living": 100.0, "nightly_hotel": 210.0},
    "Houston":       {"daily_living": 65.0,  "nightly_hotel": 130.0},
    "Phoenix":       {"daily_living": 60.0,  "nightly_hotel": 120.0},
    "New Orleans":   {"daily_living": 65.0,  "nightly_hotel": 130.0},
    "Tokyo":         {"daily_living": 70.0,  "nightly_hotel": 130.0},
    "London":        {"daily_living": 100.0, "nightly_hotel": 190.0},
    "Paris":         {"daily_living": 95.0,  "nightly_hotel": 180.0},
    "Sydney":        {"daily_living": 90.0,  "nightly_hotel": 170.0},
    "Bangkok":       {"daily_living": 35.0,  "nightly_hotel": 65.0},
    "Singapore":     {"daily_living": 75.0,  "nightly_hotel": 145.0},
    "Beijing":       {"daily_living": 40.0,  "nightly_hotel": 80.0},
    "Shanghai":      {"daily_living": 50.0,  "nightly_hotel": 100.0},
    "Nanjing":       {"daily_living": 35.0,  "nightly_hotel": 70.0},
    "Busan":         {"daily_living": 45.0,  "nightly_hotel": 90.0},
    "_default":      {"daily_living": 70.0,  "nightly_hotel": 140.0},
}

# Curated static attraction lists — final fallback if all scraping fails
STATIC_ATTRACTIONS = {
    "Los Angeles":   ["Getty Center", "Griffith Observatory", "The Broad Museum",
                      "LACMA", "Venice Beach Boardwalk", "Hollywood Walk of Fame",
                      "Runyon Canyon Park", "La Brea Tar Pits", "Santa Monica Pier",
                      "Universal Studios Hollywood", "Dodger Stadium", "The Getty Villa"],
    "San Diego":     ["Balboa Park", "San Diego Zoo", "USS Midway Museum",
                      "Gaslamp Quarter", "Cabrillo National Monument", "Old Town San Diego",
                      "La Jolla Cove", "Coronado Island", "Seaport Village",
                      "Torrey Pines State Reserve"],
    "Pittsburgh":    ["Carnegie Museum of Natural History", "Phipps Conservatory",
                      "Point State Park", "The Andy Warhol Museum", "Carnegie Science Center",
                      "Duquesne Incline", "Fallingwater", "Strip District Market",
                      "Cathedral of Learning", "Pittsburgh Zoo"],
    "Chicago":       ["Millennium Park & Cloud Gate", "Art Institute of Chicago",
                      "Navy Pier", "Chicago Riverwalk", "Willis Tower Skydeck",
                      "Lincoln Park Zoo", "Museum of Science and Industry",
                      "Field Museum", "Wrigley Field", "Shedd Aquarium",
                      "Chicago Architecture Boat Tour", "Magnificent Mile"],
    "New York":      ["Central Park", "Metropolitan Museum of Art", "Times Square",
                      "Brooklyn Bridge", "The High Line", "One World Observatory",
                      "Museum of Modern Art", "Statue of Liberty", "Rockefeller Center",
                      "Whitney Museum", "The Vessel", "Grand Central Terminal"],
    "Miami":         ["South Beach", "Art Deco Historic District", "Wynwood Walls",
                      "Everglades National Park", "Vizcaya Museum & Gardens",
                      "Pérez Art Museum Miami", "Little Havana", "Bayside Marketplace",
                      "Miami Design District", "Zoo Miami"],
    "Seattle":       ["Pike Place Market", "Space Needle", "Chihuly Garden and Glass",
                      "Museum of Pop Culture", "Seattle Art Museum", "Kerry Park",
                      "Pioneer Square", "Olympic Sculpture Park", "Fremont Troll",
                      "Seattle Aquarium", "Discovery Park", "Capitol Hill"],
    "Denver":        ["Rocky Mountain National Park", "Red Rocks Amphitheatre",
                      "Denver Art Museum", "16th Street Mall", "Larimer Square",
                      "Denver Botanic Gardens", "Colorado State Capitol",
                      "Denver Zoo", "Union Station", "RiNo Art District"],
    "Atlanta":       ["Georgia Aquarium", "World of Coca-Cola", "Centennial Olympic Park",
                      "Martin Luther King Jr. National Historic Site",
                      "Atlanta Botanical Garden", "High Museum of Art",
                      "Stone Mountain Park", "Ponce City Market", "Little Five Points",
                      "CNN Studio Tours"],
    "Boston":        ["Freedom Trail", "Faneuil Hall Marketplace", "Boston Common",
                      "Isabella Stewart Gardner Museum", "Museum of Fine Arts",
                      "Harvard University Campus", "Boston Public Garden",
                      "New England Aquarium", "Fenway Park", "Beacon Hill"],
    "Las Vegas":     ["The Strip", "Bellagio Fountains", "High Roller Observation Wheel",
                      "Fremont Street Experience", "The Venetian & Grand Canal",
                      "Red Rock Canyon", "Hoover Dam Day Trip", "Mob Museum",
                      "Neon Museum", "AREA15"],
    "San Francisco": ["Golden Gate Bridge", "Alcatraz Island", "Fisherman's Wharf",
                      "Cable Cars", "Chinatown", "Golden Gate Park",
                      "Painted Ladies", "Ferry Building Marketplace",
                      "Muir Woods", "Exploratorium"],
    "Houston":       ["Space Center Houston", "Houston Museum of Natural Science",
                      "Museum of Fine Arts Houston", "Hermann Park",
                      "Houston Zoo", "Discovery Green", "Buffalo Bayou Park",
                      "Minute Maid Park", "Kemah Boardwalk", "The Galleria"],
    "Phoenix":       ["Camelback Mountain", "Desert Botanical Garden",
                      "Heard Museum", "Musical Instrument Museum",
                      "Taliesin West", "South Mountain Park",
                      "Sedona Day Trip", "Phoenix Art Museum",
                      "Chase Field", "Old Town Scottsdale"],
    "New Orleans":   ["French Quarter", "Bourbon Street", "Jackson Square",
                      "St. Louis Cathedral", "Garden District",
                      "National WWII Museum", "Frenchmen Street Jazz",
                      "New Orleans City Park", "Audubon Zoo",
                      "Steamboat Natchez River Cruise"],
    # International cities
    "Tokyo":         ["Senso-ji Temple", "Shibuya Crossing", "Shinjuku Gyoen",
                      "teamLab Planets", "Tsukiji Outer Market", "Meiji Shrine",
                      "Tokyo Skytree", "Akihabara", "Harajuku Takeshita Street",
                      "Odaiba", "Ueno Park", "Imperial Palace East Gardens"],
    "London":        ["British Museum", "Tower of London", "Tate Modern",
                      "Buckingham Palace", "The National Gallery", "Borough Market",
                      "St. Paul's Cathedral", "Hyde Park", "Covent Garden",
                      "Victoria and Albert Museum", "Tower Bridge", "Kew Gardens"],
    "Paris":         ["Eiffel Tower", "Louvre Museum", "Notre-Dame Cathedral",
                      "Musée d'Orsay", "Sainte-Chapelle", "Palace of Versailles",
                      "Centre Pompidou", "Montmartre & Sacré-Cœur", "Seine River Cruise",
                      "Marais District", "Luxembourg Gardens", "Père Lachaise Cemetery"],
    "Sydney":        ["Sydney Opera House", "Sydney Harbour Bridge Climb",
                      "Bondi Beach", "Royal Botanic Garden", "Taronga Zoo",
                      "Darling Harbour", "The Rocks Historic District",
                      "Blue Mountains Day Trip", "Manly Beach", "Sydney Tower Eye"],
    "Bangkok":       ["Grand Palace", "Wat Pho (Temple of the Reclining Buddha)",
                      "Wat Arun", "Chatuchak Weekend Market", "Jim Thompson House",
                      "Floating Markets", "Lumphini Park", "Khao San Road",
                      "Erawan Shrine", "Asiatique The Riverfront",
                      "Museum of Siam", "Chinatown (Yaowarat)"],
    "Singapore":     ["Gardens by the Bay", "Marina Bay Sands SkyPark",
                      "Singapore Zoo & Night Safari", "Sentosa Island",
                      "Hawker Centres (Maxwell, Lau Pa Sat)", "Chinatown Heritage Centre",
                      "Little India", "Universal Studios Singapore",
                      "ArtScience Museum", "Orchard Road", "Jewel Changi Airport"],
    "Beijing":       ["Forbidden City", "Great Wall of China", "Temple of Heaven",
                      "Summer Palace", "Tiananmen Square", "798 Art District",
                      "Beihai Park", "Lama Temple", "Hutong Alleyways", "Ming Tombs"],
    "Shanghai":      ["The Bund", "Yu Garden", "Shanghai Tower Observatory",
                      "French Concession", "Xintiandi", "Zhujiajiao Water Town",
                      "Shanghai Museum", "People's Square", "M50 Creative Park", "Nanjing Road"],
    "Nanjing":       ["Sun Yat-sen Mausoleum", "Ming Xiaoling Mausoleum", "Confucius Temple",
                      "Nanjing City Wall", "Purple Mountain", "Xuanwu Lake Park",
                      "Nanjing Massacre Memorial", "Presidential Palace", "1912 Block"],
    "Busan":         ["Haeundae Beach", "Gamcheon Culture Village", "Jagalchi Fish Market",
                      "Beomeosa Temple", "Gwangalli Beach", "BIFF Square",
                      "Taejongdae Resort Park", "Haedong Yonggungsa Temple",
                      "Shinsegae Centum City", "Songdo Beach"],
}

# Curated static cuisine lists — final fallback
STATIC_CUISINE = {
    "Los Angeles":   ["Korean BBQ", "Street Tacos", "Fresh Sushi", "In-N-Out Burger",
                      "Vietnamese Pho", "California Farm-to-Table", "Ramen"],
    "San Diego":     ["Fish Tacos", "California Burritos", "Ceviche",
                      "Clam Chowder Bread Bowl", "Craft Beer", "Açaí Bowls"],
    "Pittsburgh":    ["Pierogies", "Primanti Brothers Sandwich", "Kielbasa",
                      "Haluski", "Chipped Ham", "Pittsburgh Salad"],
    "Chicago":       ["Deep Dish Pizza", "Chicago-Style Hot Dog", "Italian Beef Sandwich",
                      "Garrett Popcorn", "Jibarito", "Chicken Vesuvio", "Malört"],
    "New York":      ["New York-Style Pizza", "Bagels with Lox", "Cheesecake",
                      "Pastrami on Rye", "Hot Dogs", "Halal Cart Food", "Dim Sum"],
    "Miami":         ["Cuban Sandwich", "Stone Crab Claws", "Ceviche",
                      "Plantains & Ropa Vieja", "Key Lime Pie", "Empanadas",
                      "Café Cubano"],
    "Seattle":       ["Dungeness Crab", "Smoked Salmon", "Clam Chowder",
                      "Pike Place Chowder", "Teriyaki", "Craft Coffee",
                      "Rainier Cherries"],
    "Denver":        ["Rocky Mountain Oysters", "Bison Burger", "Green Chile",
                      "Craft Beer", "Lamb Chops", "Palisade Peaches",
                      "Colorado Lamb"],
    "Atlanta":       ["Fried Chicken", "Peach Cobbler", "Shrimp & Grits",
                      "Biscuits & Gravy", "BBQ Ribs", "Sweet Tea",
                      "Pecan Pie"],
    "Boston":        ["New England Clam Chowder", "Lobster Roll", "Boston Cream Pie",
                      "Baked Beans", "Cannoli (North End)", "Oysters",
                      "Sam Adams Beer"],
    "Las Vegas":     ["All-You-Can-Eat Buffets", "Celebrity Chef Restaurants",
                      "In-N-Out Burger", "Shrimp Cocktail", "Steak & Lobster",
                      "Late-Night Eats"],
    "San Francisco": ["Sourdough Bread Bowl Clam Chowder", "Dungeness Crab",
                      "Mission-Style Burrito", "Dim Sum", "Cioppino",
                      "Ghirardelli Chocolate", "Fresh Oysters"],
    "Houston":       ["BBQ Brisket", "Tex-Mex Fajitas", "Gulf Shrimp",
                      "Crawfish Étouffée", "Chicken Fried Steak",
                      "Vietnamese Pho (Midtown)", "Kolaches"],
    "Phoenix":       ["Sonoran Hot Dog", "Green Chile Cheeseburger", "Prickly Pear Margarita",
                      "Navajo Tacos", "Chimichanga", "Mesquite-Grilled Steak",
                      "Date Shakes"],
    "New Orleans":   ["Beignets & Café au Lait", "Gumbo", "Jambalaya",
                      "Po'boy Sandwich", "Crawfish Étouffée", "Red Beans & Rice",
                      "Bananas Foster", "Charbroiled Oysters"],
    # International cities
    "Tokyo":         ["Ramen", "Sushi & Sashimi", "Tempura", "Tonkatsu",
                      "Yakitori", "Takoyaki", "Matcha Desserts", "Conveyor Belt Sushi"],
    "London":        ["Fish & Chips", "Full English Breakfast", "Chicken Tikka Masala",
                      "Afternoon Tea", "Pies & Mash", "Salt Beef Bagels",
                      "Sticky Toffee Pudding", "Scotch Eggs"],
    "Paris":         ["Croissants & Pain au Chocolat", "French Onion Soup",
                      "Steak Frites", "Crêpes", "Macarons", "Escargot",
                      "Cheese & Charcuterie", "Crème Brûlée"],
    "Sydney":        ["Flat White Coffee", "Meat Pie", "Tim Tams",
                      "Barramundi Fish & Chips", "Vegemite on Toast",
                      "Lamingtons", "Pavlova", "Moreton Bay Bugs"],
    "Bangkok":       ["Pad Thai", "Tom Yum Goong", "Green Curry", "Mango Sticky Rice",
                      "Som Tum (Green Papaya Salad)", "Khao Man Gai",
                      "Boat Noodles", "Satay Skewers"],
    "Singapore":     ["Hainanese Chicken Rice", "Laksa", "Chili Crab",
                      "Char Kway Teow", "Nasi Lemak", "Satay",
                      "Kaya Toast & Soft-Boiled Eggs", "Durian"],
    "Beijing":       ["Peking Duck", "Jianbing (Savory Crepe)", "Zhajiangmian Noodles",
                      "Baozi (Steamed Buns)", "Hot Pot", "Lamb Skewers"],
    "Shanghai":      ["Xiaolongbao (Soup Dumplings)", "Shengjianbao (Pan-Fried Buns)",
                      "Hairy Crab", "Red-Braised Pork", "Scallion Pancakes", "Wonton Soup"],
    "Nanjing":       ["Salted Duck", "Duck Blood Vermicelli Soup", "Tangbao",
                      "Steamed Buns", "Sweet Osmanthus Cake"],
    "Busan":         ["Milmyeon Noodles", "Dwaeji Gukbap (Pork Rice Soup)",
                      "Raw Fish (Hoe)", "Ssiat Hotteok (Sweet Pancake)", "Ganjang Gejang"],
}


def get_html(url, params=None, headers=None):
    try:
        h = headers or HEADERS
        response = requests.get(url, headers=h, params=params, timeout=15)
        response.raise_for_status()
        return response.text
    except requests.RequestException:
        return None


def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()


def airport_to_city(iata_code):
    code = iata_code.upper().strip()
    return AIRPORT_TO_CITY.get(code, code)


def likely_place_name(text):
    text = clean_text(text)
    if not text:
        return None
    text = re.sub(r"\([^)]{10,}\)", "", text)
    if "." in text:
        first = text.split(".", 1)[0].strip()
        if 3 < len(first) < 100:
            text = first
    if "," in text:
        first = text.split(",", 1)[0].strip()
        if 3 < len(first) < 80:
            text = first
    text = clean_text(text)
    return text if 3 <= len(text) <= 100 else None


# ---------------------------------------------------------------------------
# ATTRACTIONS — Wikivoyage MediaWiki API (bypasses 403 that HTML scraping gets)
# ---------------------------------------------------------------------------

def scrape_wikivoyage_attractions(city):
    """
    Uses the Wikivoyage MediaWiki wikitext API to extract attraction names.
    Much more reliable than HTML scraping which gets 403 blocked.
    Falls back to curated static list if API unreachable.
    """
    try:
        # Step 1: find the section index for "See"
        r = requests.get(
            "https://en.wikivoyage.org/w/api.php",
            params={"action": "parse", "page": city, "prop": "sections", "format": "json"},
            headers=WIKI_API_HEADERS,
            timeout=15,
        )
        if r.status_code != 200:
            return STATIC_ATTRACTIONS.get(city, [])

        sections = r.json().get("parse", {}).get("sections", [])
        see_idx = None
        for s in sections:
            if s.get("line", "").strip().lower() == "see":
                see_idx = s.get("index")
                break

        if see_idx is None:
            return STATIC_ATTRACTIONS.get(city, [])

        # Step 2: fetch wikitext for that section
        r2 = requests.get(
            "https://en.wikivoyage.org/w/api.php",
            params={
                "action": "parse", "page": city, "prop": "wikitext",
                "section": see_idx, "format": "json"
            },
            headers=WIKI_API_HEADERS,
            timeout=15,
        )
        if r2.status_code != 200:
            return STATIC_ATTRACTIONS.get(city, [])

        wikitext = r2.json().get("parse", {}).get("wikitext", {}).get("*", "")

        results = []
        seen = set()
        junk = {"see", "do", "eat", "buy", "sleep", "get", "note", "tip", "go", "in", "out"}

        # Extract from {{listing|name=...}} / {{see|name=...}} templates
        for match in re.finditer(
            r'\{\{(?:listing|see|do)[^}]*\|[^}]*name\s*=\s*([^|}\n]+)',
            wikitext, re.IGNORECASE
        ):
            name = clean_text(match.group(1).strip())
            if name and 3 <= len(name) <= 80 and name.lower() not in seen:
                seen.add(name.lower())
                results.append(name)

        # Extract '''Bold text''' — often attraction names in prose
        for match in re.finditer(r"'''([^']{3,60})'''", wikitext):
            name = clean_text(match.group(1))
            if name and name.lower() not in seen and name.lower() not in junk:
                seen.add(name.lower())
                results.append(name)

        if results:
            return results[:14]

    except Exception:
        pass

    return STATIC_ATTRACTIONS.get(city, [])


# ---------------------------------------------------------------------------
# CUISINE — Wikivoyage MediaWiki API
# ---------------------------------------------------------------------------

def scrape_wikivoyage_cuisine(city):
    try:
        r = requests.get(
            "https://en.wikivoyage.org/w/api.php",
            params={"action": "parse", "page": city, "prop": "sections", "format": "json"},
            headers=WIKI_API_HEADERS,
            timeout=15,
        )
        if r.status_code != 200:
            return STATIC_CUISINE.get(city, [])

        sections = r.json().get("parse", {}).get("sections", [])
        eat_idx = None
        for s in sections:
            if s.get("line", "").strip().lower() == "eat":
                eat_idx = s.get("index")
                break

        if eat_idx is None:
            return STATIC_CUISINE.get(city, [])

        r2 = requests.get(
            "https://en.wikivoyage.org/w/api.php",
            params={
                "action": "parse", "page": city, "prop": "wikitext",
                "section": eat_idx, "format": "json"
            },
            headers=WIKI_API_HEADERS,
            timeout=15,
        )
        if r2.status_code != 200:
            return STATIC_CUISINE.get(city, [])

        wikitext = r2.json().get("parse", {}).get("wikitext", {}).get("*", "")

        results = []
        seen = set()
        junk = {"budget", "mid-range", "splurge", "eat", "note", "tip"}

        # Bold dish names '''name'''
        for match in re.finditer(r"'''([^']{2,50})'''", wikitext):
            name = clean_text(match.group(1))
            if name and name.lower() not in seen and name.lower() not in junk:
                seen.add(name.lower())
                results.append(name)

        # Italic dish names ''name''
        for match in re.finditer(r"(?<!')''(?!')([^']{3,50})(?<!')''(?!')", wikitext):
            name = clean_text(match.group(1))
            if name and name.lower() not in seen and name.lower() not in junk:
                seen.add(name.lower())
                results.append(name)

        if results:
            return results[:10]

    except Exception:
        pass

    return STATIC_CUISINE.get(city, [])


# ---------------------------------------------------------------------------
# COST OF LIVING — Numbeo HTML scraping, falls back to per-city static estimates
# ---------------------------------------------------------------------------

def scrape_numbeo_cost_of_living(city):
    """
    Priority order:
    1. Numbeo HTML scraping
    2. Per-city static estimates
    Returns dict: {daily_living, nightly_hotel, source}
    """
    fallback = CITY_COST_FALLBACKS.get(city, CITY_COST_FALLBACKS["_default"]).copy()
    fallback["source"] = "estimated"

    # --- 1. Try Numbeo HTML ---
    city_slug = city.replace(" ", "-")
    html = get_html(f"https://www.numbeo.com/cost-of-living/in/{city_slug}")
    if html:
        soup = BeautifulSoup(html, "html.parser")
        result = fallback.copy()
        scraped_any = False

        box = soup.find("div", class_="seeding-call table_color summary")
        if box:
            m = re.search(r"single person estimated monthly costs are ([\d,.]+)", box.get_text())
            if m:
                try:
                    result["daily_living"] = round(float(m.group(1).replace(",", "")) / 30, 1)
                    scraped_any = True
                except ValueError:
                    pass

        for row in soup.find_all("tr"):
            if "Apartment (1 bedroom) in City Centre" in row.get_text():
                tds = row.find_all("td")
                if tds:
                    pt = re.sub(r'[^\d.]', '', tds[-1].get_text())
                    if pt:
                        try:
                            result["nightly_hotel"] = round((float(pt) / 30) * 1.5, 1)
                            scraped_any = True
                        except ValueError:
                            pass
                break

        if scraped_any:
            result["source"] = "scraped"
            return result

    # --- 2. Static fallback ---
    return fallback


# ---------------------------------------------------------------------------
# WEATHER — timeanddate.com HTML scraping (working well, unchanged)
# ---------------------------------------------------------------------------

def scrape_timeanddate_weather(city):
    if city not in WEATHER_PAGE_MAP:
        return []
    country_slug, city_slug = WEATHER_PAGE_MAP[city]
    url = f"https://www.timeanddate.com/weather/{country_slug}/{city_slug}/ext"
    html = get_html(url)
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    weather_table = soup.find("table", id="wt-ext")
    if not weather_table:
        return []
    forecast = []
    tbody = weather_table.find("tbody")
    for row in tbody.find_all("tr"):
        th = row.find("th")
        cells = row.find_all("td")
        if not th or len(cells) < 12:
            continue
        forecast.append({
            "day":         clean_text(th.get_text()),
            "temperature": clean_text(cells[2].get_text()),
            "weather":     clean_text(cells[3].get_text()),
            "humidity":    clean_text(cells[6].get_text()),
            "chance":      clean_text(cells[7].get_text()),
        })
    return forecast


def scrape_destination_info(arrival_iata):
    city = airport_to_city(arrival_iata)
    return {
        "city":            city,
        "top_attractions": scrape_wikivoyage_attractions(city),
        "cost_of_living":  scrape_numbeo_cost_of_living(city),
        "weather":         scrape_timeanddate_weather(city),
        "cuisine":         scrape_wikivoyage_cuisine(city),
    }