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
        if not filename.endswith(".json"):
            continue
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
        if not df.empty:
            all_routes[route] = df

    return all_routes


def print_summary(df):
    if df.empty:
        print("No data.")
        return

    prices = df["price_usd"].dropna()
    print("Price Summary:")
    print("  Mean:   $" + str(round(prices.mean(), 2)))
    print("  Median: $" + str(round(prices.median(), 2)))
    print("  Std:    $" + str(round(prices.std(), 2)))
    print("  Min:    $" + str(round(prices.min(), 2)))
    print("  Max:    $" + str(round(prices.max(), 2)))

    cheapest_row = df.loc[df["price_usd"].idxmin()]
    print("  Cheapest airline: " + str(cheapest_row["airline"]) + " @ $" + str(round(cheapest_row["price_usd"], 2)))

    daily_avg = df.groupby("date")["price_usd"].mean()
    best_date = daily_avg.idxmin()
    print("  Best date to fly: " + str(best_date) + " (avg $" + str(round(daily_avg.min(), 2)) + ")")
    print("  Total flights found: " + str(len(df)))


def print_destination_info(arrival_iata):
    info = web_scraper.scrape_destination_info(arrival_iata)
    city = info["city"]

    print("\nDestination: " + city)

    print("Top Attractions:")
    for i, place in enumerate(info["top_attractions"][:10]):
        print("  " + str(i + 1) + ". " + place)

    print("Local Cuisine:")
    for item in info["cuisine"][:5]:
        print("  - " + item)

    print("Cost of Living:")
    for key, val in info["cost_of_living"].items():
        print("  " + key + ": " + val)


def chart_price_trend(df, route_name):
    if df.empty or "date" not in df.columns:
        return

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
    print("Saved price_trend_" + route_name + ".png")


def chart_airline_comparison(df, route_name):
    if df.empty or "airline" not in df.columns:
        return

    airline_avg = df.groupby("airline")["price_usd"].mean().sort_values()

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(list(airline_avg.index), list(airline_avg.values), color="steelblue")
    ax.set_title("Average Price by Airline - " + route_name)
    ax.set_xlabel("Average Price (USD)")
    ax.grid(axis="x")
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "airline_comparison_" + route_name + ".png"), dpi=150)
    plt.close(fig)
    print("Saved airline_comparison_" + route_name + ".png")


def chart_stop_distribution(df, route_name):
    if df.empty or "num_stops" not in df.columns:
        return

    counts = df["num_stops"].value_counts().sort_index()
    labels = []
    for i in counts.index:
        if i == 0:
            labels.append("Nonstop")
        elif i == 1:
            labels.append("1 Stop")
        else:
            labels.append(str(i) + " Stops")

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(list(counts.values), labels=labels, autopct="%1.1f%%", startangle=140)
    ax.set_title("Stops Distribution - " + route_name)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "stop_distribution_" + route_name + ".png"), dpi=150)
    plt.close(fig)
    print("Saved stop_distribution_" + route_name + ".png")


def chart_duration_vs_price(df, route_name):
    if df.empty or "total_duration_min" not in df.columns:
        return

    df2 = df.dropna(subset=["total_duration_min", "price_usd"])

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.scatter(df2["total_duration_min"] / 60, df2["price_usd"], alpha=0.6, color="steelblue")
    ax.set_title("Duration vs Price - " + route_name)
    ax.set_xlabel("Total Duration (hours)")
    ax.set_ylabel("Price (USD)")
    ax.grid(True)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "duration_vs_price_" + route_name + ".png"), dpi=150)
    plt.close(fig)
    print("Saved duration_vs_price_" + route_name + ".png")


def chart_route_comparison(all_routes):
    if not all_routes:
        return

    route_names = []
    min_prices = []
    avg_prices = []

    for route, df in all_routes.items():
        if df.empty or "price_usd" not in df.columns:
            continue
        route_names.append(route)
        min_prices.append(round(df["price_usd"].min(), 2))
        avg_prices.append(round(df["price_usd"].mean(), 2))

    x = list(range(len(route_names)))

    fig, ax = plt.subplots(figsize=(10, 5))
    bar_width = 0.35
    ax.bar([i - bar_width / 2 for i in x], min_prices, width=bar_width, label="Min Price", color="steelblue")
    ax.bar([i + bar_width / 2 for i in x], avg_prices, width=bar_width, label="Avg Price", color="orange")
    ax.set_xticks(x)
    ax.set_xticklabels(route_names, rotation=20, ha="right")
    ax.set_ylabel("Price (USD)")
    ax.set_title("Price Comparison Across All Routes")
    ax.legend()
    ax.grid(axis="y")
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "route_comparison.png"), dpi=150)
    plt.close(fig)
    print("Saved route_comparison.png")


def chart_weather(arrival_iata):
    city = web_scraper.airport_to_city(arrival_iata)
    forecast = web_scraper.scrape_timeanddate_weather(city)

    if not forecast:
        print("No weather data for " + city)
        return

    days = []
    highs = []
    lows = []
    chances = []

    for entry in forecast[:14]:
        days.append(entry["day"])

        temp_str = entry.get("temperature", "")
        match = re.findall(r"\d+", temp_str)
        if len(match) >= 2:
            highs.append(int(match[0]))
            lows.append(int(match[1]))
        elif len(match) == 1:
            highs.append(int(match[0]))
            lows.append(int(match[0]))
        else:
            highs.append(0)
            lows.append(0)

        chance_str = entry.get("chance", "0%")
        chance_match = re.findall(r"\d+", chance_str)
        chances.append(int(chance_match[0]) if chance_match else 0)

    x = list(range(len(days)))

    fig, ax1 = plt.subplots(figsize=(12, 5))
    ax2 = ax1.twinx()

    ax1.plot(x, highs, marker="o", color="tomato", linewidth=2, label="High (°F)")
    ax1.plot(x, lows, marker="o", color="steelblue", linewidth=2, label="Low (°F)")
    ax1.fill_between(x, lows, highs, alpha=0.1, color="gray")
    ax2.bar(x, chances, alpha=0.3, color="blue", label="Rain Chance (%)")

    ax1.set_xticks(x)
    ax1.set_xticklabels(days, rotation=30, ha="right", fontsize=8)
    ax1.set_ylabel("Temperature (°F)")
    ax2.set_ylabel("Rain Chance (%)")
    ax2.set_ylim(0, 100)
    ax1.set_title("Weather Forecast - " + city)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right")
    ax1.grid(axis="y", linestyle="--", alpha=0.4)

    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "weather_" + city.replace(" ", "_") + ".png"), dpi=150)
    plt.close(fig)
    print("Saved weather_" + city + ".png")


if __name__ == "__main__":
    print("Loading all cached routes...")
    all_routes = load_all_routes()
    print("Routes loaded: " + str(list(all_routes.keys())))

    for route_name, df in all_routes.items():
        print("\n--- " + route_name + " ---")
        print_summary(df)
        chart_price_trend(df, route_name)
        chart_airline_comparison(df, route_name)
        chart_stop_distribution(df, route_name)
        chart_duration_vs_price(df, route_name)

        arrival_iata = route_name.split("_")[-1]
        print_destination_info(arrival_iata)
        chart_weather(arrival_iata)

    chart_route_comparison(all_routes)
    print("\nAll charts saved to: " + OUTPUT_DIR)

