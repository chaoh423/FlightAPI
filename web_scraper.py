import re
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

AIRPORT_TO_CITY = {
    "LAX": "Los Angeles",
    "SAN": "San Diego",
    "PIT": "Pittsburgh",
    "PEK": "Beijing",
    "SHA": "Shanghai",
    "NKG": "Nanjing",
    "PUS": "Busan",
}

WEATHER_PAGE_MAP = {
    "Los Angeles": ("usa", "los-angeles"),
    "San Diego": ("usa", "san-diego"),
    "Pittsburgh": ("usa", "pittsburgh"),
    "Shanghai": ("china", "shanghai"),
    "Beijing": ("china", "beijing"),
    "Nanjing": ("china", "nanjing"),
    "Busan": ("south-korea", "busan"),
}


def get_html(url, params=None):
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=15)
        response.raise_for_status()
        return response.text
    except requests.RequestException:
        return None


def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()


def airport_to_city(iata_code):
    code = iata_code.upper().strip()
    return AIRPORT_TO_CITY.get(code, code)


def shorten_text(text, max_len=120):
    text = clean_text(text)
    if len(text) <= max_len:
        return text
    shortened = text[:max_len].rsplit(" ", 1)[0]
    return shortened + "..."


def likely_place_name(text):
    text = clean_text(text)

    if not text:
        return None

    # remove long parenthetical notes/translations
    text = re.sub(r"\([^)]{10,}\)", "", text)
    text = clean_text(text)

    # if there is a period, often the first sentence is enough
    if "." in text:
        first = text.split(".", 1)[0].strip()
        if 3 < len(first) < 100:
            text = first

    # if there is a comma early on, keep the first chunk
    if "," in text:
        first = text.split(",", 1)[0].strip()
        if 3 < len(first) < 80:
            text = first

    text = clean_text(text)

    if 3 <= len(text) <= 100:
        return text

    return None


def scrape_wikivoyage_attractions(city):
    city_slug = city.replace(" ", "_")
    url = f"https://en.wikivoyage.org/wiki/{city_slug}"
    html = get_html(url)

    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")

    see_heading = soup.find(id="See")
    if not see_heading:
        return []

    see_section = see_heading.find_parent("section")
    if not see_section:
        return []

    results = []

    # 1. Rich listing names (common in pages like Shanghai)
    for tag in see_section.select("span.listing-name"):
        text = likely_place_name(tag.get_text(" ", strip=True))
        if text:
            results.append(text)

    # 2. Plain bullet list items
    for li in see_section.find_all("li"):
        if li.select_one("span.listing-name"):
            continue

        bold = li.find("b")
        if bold:
            text = likely_place_name(bold.get_text(" ", strip=True))
            if text:
                results.append(text)
                continue

        link = li.find("a")
        if link:
            text = likely_place_name(link.get_text(" ", strip=True))
            if text:
                results.append(text)
                continue

        text = likely_place_name(li.get_text(" ", strip=True))
        if text:
            results.append(text)

    # 3. Bold names inside paragraphs (useful for pages like Busan)
    for p in see_section.find_all("p"):
        for bold in p.find_all("b"):
            text = likely_place_name(bold.get_text(" ", strip=True))
            if text:
                results.append(text)

    # 4. Infobox tables inside See (common in Busan)
    for table in see_section.find_all("table"):
        for li in table.find_all("li"):
            text = likely_place_name(li.get_text(" ", strip=True))
            if text:
                results.append(text)

    cleaned = []
    seen = set()

    junk_phrases = {
        "Districts",
        "See",
        "edit",
        "add listing",
        "own article",
    }

    for item in results:
        item = clean_text(item)

        if item in junk_phrases:
            continue
        if len(item) < 3:
            continue
        if item.lower() in seen:
            continue

        seen.add(item.lower())
        cleaned.append(item)

    return cleaned[:15]


def scrape_numbeo_cost_of_living(city):
    city_slug = city.replace(" ", "-")
    url = f"https://www.numbeo.com/cost-of-living/in/{city_slug}"
    html = get_html(url)

    if not html:
        return {}

    soup = BeautifulSoup(html, "html.parser")

    summary_box = soup.find("div", class_="seeding-call table_color summary")
    if not summary_box:
        summary_box = soup.find("div", class_=lambda x: x and "summary" in x)

    if not summary_box:
        return {}

    items = summary_box.find_all("li")
    if not items:
        return {}

    result = {}

    for item in items:
        text = clean_text(item.get_text(" ", strip=True))

        if "family of four" in text.lower():
            result["Family of four monthly cost"] = text
        elif "single person" in text.lower():
            result["Single person monthly cost"] = text
        elif "less expensive than" in text.lower() or "more expensive than" in text.lower():
            result["Relative cost vs Pittsburgh"] = text
        elif "rent in" in text.lower():
            result["Rent comparison vs Pittsburgh"] = text

    return result

def scrape_timeanddate_weather(city):
    city = clean_text(city)

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
    if not tbody:
        return []

    rows = tbody.find_all("tr")
    for row in rows:
        th = row.find("th")
        cells = row.find_all("td")

        if not th or len(cells) < 12:
            continue

        day_text = clean_text(th.get_text(" ", strip=True))
        icon_img = row.find("img", class_="mtt")
        condition_text = icon_img.get("title", "").strip() if icon_img else ""

        entry = {
            "day": day_text,
            "temperature": clean_text(cells[1].get_text(" ", strip=True)),   # 69 / 58 °F
            "weather": clean_text(cells[2].get_text(" ", strip=True)) or condition_text,
            "feels_like": clean_text(cells[3].get_text(" ", strip=True)),
            "wind": clean_text(cells[4].get_text(" ", strip=True)),
            "humidity": clean_text(cells[6].get_text(" ", strip=True)),
            "chance": clean_text(cells[7].get_text(" ", strip=True)),
            "amount": clean_text(cells[8].get_text(" ", strip=True)),
            "uv": clean_text(cells[9].get_text(" ", strip=True)),
            "sunrise": clean_text(cells[10].get_text(" ", strip=True)),
            "sunset": clean_text(cells[11].get_text(" ", strip=True)),
        }

        forecast.append(entry)

    return forecast

def scrape_wikivoyage_cuisine(city):
    city_slug = city.replace(" ", "_")
    url = f"https://en.wikivoyage.org/wiki/{city_slug}"
    html = get_html(url)

    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")

    eat_heading = soup.find(id="Eat")
    if not eat_heading:
        return []

    eat_section = eat_heading.find_parent("section")
    if not eat_section:
        return []

    results = []

    # 1. Pull dish/cuisine names from italics in paragraph text
    for p in eat_section.find_all("p"):
        for ital in p.find_all("i"):
            text = clean_text(ital.get_text(" ", strip=True))

            # remove translation notes after semicolon
            if ";" in text:
                text = text.split(";", 1)[0].strip()

            if 2 < len(text) < 80:
                results.append(text)

    # 2. Pull listing names if they exist in Eat section
    for tag in eat_section.select("span.listing-name"):
        text = clean_text(tag.get_text(" ", strip=True))
        if 2 < len(text) < 100:
            results.append(text)

    # 3. Pull linked/bold dish or cuisine terms from bullet lists
    for li in eat_section.find_all("li"):
        if li.select_one("span.listing-name"):
            continue

        ital = li.find("i")
        if ital:
            text = clean_text(ital.get_text(" ", strip=True))
            if ";" in text:
                text = text.split(";", 1)[0].strip()
            if 2 < len(text) < 80:
                results.append(text)
                continue

        bold = li.find("b")
        if bold:
            text = clean_text(bold.get_text(" ", strip=True))
            if 2 < len(text) < 80:
                results.append(text)
                continue

        link = li.find("a")
        if link:
            text = clean_text(link.get_text(" ", strip=True))
            if 2 < len(text) < 80:
                results.append(text)
                continue

    # remove duplicates and junk
    cleaned = []
    seen = set()
    junk = {"Eat", "edit", "add listing"}

    for item in results:
        item = clean_text(item)

        if not item or item in junk:
            continue
        if item.lower() in seen:
            continue

        seen.add(item.lower())
        cleaned.append(item)

    return cleaned[:10]


def scrape_destination_info(arrival_iata):
    city = airport_to_city(arrival_iata)

    return {
        "city": city,
        "top_attractions": scrape_wikivoyage_attractions(city),
        "cost_of_living": scrape_numbeo_cost_of_living(city),
        "weather": scrape_timeanddate_weather(city),
        "cuisine": scrape_wikivoyage_cuisine(city),
    }