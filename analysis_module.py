"""
File: analysis_module.py
Team Name: AirAudit
Team Members:
- Menaka Ananda (AndrewID: [ID 1])
- Chao Huang (AndrewID: chaoh)
- Rong Guo (AndrewID: [ID 3])
- Tracy Yang (AndrewID: [ID 4])

Description:
This module handles data analysis and visualization for the AirAudit project.
It takes flight data from flight_data.py and destination/weather data from
web_scraper.py, then generates charts and statistical summaries.

Imported by: app.py
"""

import os
import re
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import flight_data
import web_scraper

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "charts")
os.makedirs(OUTPUT_DIR, exist_ok=True)
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")


def load_all_routes():
    all_routes = {}
    if not os.path.isdir(CACHE_DIR):
        print("No cache folder found.")
        return all_routes

    for filename in os.listdir(CACHE_DIR):
        if not filename.endswith(".json"): continue
        route = filename.replace(".json", "")
        path = os.path.join(CACHE_DIR, filename)
        with open(path, "r", encoding="utf-8") as f:
            by_date = json.load(f)

        all_flights = []
        for date, flights in by_date.items():
            for fl in flights:
                fl["_date"] = date
                all_flights.append(fl)

        df = flight_data.parse_flights(all_flights)
        if not df.empty: all_routes[route] = df
    return all_routes


def chart_price_trend(df, route_name):
    if df.empty: return
    daily = df.groupby("date")["price_usd"].mean().sort_index()
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(daily.index, daily.values, marker="o", color="steelblue", linewidth=2)
    ax.set_title("Price Trend - " + route_name)
    ax.set_xlabel("Date")
    ax.set_ylabel("Average Price (USD)")
    ax.grid(True)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "price_trend_" + route_name + ".png"), dpi=150)
    plt.close(fig)

def chart_stop_distribution(df, route_name):
    if df.empty: return
    counts = df["num_stops"].value_counts().sort_index()
    labels = ["Nonstop" if i == 0 else f"{i} Stops" for i in counts.index]
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(list(counts.values), labels=labels, autopct="%1.1f%%", startangle=140)
    ax.set_title("Stops Distribution - " + route_name)
    fig.savefig(os.path.join(OUTPUT_DIR, "stop_distribution_" + route_name + ".png"), dpi=150)
    plt.close(fig)

def chart_duration_vs_price(df, route_name):
    if df.empty: return
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.scatter(df["total_duration_min"] / 60, df["price_usd"], alpha=0.6, color="steelblue")
    ax.set_title("Duration vs Price - " + route_name)
    ax.set_xlabel("Total Duration (hours)")
    ax.set_ylabel("Price (USD)")
    ax.grid(True)
    fig.savefig(os.path.join(OUTPUT_DIR, "duration_vs_price_" + route_name + ".png"), dpi=150)
    plt.close(fig)

def chart_weather(arrival_iata):
    city = web_scraper.airport_to_city(arrival_iata)
    forecast = web_scraper.scrape_timeanddate_weather(city)
    if not forecast: return
    
    days = [e["day"] for e in forecast[:14]]
    # Simplified high/low extraction for plot stability
    highs = [int(re.findall(r"\d+", e["temperature"])[0]) if re.findall(r"\d+", e["temperature"]) else 0 for e in forecast[:14]]
    
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(days, highs, marker="o", color="tomato", label="High (°F)")
    ax.set_title(f"Weather Forecast - {city}")
    plt.xticks(rotation=45)
    fig.savefig(os.path.join(OUTPUT_DIR, f"weather_{city.replace(' ', '_')}.png"), dpi=150)
    plt.close(fig)

if __name__ == "__main__":
    all_routes = load_all_routes()
    for route, df in all_routes.items():
        chart_price_trend(df, route)
        chart_stop_distribution(df, route)
        chart_duration_vs_price(df, route)
        chart_weather(route.split("_")[-1])