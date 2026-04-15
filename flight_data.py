"""
File: flight_data.py
Team Name: AirAudit
Team Members:
- Menaka Ananda (AndrewID: [ID 1])
- Chao Huang (AndrewID: chaoh)
- Rong Guo (AndrewID: [ID 3])
- Tracy Yang (AndrewID: [ID 4])


Description: 
This backend module handles the data pipeline for our Flight Search application. 
It retrieves flight data from the SerpApi (Google Flights) endpoint, implements 
a local caching system to minimize API calls, parses the complex nested JSON responses 
into structured Pandas DataFrames, and applies custom filters based on user preferences.

Imported by: app.py
"""

import json
import os
from datetime import datetime, timedelta

import pandas as pd
import serpapi

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
KEY_FILE = os.path.join(SCRIPT_DIR, "serpapi_key.txt")
CACHE_DIR = os.path.join(SCRIPT_DIR, "cache")

API_KEY = ""
if os.path.isfile(KEY_FILE):
    with open(KEY_FILE, "r") as f:
        API_KEY = f.read().strip()


# cache
# cache is one json per route, like cache/PIT_LAX.json

def load_cache(dep, arr):
    path = os.path.join(CACHE_DIR, f"{dep}_{arr}.json")
    # if the file does not exist, return an empty dictionary
    if not os.path.isfile(path):
        return {}
    # if the file exists, load the data from the file
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_cache(dep, arr, by_date):
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, f"{dep}_{arr}.json")
    with open(path, "w", encoding="utf-8") as f:
        # dump the data to the file
        json.dump(by_date, f, indent=2)


# fetch one-day flight data from api

def fetch_one_day(dep, arr, date):
    if not API_KEY:
        raise ValueError("No API key found! Put your key in serpapi_key.txt.")
    # try to fetch the data from the api
    try:
        client = serpapi.Client(api_key=API_KEY)
        results = client.search({
            "engine": "google_flights",
            "departure_id": dep,
            "arrival_id": arr,
            "outbound_date": date,
            "type": "2",
            "currency": "USD",
            "hl": "en",
            "sort_by": "2",
        })
        # print the results to see what we get
        # print(json.dumps(dict(results), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"API error for {date}: {e}")
        return []

    flights = []
    # google flights return two best_flights and other_flights sections
    for section in ["best_flights", "other_flights"]:
        if section in results:
            for flight in results[section]:
                flight["_date"] = date
                flights.append(flight)
    return flights


def fetch_date_range(dep, arr, start_date, end_date, use_cache=False):
    # build list of dates we want
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    if start > end:
        return []

    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)

    # load what we already have saved
    cached = load_cache(dep, arr)

    # if we are using cache, only fetch days we dont have yet
    if use_cache:
        # only fetch days we dont have yet
        missing = [d for d in dates if d not in cached]
        if missing:
            # fetch the missing days
            for d in missing:
                cached[d] = fetch_one_day(dep, arr, d)
            save_cache(dep, arr, cached)
    else:
        # fetch everything fresh, but keep other dates we had before
        for d in dates:
            cached[d] = fetch_one_day(dep, arr, d)
        save_cache(dep, arr, cached)

    # collect flights for the dates we asked for
    all_flights = []
    for d in dates:
        if d in cached:
            all_flights += cached[d]
    return all_flights


#parse raw api data into a table

def parse_flights(raw_flights):
    rows = []
    for item in raw_flights:
        try:
            # get the legs of the flight
            legs = item["flights"]
            if len(legs) == 0:
                continue

            first_leg = legs[0]
            last_leg = legs[-1]
            stops = len(legs) - 1

            # get airline names 
            airline_names = []
            for leg in legs:
                name = leg["airline"]
                if name not in airline_names:
                    airline_names.append(name)
            airline_str = " + ".join(airline_names)

            # get flight numbers
            nums = []
            for leg in legs:
                nums.append(leg["flight_number"])
            flight_num_str = " / ".join(nums)

            # get layover info
            layovers = item.get("layovers", [])
            lay_airports = []
            has_overnight = False
            for lay in layovers:
                lay_airports.append(lay.get("id", ""))
                if lay.get("overnight", False):
                    has_overnight = True
            lay_str = " -> ".join(lay_airports) if lay_airports else "None"

            # carbon emissions
            carbon = None
            if "carbon_emissions" in item:
                carbon = item["carbon_emissions"].get("this_flight")

            row = {
                "date": item["_date"],
                "price_usd": item["price"],
                "total_duration_min": item["total_duration"],
                "num_stops": stops,
                "airline": airline_str,
                "flight_numbers": flight_num_str,
                "departure_airport": first_leg["departure_airport"]["id"],
                "departure_time": first_leg["departure_airport"]["time"],
                "arrival_airport": last_leg["arrival_airport"]["id"],
                "arrival_time": last_leg["arrival_airport"]["time"],
                "layover_airports": lay_str,
                "overnight_layover": has_overnight,
                "carbon_g": carbon,
                "travel_class": first_leg.get("travel_class", "Economy"),
            }
            rows.append(row)
        except (KeyError, IndexError):
            # some results have missing data, skip them
            continue

    if len(rows) == 0:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["price_usd"] = pd.to_numeric(df["price_usd"], errors="coerce")
    df["total_duration_min"] = pd.to_numeric(df["total_duration_min"], errors="coerce")
    df["num_stops"] = pd.to_numeric(df["num_stops"], errors="coerce").astype("Int64")
    df["carbon_g"] = pd.to_numeric(df["carbon_g"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=["price_usd"])
    return df

# Filters the flight dataframe
def apply_filters(df, filters):
    if not filters or df.empty:
        return df

    result = df.copy()
    # filter by max stops
    if "max_stops" in filters and filters["max_stops"] is not None:
        result = result[result["num_stops"] <= filters["max_stops"]]

    # filter by max duration
    if "max_duration" in filters and filters["max_duration"] is not None:
        result = result[result["total_duration_min"] <= filters["max_duration"]]

    # filter by max price
    if "max_price" in filters and filters["max_price"] is not None:
        result = result[result["price_usd"] <= filters["max_price"]]

    # filter by no overnight layovers
    if filters.get("no_overnight", False):
        result = result[result["overnight_layover"] == False]

    return result

# Search all flights
def search_all(dep, arr, start_date, end_date, filters=None, use_cache=False):
    raw = fetch_date_range(dep, arr, start_date, end_date, use_cache)
    if not raw:
        return pd.DataFrame()
    df = parse_flights(raw)
    if df.empty:
        return pd.DataFrame()
    df = apply_filters(df, filters)
    if df.empty:
        return pd.DataFrame()
    df = df.sort_values("price_usd").reset_index(drop=True)
    df.index += 1
    return df
