"""
File: app.py
Team Name: AirAudit
Team Members:
- Menaka Ananda (AndrewID: [ID 1])
- Chao Huang (AndrewID: chaoh)
- Rong Guo (AndrewID: [ID 3])
- Tracy Yang (AndrewID: [ID 4])

Description: 
This is the main graphical user interface (GUI) module for our Flight Search project. 
It uses the Streamlit library to render an interactive web page. It imports our custom 
'flight_data' module to fetch, clean, and filter SerpApi (Google Flights) data based 
on user inputs from the sidebar. 

run with: streamlit run app.py
"""


import pandas as pd
import streamlit as st
import flight_data

# Set up the basic configuration of the web page
st.set_page_config(page_title="Flight Search", page_icon="✈️", layout="wide")

# columns we want to show in the table
SHOW_COLS = [
    "date", "price_usd", "airline", "num_stops",
    "departure_airport", "departure_time",
    "arrival_airport", "arrival_time",
    "total_duration_min", "total_duration_hm",
    "layover_airports", "overnight_layover",
    "flight_numbers", "travel_class", "carbon_g",
]

# convert the duration of the flight to hours and minutes
def format_duration(minutes_col):
    """
    Helper function to convert raw integer minutes into a human-readable 
    hours and minutes format (e.g., 330 -> "5h 30m").
    """
    results = []
    for val in minutes_col:
        if pd.isna(val):
            results.append("")
        else:
            total = int(val)
            h = total // 60
            m = total % 60
            results.append(f"{h}h {m}m")
    return results

# Build filters for the flight dataframe
def build_filters(max_stops, max_price, dur_hours, dur_minutes, no_overnight):
    """
    Collects the UI filter inputs from the sidebar and packages them 
    into a dictionary to be passed to the backend flight_data module.
    """
    filters = {}
    if max_stops is not None:
        filters["max_stops"] = int(max_stops)
    if max_price and max_price > 0:
        filters["max_price"] = float(max_price)
    total_min = int(dur_hours) * 60 + int(dur_minutes)
    if total_min > 0:
        filters["max_duration"] = total_min
    if no_overnight:
        filters["no_overnight"] = True
    return filters


def main():
    st.title("Flight Search")
    st.caption("Powered by SerpApi (Google Flights)")

    if not flight_data.API_KEY:
        st.error("No API key found! Put your key in serpapi_key.txt.")
        st.stop()

    # sidebar inputs for the search
    with st.sidebar:
        st.header("Search")
        dep = st.text_input("From (IATA)", value="PIT", max_chars=3).upper().strip()
        arr = st.text_input("To (IATA)", value="LAX", max_chars=3).upper().strip()

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start date", value=pd.Timestamp("2026-05-01"))
        with col2:
            end_date = st.date_input("End date", value=pd.Timestamp("2026-05-05"))

        use_cache = st.checkbox("Use cached data when possible", value=False,
                                help="Loads saved results from cache folder, only fetches days not cached yet")
        top_n = st.slider("How many results to show", min_value=5, max_value=50, value=15, step=5)

        st.divider()
        st.subheader("Filters")

        max_stops = st.selectbox("Max stops", options=[None, 0, 1, 2],
                                 format_func=lambda x: "Any" if x is None else f"<= {x}")
        max_price = st.number_input("Max price (USD)", min_value=0.0, value=0.0, step=50.0, help="0 = no limit")

        st.caption("Max flight duration")
        dh_col, dm_col = st.columns(2)
        with dh_col:
            dur_h = st.number_input("Hours", min_value=0, max_value=72, value=0, step=1, help="0h 0m = no limit")
        with dm_col:
            dur_m = st.number_input("Minutes", min_value=0, max_value=59, value=0, step=1)

        no_overnight = st.checkbox("No overnight layovers", value=False)

        search_btn = st.button("Search", type="primary", use_container_width=True)

    # Convert dates to string format required by the backend API
    start_str = pd.Timestamp(start_date).strftime("%Y-%m-%d")
    end_str = pd.Timestamp(end_date).strftime("%Y-%m-%d")

    if not search_btn:
        st.info("Fill in the sidebar and click Search.")
        return

    if len(dep) != 3 or len(arr) != 3:
        st.warning("Please use 3-letter IATA airport codes (e.g. PIT, LAX)")
        return

    filters = build_filters(max_stops, max_price, dur_h, dur_m, no_overnight)

    with st.spinner("Fetching flight data..."):
        try:
            all_results = flight_data.search_all(
                dep, arr, start_str, end_str,
                filters=filters if filters else None,
                use_cache=use_cache,
            )
        except ValueError as e:
            st.error(str(e))
            return
        except Exception as e:
            st.error(f"Something went wrong: {e}")
            return

    if all_results.empty:
        st.warning("No flights found. Try different dates or relax the filters.")
        return

    # show results
    show = all_results.head(top_n)

    # add readable duration column
    show = show.copy()
    show["total_duration_hm"] = format_duration(show["total_duration_min"])

    # pick columns that exist
    display_cols = [c for c in SHOW_COLS if c in show.columns]
    display_df = show[display_cols].copy()

    # format date and price for display
    if "date" in display_df.columns:
        display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")
    if "price_usd" in display_df.columns:
        display_df["price_usd"] = display_df["price_usd"].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "")

    # summary stats
    prices = all_results["price_usd"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cheapest", f"${prices.min():,.0f}")
    c2.metric("Average", f"${prices.mean():,.0f}")
    c3.metric("Total matches", str(len(all_results)))
    c4.metric("Showing", str(len(show)))

    st.subheader("Results (cheapest first)")
    st.dataframe(display_df, use_container_width=True, hide_index=False)

    # csv download
    csv_df = show.copy()
    if "date" in csv_df.columns:
        csv_df["date"] = csv_df["date"].dt.strftime("%Y-%m-%d")
    csv_bytes = csv_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("Download CSV", data=csv_bytes,
                       file_name=f"{dep}_{arr}_{start_str}_{end_str}.csv",
                       mime="text/csv")



if __name__ == "__main__":
    main()
