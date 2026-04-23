"""
File: app.py
Team Name: AirAudit
Team Members:
- Menaka Ananda (AndrewID: mgowdaan)
- Chao Huang (AndrewID: chaoh)
- Rong Guo (AndrewID: rongguo)
- Tracy Yang (AndrewID: tracyy)
Description: 
Enhanced GUI for AirAudit. Features professional CSS injection, 
real-time data filtering, and high-fidelity visualization tabs.

run with: streamlit run app.py
"""
import streamlit as st
import pandas as pd
import flight_data
import web_scraper
import analysis_module
import os
from datetime import datetime

# --- UI CONFIG ---
st.set_page_config(page_title="AirAudit | Cloud Traveler", layout="wide")

# ── City banner photos (Unsplash, free, no key needed) ──────────────────────
CITY_PHOTOS = {
    # US cities
    "Los Angeles":   "https://images.unsplash.com/photo-1534190760961-74e8c1c5c3da?w=1200&q=80",
    "San Diego":     "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1200&q=80",
    "Pittsburgh":    "https://images.unsplash.com/photo-1600695268275-1a6468700bd5?w=1200&q=80",
    "Chicago":       "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=1200&q=80",
    "New York":      "https://images.unsplash.com/photo-1534430480872-3498386e7856?w=1200&q=80",
    "Miami":         "https://images.unsplash.com/photo-1533106497176-45ae19e68ba2?w=1200&q=80",
    "Seattle":       "https://images.unsplash.com/photo-1502175353174-a7a70e73b362?w=1200&q=80",
    "Denver":        "https://images.unsplash.com/photo-1619468129361-605ebea04b44?w=1200&q=80",
    "Atlanta":       "https://images.unsplash.com/photo-1575917649705-5b59aaa12e6b?w=1200&q=80",
    "Boston":        "https://images.unsplash.com/photo-1501979376754-f519a8a8af05?w=1200&q=80",
    "Las Vegas":     "https://images.unsplash.com/photo-1581351721010-8cf859cb14a4?w=1200&q=80",
    "San Francisco": "https://images.unsplash.com/photo-1501594907352-04cda38ebc29?w=1200&q=80",
    "Houston":       "https://images.unsplash.com/photo-1530089711124-9ca31fb9e863?w=1200&q=80",
    "Phoenix":       "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=1200&q=80",
    "New Orleans":   "https://images.unsplash.com/photo-1568794500574-7d31e84c4f8b?w=1200&q=80",
    # International cities
    "Tokyo":         "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=1200&q=80",
    "London":        "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=1200&q=80",
    "Paris":         "https://images.unsplash.com/photo-1499856871958-5b9627545d1a?w=1200&q=80",
    "Sydney":        "https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9?w=1200&q=80",
    "Bangkok":       "https://images.unsplash.com/photo-1563492065599-3520f775eeed?w=1200&q=80",
    "Singapore":     "https://images.unsplash.com/photo-1525625293386-3f8f99389edd?w=1200&q=80",
    "Beijing":       "https://images.unsplash.com/photo-1508804185872-d7badad00f7d?w=1200&q=80",
    "Shanghai":      "https://images.unsplash.com/photo-1538428494232-9c0d8a3ab403?w=1200&q=80",
    "Nanjing":       "https://images.unsplash.com/photo-1584464491033-06628f3a6b7b?w=1200&q=80",
    "Busan":         "https://images.unsplash.com/photo-1578637387939-43c525550085?w=1200&q=80",
}

# ── Landing page city preview cards — 1 row of 4 ─────────────────────────────
LANDING_CITY_CARDS = [
    ("New York",      "https://images.unsplash.com/photo-1534430480872-3498386e7856?w=600&q=75"),
    ("Chicago",       "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=600&q=75"),
    ("Los Angeles",   "https://images.unsplash.com/photo-1534190760961-74e8c1c5c3da?w=600&q=75"),
    ("Miami",         "https://images.unsplash.com/photo-1533106497176-45ae19e68ba2?w=600&q=75"),
]

st.markdown("""
    <style>
    /* ── Hero cost box ────────────────────────────────────────────── */
    .hero-box {
        background: #1a1f2e;
        border: 1px solid rgba(255,255,255,0.08);
        padding: 36px 40px;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 28px;
    }
    .hero-label {
        text-transform: uppercase;
        letter-spacing: 3px;
        font-size: 0.8rem;
        color: #8892a4;
        margin-bottom: 6px;
    }
    .hero-total {
        font-size: 3.8rem;
        font-weight: 800;
        color: #ffffff;
        margin: 0 0 12px 0;
        line-height: 1;
    }
    .hero-breakdown { color: #b0bac8; font-size: 0.95rem; line-height: 1.8; }
    .hero-breakdown b { color: #d8e0ec; }
    .hero-breakdown small { color: #6b7789; font-size: 0.82rem; }

    /* ── Destination banner ───────────────────────────────────────── */
    .dest-banner {
        position: relative;
        height: 220px;
        border-radius: 14px;
        overflow: hidden;
        margin-bottom: 24px;
    }
    .dest-banner img {
        width: 100%; height: 100%;
        object-fit: cover;
        display: block;
    }
    .dest-banner-overlay {
        position: absolute; inset: 0;
        background: linear-gradient(to top, rgba(0,0,0,0.72) 0%, rgba(0,0,0,0.10) 60%);
        display: flex; align-items: flex-end;
        padding: 20px 24px;
    }
    .dest-banner-title {
        color: #fff;
        font-size: 1.9rem;
        font-weight: 800;
        text-shadow: 0 2px 8px rgba(0,0,0,0.5);
        margin: 0;
        line-height: 1;
    }
    .dest-banner-sub {
        color: rgba(255,255,255,0.75);
        font-size: 0.85rem;
        margin: 4px 0 0 2px;
    }

    /* ── Flight cards ─────────────────────────────────────────────── */
    .f-card {
        background: var(--background-color, #fff);
        border: 1px solid rgba(128,128,128,0.18);
        padding: 16px 18px;
        border-radius: 12px;
        margin-bottom: 12px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }
    .f-top  { display: flex; justify-content: space-between; align-items: center; }
    .f-airline { font-size: 1.1rem; font-weight: 700; color: #0984e3; }
    .f-price   { font-size: 1.5rem; color: #27ae60; font-weight: 800; }
    .f-detail  {
        color: var(--text-color, #555);
        opacity: 0.82;
        font-size: 0.87rem;
        margin-top: 6px;
        line-height: 1.55;
    }

    /* ── Estimated cost badge ─────────────────────────────────────── */
    .est-badge {
        display: inline-block;
        font-size: 0.7rem;
        background: rgba(255,180,0,0.12);
        color: #b8860b;
        border: 1px solid rgba(184,134,11,0.3);
        border-radius: 4px;
        padding: 1px 5px;
        margin-left: 4px;
        vertical-align: middle;
    }

    /* ── Landing page ─────────────────────────────────────────────── */
    .landing-hero {
        position: relative;
        border-radius: 16px;
        overflow: hidden;
        margin-bottom: 28px;
        height: 360px;
    }
    .landing-hero img {
        width: 100%; height: 100%;
        object-fit: cover;
        display: block;
        filter: brightness(0.55);
    }
    .landing-hero-overlay {
        position: absolute; inset: 0;
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        text-align: center;
        padding: 20px;
    }
    .landing-hero-overlay h1 {
        font-size: 3rem !important;
        font-weight: 800 !important;
        color: #ffffff !important;
        margin-bottom: 10px;
        text-shadow: 0 3px 12px rgba(0,0,0,0.5);
    }
    .landing-hero-overlay p {
        font-size: 1.1rem;
        color: rgba(255,255,255,0.82);
        max-width: 500px;
        margin-bottom: 20px;
    }
    .landing-stat-row {
        display: flex; gap: 14px; justify-content: center;
    }
    .landing-stat {
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.18);
        border-radius: 10px;
        padding: 8px 20px;
        color: #fff;
        font-size: 0.82rem;
        backdrop-filter: blur(6px);
    }
    .landing-stat b { display: block; font-size: 1.25rem; }

    /* ── City preview cards on landing ───────────────────────────── */
    .city-card {
        position: relative;
        border-radius: 12px;
        overflow: hidden;
        height: 130px;
        cursor: default;
    }
    .city-card img { width: 100%; height: 100%; object-fit: cover; display: block; }
    .city-card-label {
        position: absolute; bottom: 0; left: 0; right: 0;
        background: linear-gradient(to top, rgba(0,0,0,0.7), transparent);
        color: #fff; font-weight: 700; font-size: 0.9rem;
        padding: 8px 10px;
    }
    </style>
""", unsafe_allow_html=True)


def main():
    CITY_OPTIONS = {f"{v} ({k})": k for k, v in web_scraper.AIRPORT_TO_CITY.items()}
    CITY_LIST = sorted(list(CITY_OPTIONS.keys()))

    if 'audit_data' not in st.session_state:
        st.session_state.audit_data = None
    if 'sel_price' not in st.session_state:
        st.session_state.sel_price = 0.0

    # ── SIDEBAR ────────────────────────────────────────────────────────────
    with st.sidebar:
        st.title("☁️ AirAudit Terminal")
        origin_full = st.selectbox("Departure City", CITY_LIST, index=0)
        dest_full   = st.selectbox("Destination City", CITY_LIST, index=2)

        dep_iata = CITY_OPTIONS[origin_full]
        arr_iata = CITY_OPTIONS[dest_full]

        c1, c2 = st.columns(2)
        start = c1.date_input("Outbound", datetime(2026, 5, 1))
        end   = c2.date_input("Inbound",  datetime(2026, 5, 10))

        st.markdown("### 🏨 Stay Style")
        travel_style = st.select_slider(
            "Select Comfort Level",
            options=["Budget", "Mid-Range", "Luxury"],
            value="Mid-Range"
        )

        stops    = st.selectbox("Flight Layovers", ["Any", "Non-stop", "1 Stop", "2+ Stops"])
        stop_map = {"Any": None, "Non-stop": 0, "1 Stop": 1, "2+ Stops": 2}

        st.markdown("### 🗄️ Data Source")
        use_cache = st.radio(
            "Flight data source",
            options=["Use cached data (fast)", "Fetch live data (uses API quota)"],
            index=0,
            help="Cached data reuses previously downloaded flights. Live fetch calls SerpApi and counts against your monthly quota."
        ) == "Use cached data (fast)"

        if st.button("CALCULATE TOTAL TRIP COST", type="primary", use_container_width=True):
            with st.spinner("Analyzing destination markers..."):
                st.session_state.audit_data = {
                    'flights':  flight_data.search_all(
                        dep_iata, arr_iata, str(start), str(end),
                        filters={"max_stops": stop_map[stops]}, use_cache=use_cache
                    ),
                    'dest':     web_scraper.scrape_destination_info(arr_iata),
                    'days':     (end - start).days if (end - start).days > 0 else 1,
                    'route_id': f"{dep_iata}_{arr_iata}",
                    'start':    start,
                    'end':      end,
                }
                st.session_state.sel_price = 0.0

    # ── MAIN CONTENT ────────────────────────────────────────────────────────
    if st.session_state.audit_data:
        data  = st.session_state.audit_data
        costs = data['dest']['cost_of_living']
        city  = data['dest']['city']

        style_mult    = {"Budget": 0.6, "Mid-Range": 1.0, "Luxury": 2.0}[travel_style]
        daily_living  = costs['daily_living']  * style_mult
        nightly_hotel = costs['nightly_hotel'] * style_mult
        daily_rate    = daily_living + nightly_hotel
        total_land    = daily_rate * data['days']
        grand_total   = st.session_state.sel_price + total_land

        cost_source = costs.get('source', 'estimated')
        badge       = '' if cost_source == 'scraped' else '<span class="est-badge">est.</span>'
        source_note = {'scraped': '(live · Numbeo)', 'estimated': '(estimated)'}.get(cost_source, '(estimated)')

        # ── Flight selection nudge (only shown before a flight is picked) ───
        if st.session_state.sel_price == 0.0:
            st.info("✈️ **Select a flight below** to include the fare in your total trip cost.", icon=None)

        # ── Cost hero ──────────────────────────────────────────────────────
        st.markdown(f"""
            <div class="hero-box">
                <p class="hero-label">{data['days']}-Day Trip to {city}</p>
                <h1 class="hero-total">${grand_total:,.0f}</h1>
                <div class="hero-breakdown">
                    <b>✈️ Flight</b>&nbsp; {'<span style="color:#f39c12;">not selected</span>' if st.session_state.sel_price == 0.0 else f'${st.session_state.sel_price:,.0f}'}
                    &nbsp;&nbsp;·&nbsp;&nbsp;
                    <b>🏨 Hotel</b>&nbsp; ${nightly_hotel * data['days']:,.0f}{badge}
                    &nbsp;&nbsp;·&nbsp;&nbsp;
                    <b>🍽️ Living</b>&nbsp; ${daily_living * data['days']:,.0f}{badge}
                    <br>
                    <small>${daily_rate:,.0f}/day &nbsp;·&nbsp; {travel_style} style &nbsp;·&nbsp; costs {source_note}</small>
                </div>
            </div>
        """, unsafe_allow_html=True)

        tab1, tab2, tab3 = st.tabs(["✈️ Flight Search", "🌍 Destination Intel", "📈 Market Analytics"])

        # ── Tab 1: Flights ─────────────────────────────────────────────────
        with tab1:
            st.subheader("Select an Itinerary")
            if data['flights'].empty:
                st.info("No flights found for this route and date range. Try different dates or remove stop filters.")
            else:
                for i, row in data['flights'].head(10).iterrows():
                    c_info, c_sel = st.columns([5, 1])
                    with c_info:
                        st.markdown(f"""
                            <div class="f-card">
                                <div class="f-top">
                                    <span class="f-airline">{row['airline']}</span>
                                    <span class="f-price">${row['price_usd']:,.0f}</span>
                                </div>
                                <div class="f-detail">
                                    <b>Flight:</b> {row['flight_numbers']} &nbsp;|&nbsp;
                                    <b>Duration:</b> {int(row['total_duration_min'])//60}h {int(row['total_duration_min'])%60}m<br>
                                    <b>Route:</b> {row['departure_airport']} ({row['departure_time']}) → {row['arrival_airport']} ({row['arrival_time']})<br>
                                    <b>Stops:</b> {row['num_stops']} &nbsp;|&nbsp; {row['layover_airports']}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                    with c_sel:
                        if st.button("Select", key=f"btn_{i}", use_container_width=True):
                            st.session_state.sel_price = row['price_usd']
                            st.rerun()

                st.divider()
                csv_data = data['flights'].to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="⬇️ Download All Flights as CSV",
                    data=csv_data,
                    file_name=f"flights_{data['route_id']}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

        # ── Tab 2: Destination Intel ───────────────────────────────────────
        with tab2:
            # City banner photo
            banner_url = CITY_PHOTOS.get(city, "https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=1200&q=80")
            st.markdown(f"""
                <div class="dest-banner">
                    <img src="{banner_url}" alt="{city}">
                    <div class="dest-banner-overlay">
                        <div>
                            <p class="dest-banner-title">{city}</p>
                            <p class="dest-banner-sub">{data['days']}-day itinerary · {travel_style}</p>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("🏛️ Must-See Attractions")
                attractions = data['dest']['top_attractions']
                if attractions:
                    for place in attractions[:12]:
                        st.write(f"✅ **{place}**")
                else:
                    st.info("Attraction data unavailable for this destination.")

                st.divider()
                st.subheader("🍱 Local Cuisine")
                cuisine = data['dest']['cuisine']
                if cuisine:
                    for dish in cuisine:
                        st.write(f"🍜 {dish}")
                else:
                    st.info("Cuisine data unavailable for this destination.")

            with col_b:
                st.subheader("☀️ Weather Forecast")
                weather = data['dest']['weather']
                if weather:
                    from datetime import timedelta
                    import re as _re

                    trip_start = data['start']
                    trip_end   = data['end']

                    # timeanddate day strings look like "MonApr 20" or "Sat Apr 18"
                    # We parse them to a date using the current year, then filter.
                    current_year = trip_start.year
                    filtered = []
                    for row in weather:
                        raw = row['day'].strip()
                        # Strip leading weekday (3 chars) — leaves e.g. "Apr 20" or "Apr20"
                        day_part = raw[3:].strip()
                        try:
                            from datetime import datetime as _dt
                            # Try "Apr 20" format first, then "Apr20"
                            for fmt in ("%b %d", "%b%d"):
                                try:
                                    parsed = _dt.strptime(f"{day_part} {current_year}", f"{fmt} %Y").date()
                                    break
                                except ValueError:
                                    parsed = None
                            if parsed and trip_start <= parsed <= trip_end:
                                filtered.append(row)
                        except Exception:
                            continue

                    # If parsing matched nothing (e.g. trip is far future), fall back to slice
                    display = filtered if filtered else weather[:data['days']]
                    st.table(pd.DataFrame(display))
                else:
                    st.info("Weather forecast unavailable.")

            st.divider()
            st.subheader("💰 Cost of Living Breakdown")
            cc = st.columns(3)
            cc[0].metric("Daily Living", f"${costs['daily_living']:.0f}",
                         help="Food, transport & activities per person per day (before style multiplier)")
            cc[1].metric("Nightly Hotel", f"${costs['nightly_hotel']:.0f}",
                         help="Estimated nightly rate (before style multiplier)")
            cc[2].metric("Style Multiplier", f"{style_mult:.1f}×",
                         help=f"{travel_style} tier applied to both figures above")

        # ── Tab 3: Analytics ───────────────────────────────────────────────
        with tab3:
            st.subheader("Market Volatility & Data Analysis")
            if not data['flights'].empty:
                analysis_module.chart_price_trend(data['flights'], data['route_id'])
                analysis_module.chart_stop_distribution(data['flights'], data['route_id'])

                c_plot1, c_plot2 = st.columns(2)
                trend_p = os.path.join("output", "charts", f"price_trend_{data['route_id']}.png")
                stop_p  = os.path.join("output", "charts", f"stop_distribution_{data['route_id']}.png")

                if os.path.exists(trend_p):
                    c_plot1.image(trend_p, caption="Flight Price Trend (USD)")
                if os.path.exists(stop_p):
                    c_plot2.image(stop_p,  caption="Stop Distribution Breakdown")
            else:
                st.info("No flight data to chart yet.")

    # ── LANDING PAGE ────────────────────────────────────────────────────────
    else:
        # Hero: photo with only the brand name — nothing else
        st.markdown("""
            <div class="landing-hero">
                <img src="https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=1600&q=80"
                     alt="Aerial view of plane over clouds">
                <div class="landing-hero-overlay">
                    <h1>✈️ AirAudit</h1>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # "Popular destinations" city photo grid — 1 row of 4
        st.markdown("#### 🌍 Popular Destinations")
        row_cols = st.columns(4)
        for col, (name, url) in zip(row_cols, LANDING_CITY_CARDS):
            col.markdown(f"""
                <div class="city-card">
                    <img src="{url}" alt="{name}">
                    <div class="city-card-label">{name}</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### How it works")
        c1, c2, c3 = st.columns(3)
        c1.info("**1. Pick your route**\nChoose departure & destination cities plus travel dates in the sidebar.")
        c2.info("**2. Set your style**\nBudget, Mid-Range, or Luxury — adjusts hotel & daily spend estimates.")
        c3.info("**3. Get your audit**\nSee real flight options with total trip cost including on-the-ground expenses.")


if __name__ == "__main__":
    main()