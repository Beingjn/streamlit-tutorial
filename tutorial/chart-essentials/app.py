# How to start this app
# Start the app from the project folder(in terminal):
#   streamlit run app.py
# Your browser should open to:
#   http://localhost:8501
#   (If it doesn’t, copy that URL into your browser.)
# Stop the app: press Ctrl+C in the terminal.

import numpy as np
import pandas as pd
import streamlit as st
import altair as alt
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Chart Essentials", layout="centered")

conn = st.connection("gsheets", type=GSheetsConnection)
try:
    df = conn.read()
except Exception as e:
    st.error(f"Could not read from Google Sheet: {e}")
    st.stop()


df["date"] = pd.to_datetime(df["date"], errors="coerce")
num_cols = ["sale_price", "list_price", "purchase_price", "size", "CDOM", "latitude", "longitude", "bds", "bths", "year_built"]
for c in num_cols:
    df[c] = pd.to_numeric(df[c], errors="coerce")

df["zipcode"] = df["zipcode"].astype(str)

# Derived columns
df["profit"] = df["sale_price"] - df["purchase_price"]
df["roi_pct"] = np.where(df["purchase_price"] > 0, (df["sale_price"] - df["purchase_price"]) / df["purchase_price"], np.nan)
df["discount_pct"] = np.where(df["list_price"] > 0, (df["sale_price"] - df["list_price"]) / df["list_price"], np.nan)
df["ppsf"] = np.where(df["size"] > 0, df["sale_price"] / df["size"], np.nan)

# Helpers
df_time = df.dropna(subset=["date"])
TOP_N_CITIES = 12
top_cities = df["city"].value_counts().nlargest(TOP_N_CITIES).index
df_top_cities = df[df["city"].isin(top_cities)]
df_top_cities_time = df_top_cities.dropna(subset=["date"])

st.title("Chart Essentials")

tab_native, tab_altair, tab_reference = st.tabs(
    ["Native Charts", "Altair Syntax", "Chart Cheatsheet"]
)


# Streamlit charts
with tab_native:
    st.subheader("Quick native charts")
    st.write("Great for a first look; limited customization.")

    # Line
    _line_df = df.dropna(subset=["date", "sale_price"]).set_index("date")[["sale_price"]].sort_index()
    st.line_chart(_line_df, use_container_width=True)
    st.code(
        "st.line_chart(df.dropna(subset=['date','sale_price']).set_index('date')[['sale_price']].sort_index())",
        language="python",
    )

    # Scatter
    _scatter_df = df[['size', 'sale_price', 'city']].dropna(subset=['size', 'sale_price'])
    st.scatter_chart(_scatter_df, x='size', y='sale_price', color='city', use_container_width=True)
    st.code(
        "st.scatter_chart(df[['size','sale_price','city']].dropna(subset=['size','sale_price']), x='size', y='sale_price', color='city')",
        language="python",
    )

    st.write("\n")
    st.write("Here’s the signature of `st.line_chart`, we have very limited customizaiton options.")
    st.code("""st.line_chart(data=None, *, x=None, y=None, x_label=None, y_label=None, color=None, width="stretch", height="content", use_container_width=None)""")
    

# Basic Altair syntax 
with tab_altair:
    st.subheader("Altair: Syntax & Core Ideas")
    st.caption("Focus on how the syntax works. Additional chart types live in the Altair Reference tab.")
    st.markdown("""

""")

    st.markdown(
        """
Altair is a declarative statistical visualization library for Python built on the Vega-Lite grammar of graphics. 
Rather than drawing charts step by step, you describe your data, the visual mark (bar/line/point), and the encodings (x, y, color), 
and Altair compiles that specification into interactive charts with minimal code.
We'll be using Altair for future tutorials.
"""
    )
    df_bar = pd.DataFrame(
        {"category": list("ABCD"), "value": [3, 7, 5, 2]}
    )

    st.markdown("#### Example: Bar chart")
    chart = (
        alt.Chart(df_bar, title="Sales by Category")     # 1) Bind a DataFrame to a chart object; add a chart-level title.
        .mark_bar()                                      # 2) Choose the mark (bar, line, point, area, …). Nothing is placed until encodings are set.
        .encode(                                         # 3) Map DataFrame fields to visual channels.
            x=alt.X("category:N", title="Category"),     #    - x-axis: 'category' is Nominal (N) → discrete axis.
            y=alt.Y("value:Q", title="Sales"),           #    - y-axis: 'value' is Quantitative (Q) → continuous scale.
            color="category:N",                          #    - color by category → discrete legend, distinct hues.
            tooltip=["category:N", "value:Q"],           #    - tooltip
        )
        .properties(width=500, height=280)               # 4) Size the drawing area (affects scales/label wrapping).
    )
    st.altair_chart(chart, use_container_width=True)

    st.subheader("What each line does?")
    st.code(
        """chart = (
    alt.Chart(df_bar, title="Sales by Category")
    .mark_bar()
    .encode(
        x=alt.X("category:N", title="Category"),
        y=alt.Y("value:Q", title="Sales"),
        color="category:N",
        tooltip=["category:N", "value:Q"],
    )
    .properties(width=500, height=280)
            )
st.altair_chart(chart, use_container_width=True)
            """,
            language="python",
        )
    st.markdown(
            """
1) **`alt.Chart(df_bar, title="Sales by Category")`**  
   Creates a chart object tied to your DataFrame. `title=` sets a chart-level title. No drawing yet.

2) **`.mark_bar()`**  
   Selects the geometric glyph. Other options include `mark_point()`, `mark_line()`, `mark_area()`, etc.

3) **`.encode(...)`** (fields → visual channels)  
   - **`x=alt.X("category:N", title="Category")`**: put the categorical field on the x-axis. `:N` = **Nominal** (unordered categories).  
   - **`y=alt.Y("value:Q", title="Sales")`**: put numbers on the y-axis. `:Q` = **Quantitative** (continuous scale).  
   - **`color="category:N"`**: discrete colors per category with an automatic legend.  
   - **`tooltip=[...]`**: fields shown on hover in interactive viewers.

4) **`.properties(width=500, height=280)`**  
   Sets the size of the drawing area. Prefer sizing here (not via CSS) so scales/labels lay out correctly.

5) **`st.altair_chart(chart, use_container_width=True)`**  
   Renders the chart in Streamlit and lets it expand to the container’s width.
"""
    )
    st.info("""
    Field types include: `:Q` quantitative (numbers, continuous) · `:T` temporal (dates/times)· `:N` nominal (unordered categories)· `:O` ordinal (ordered categories)
    · `G` geojson (geographic shape)
    """
    )

# Chart Reference
with tab_reference:
    st.markdown("""
**Dataset: Greater Seattle House Flips**

This example dataset captures a real estate company's house-flipping projects across Greater Seattle, with purchase/sale dates and prices, property details (beds/baths, sqft, city, coordinates), plus derived metrics like ROI and $/sqft.
""")

    st.caption(f"{len(df):,} flips from {df['date'].min():%Y-%m-%d} to {df['date'].max():%Y-%m-%d}")

    st.dataframe(df.head(8), use_container_width=True)

    st.markdown("Altair documentation: https://altair-viz.github.io/user_guide/data.html")

    # 1) Line: flips per month
    st.subheader("Flips per Month")
    line_count = (
        alt.Chart(df_time)
        .mark_line(point=True)
        .encode(
            x="yearmonth(date):T",
            y="count()",
            tooltip=[alt.Tooltip("yearmonth(date):T", title="Month"), alt.Tooltip("count()", title="# Flips")],
        )
        .properties(height=300)
    )
    st.altair_chart(line_count, use_container_width=True)
    st.code('''alt.Chart(df_time).mark_line(point=True).encode(
        x="yearmonth(date):T",
        y="count()",
        tooltip=[alt.Tooltip("yearmonth(date):T", title="Month"), alt.Tooltip("count()", title="# Flips")]
    ).properties(height=300)''', language="python")

    # 2) Line: median sale price over time
    st.subheader("Median Sale Price Over Time")
    line_med_price = (
        alt.Chart(df_time)
        .mark_line(point=True)
        .encode(
            x="yearmonth(date):T",
            y=alt.Y("median(sale_price):Q", title="Median Sale Price (USD)"),
            tooltip=[alt.Tooltip("yearmonth(date):T", title="Month"), alt.Tooltip("median(sale_price):Q", title="Median Price")]
        )
        .properties(height=300)
    )
    st.altair_chart(line_med_price, use_container_width=True)
    st.code('''alt.Chart(df_time).mark_line(point=True).encode(
        x="yearmonth(date):T",
        y=alt.Y("median(sale_price):Q", title="Median Sale Price (USD)"),
        tooltip=[alt.Tooltip("yearmonth(date):T", title="Month"), alt.Tooltip("median(sale_price):Q", title="Median Price")]
    ).properties(height=300)''', language="python")

    # 3) Line: median ROI over time
    st.subheader("Median ROI Over Time")
    df_time_roi = df_time.dropna(subset=["roi_pct"])
    line_med_roi = (
        alt.Chart(df_time_roi)
        .mark_line(point=True)
        .encode(
            x="yearmonth(date):T",
            y=alt.Y("median(roi_pct):Q", title="Median ROI (fraction)"),
            tooltip=[alt.Tooltip("yearmonth(date):T", title="Month"), alt.Tooltip("median(roi_pct):Q", title="Median ROI")]
        )
        .properties(height=300)
    )
    st.altair_chart(line_med_roi, use_container_width=True)
    st.code('''alt.Chart(df_time.dropna(subset=["roi_pct"])).mark_line(point=True).encode(
        x="yearmonth(date):T",
        y=alt.Y("median(roi_pct):Q", title="Median ROI (fraction)"),
        tooltip=[alt.Tooltip("yearmonth(date):T", title="Month"), alt.Tooltip("median(roi_pct):Q", title="Median ROI")]
    ).properties(height=300)''', language="python")

    # 4) Bar: flips by city
    st.subheader(f"Flips by City (Top {TOP_N_CITIES})")
    bar_city_count = (
        alt.Chart(df_top_cities)
        .mark_bar()
        .encode(
            x=alt.X("city:N", sort="-y", title="City"),
            y=alt.Y("count()", title="# Flips"),
            tooltip=[alt.Tooltip("city:N", title="City"), alt.Tooltip("count()", title="# Flips")]
        )
        .properties(height=300)
    )
    st.altair_chart(bar_city_count, use_container_width=True)
    st.code(f'''top_cities = df["city"].value_counts().nlargest({TOP_N_CITIES}).index
    alt.Chart(df[df["city"].isin(top_cities)]).mark_bar().encode(
        x=alt.X("city:N", sort="-y", title="City"),
        y=alt.Y("count()", title="# Flips"),
        tooltip=[alt.Tooltip("city:N", title="City"), alt.Tooltip("count()", title="# Flips")]
    ).properties(height=300)''', language="python")

    # 5) Bar: beds popularity
    st.subheader("Beds Popularity")
    bar_beds = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("bds:O", title="Bedrooms"),
            y=alt.Y("count()", title="Count"),
            tooltip=[alt.Tooltip("bds:O", title="Bedrooms"), alt.Tooltip("count()", title="Count")]
        )
        .properties(height=300)
    )
    st.altair_chart(bar_beds, use_container_width=True)
    st.code('''alt.Chart(df).mark_bar().encode(
        x=alt.X("bds:O", title="Bedrooms"),
        y=alt.Y("count()", title="Count"),
        tooltip=[alt.Tooltip("bds:O", title="Bedrooms"), alt.Tooltip("count()", title="Count")]
    ).properties(height=300)''', language="python")

    # 6) Bar: average sale price by city
    st.subheader(f"Average Sale Price by City (Top {TOP_N_CITIES})")
    bar_avg_price_city = (
        alt.Chart(df_top_cities)
        .mark_bar()
        .encode(
            x=alt.X("city:N", sort="-y", title="City"),
            y=alt.Y("mean(sale_price):Q", title="Average Sale Price (USD)"),
            tooltip=[alt.Tooltip("city:N", title="City"), alt.Tooltip("mean(sale_price):Q", title="Avg Price")]
        )
        .properties(height=300)
    )
    st.altair_chart(bar_avg_price_city, use_container_width=True)
    st.code(f'''top_cities = df["city"].value_counts().nlargest({TOP_N_CITIES}).index
    alt.Chart(df[df["city"].isin(top_cities)]).mark_bar().encode(
        x=alt.X("city:N", sort="-y", title="City"),
        y=alt.Y("mean(sale_price):Q", title="Average Sale Price (USD)"),
        tooltip=[alt.Tooltip("city:N", title="City"), alt.Tooltip("mean(sale_price):Q", title="Avg Price")]
    ).properties(height=300)''', language="python")

    # 7) Scatter: size vs sale price
    st.subheader("Size vs Sale Price")
    scatter_size_price = (
        alt.Chart(df.dropna(subset=["size", "sale_price"]))
        .mark_circle(opacity=0.6)
        .encode(
            x=alt.X("size:Q", title="Size (sqft)"),
            y=alt.Y("sale_price:Q", title="Sale Price (USD)"),
            tooltip=["address:N", "city:N", "bds:Q", "bths:Q", alt.Tooltip("ppsf:Q", title="Price/Sqft")]
        )
        .properties(height=320)
    )
    st.altair_chart(scatter_size_price, use_container_width=True)
    st.code('''alt.Chart(df.dropna(subset=["size", "sale_price"])).mark_circle(opacity=0.6).encode(
        x=alt.X("size:Q", title="Size (sqft)"),
        y=alt.Y("sale_price:Q", title="Sale Price (USD)"),
        tooltip=["address:N", "city:N", "bds:Q", "bths:Q", alt.Tooltip("ppsf:Q", title="Price/Sqft")]
    ).properties(height=320)''', language="python")

    # 8) Scatter: days on market vs discount
    st.subheader("Days on Market vs Discount from List")
    scatter_cdom_disc = (
        alt.Chart(df.dropna(subset=["CDOM", "discount_pct"]))
        .mark_circle(opacity=0.6)
        .encode(
            x=alt.X("CDOM:Q", title="Cumulative Days on Market"),
            y=alt.Y("discount_pct:Q", title="Discount from List (fraction)"),
            tooltip=["address:N", "city:N", alt.Tooltip("list_price:Q", title="List"), alt.Tooltip("sale_price:Q", title="Sale")]
        )
        .properties(height=320)
    )
    st.altair_chart(scatter_cdom_disc, use_container_width=True)
    st.code('''alt.Chart(df.dropna(subset=["CDOM", "discount_pct"])).mark_circle(opacity=0.6).encode(
        x=alt.X("CDOM:Q", title="Cumulative Days on Market"),
        y=alt.Y("discount_pct:Q", title="Discount from List (fraction)"),
        tooltip=["address:N", "city:N", alt.Tooltip("list_price:Q", title="List"), alt.Tooltip("sale_price:Q", title="Sale")]
    ).properties(height=320)''', language="python")

    # 9) Histogram: sale price
    st.subheader("Sale Price Distribution")
    hist_price = (
        alt.Chart(df.dropna(subset=["sale_price"]))
        .mark_bar()
        .encode(
            x=alt.X("sale_price:Q", bin=alt.Bin(maxbins=40), title="Sale Price (USD)"),
            y=alt.Y("count()", title="Count"),
            tooltip=[alt.Tooltip("count()", title="Count")]
        )
        .properties(height=280)
    )
    st.altair_chart(hist_price, use_container_width=True)
    st.code('''alt.Chart(df.dropna(subset=["sale_price"])).mark_bar().encode(
        x=alt.X("sale_price:Q", bin=alt.Bin(maxbins=40), title="Sale Price (USD)"),
        y=alt.Y("count()", title="Count"),
        tooltip=[alt.Tooltip("count()", title="Count")]
    ).properties(height=280)''', language="python")


    # 10) Histogram: ROI
    st.subheader("ROI Distribution")
    hist_roi = (
        alt.Chart(df.dropna(subset=["roi_pct"]))
        .mark_bar()
        .encode(
            x=alt.X("roi_pct:Q", bin=alt.Bin(maxbins=40), title="ROI (fraction)"),
            y=alt.Y("count()", title="Count"),
            tooltip=[alt.Tooltip("count()", title="Count")]
        )
        .properties(height=280)
    )
    st.altair_chart(hist_roi, use_container_width=True)
    st.code('''alt.Chart(df.dropna(subset=["roi_pct"])).mark_bar().encode(
        x=alt.X("roi_pct:Q", bin=alt.Bin(maxbins=40), title="ROI (fraction)"),
        y=alt.Y("count()", title="Count"),
        tooltip=[alt.Tooltip("count()", title="Count")]
    ).properties(height=280)''', language="python")

    # 11) Box plot: sale price by city
    st.subheader(f"Sale Price by City (Top {TOP_N_CITIES}) — Box Plot")

    # Ensure df_top_cities exists
    if "df_top_cities" not in locals():
        TOP_N_CITIES = 12
        top_cities = df["city"].value_counts().nlargest(TOP_N_CITIES).index
        df_top_cities = df[df["city"].isin(top_cities)]

    # Sort cities by median sale_price in pandas, then pass the explicit order to Altair
    _order_city_by_median = (
        df_top_cities.groupby("city")["sale_price"]
        .median()
        .sort_values(ascending=False)
        .index.tolist()
    )

    box_price_city = (
        alt.Chart(df_top_cities)
        .mark_boxplot()
        .encode(
            x=alt.X("city:N", sort=_order_city_by_median, title="City"),
            y=alt.Y("sale_price:Q", title="Sale Price (USD)"),
            tooltip=[alt.Tooltip("city:N", title="City")]
        )
        .properties(height=320)
    )
    st.altair_chart(box_price_city, use_container_width=True)
    st.code(
        '''# Sort cities by median sale_price, then use that order in the x-encoding
    _order_city_by_median = (
        df_top_cities.groupby("city")["sale_price"]
        .median()
        .sort_values(ascending=False)
        .index.tolist()
    )

    alt.Chart(df_top_cities).mark_boxplot().encode(
        x=alt.X("city:N", sort=_order_city_by_median, title="City"),
        y=alt.Y("sale_price:Q", title="Sale Price (USD)")
    ).properties(height=320)''',
        language="python",
    )

    # 12) Heatmap: beds × baths, median sale price
    st.subheader("Beds × Baths — Median Sale Price")
    heat_beds_baths = (
        alt.Chart(df.dropna(subset=["bds", "bths", "sale_price"]))
        .mark_rect()
        .encode(
            x=alt.X("bds:O", title="Bedrooms"),
            y=alt.Y("bths:O", title="Bathrooms"),
            color=alt.Color("median(sale_price):Q", title="Median Price (USD)"),
            tooltip=[alt.Tooltip("bds:O", title="Bed"), alt.Tooltip("bths:O", title="Bath"), alt.Tooltip("median(sale_price):Q", title="Median Price")]
        )
        .properties(height=300)
    )
    st.altair_chart(heat_beds_baths, use_container_width=True)
    st.code('''alt.Chart(df.dropna(subset=["bds", "bths", "sale_price"])).mark_rect().encode(
        x=alt.X("bds:O", title="Bedrooms"),
        y=alt.Y("bths:O", title="Bathrooms"),
        color=alt.Color("median(sale_price):Q", title="Median Price (USD)"),
        tooltip=[alt.Tooltip("bds:O", title="Bed"), alt.Tooltip("bths:O", title="Bath"), alt.Tooltip("median(sale_price):Q", title="Median Price")]
    ).properties(height=300)''', language="python")


    # 13)Streamlit native Map 
    st.subheader("Locations")
    st.markdown("""
        This map is achieved using `st.map`. Using Streamlit’s native map (based on pydeck/deck.gl) gives us a quick basemap with pan/zoom out of the box. 
        Altair can plot points, but it doesn’t fetch map tiles, you’d have to bring your own.
    """)
    _geo = df.dropna(subset=["latitude", "longitude"])[["latitude", "longitude"]]
    st.map(_geo, latitude="latitude", longitude="longitude", zoom=10, use_container_width=True)

    st.code(
        """_geo = df.dropna(subset=["latitude", "longitude"])[["latitude", "longitude"]]
        st.map(_geo, latitude="latitude", longitude="longitude", zoom=10, use_container_width=True)""",
        language="python",
    )

    # --- Pie chart: share of flips by bedrooms ---
    # Assumes `df` and `alt` are available; `bds` is the bedrooms column.

    base = (
    alt.Chart(df)
    .transform_aggregate(count='count()', groupby=['bds'])
    .transform_joinaggregate(total='sum(count)')
    .transform_calculate(pct='datum.count / datum.total')
    )

    pie = base.mark_arc(outerRadius=120).encode(
        theta=alt.Theta('count:Q', stack=True),
        color=alt.Color('bds:N', title='Bedrooms'),
        tooltip=[
            alt.Tooltip('bds:N', title='Bedrooms'),
            alt.Tooltip('count:Q', title='Flips'),
            alt.Tooltip('pct:Q', title='Share', format='.1%')
        ]
    ).properties(height=340, title='Share of flips by bedrooms')

    label_min = 0.03  # hide labels under 3%

    labels = (
        base
        .transform_filter(alt.datum.pct >= label_min)
        .mark_text(radius=145, size=12)
        .encode(
            theta=alt.Theta('count:Q', stack=True),
            text=alt.Text('pct:Q', format='.0%'),
            detail='bds:N'
        )
    )

    st.altair_chart(pie + labels, use_container_width=True)


    # --- Stacked bar: monthly deal counts by city (Top 8) ---
    # Assumes `df` has columns `date` (datetime) and `city`.

    top_cities = df['city'].value_counts().nlargest(8).index
    df_top = df[df['city'].isin(top_cities)]

    stacked = (
        alt.Chart(df_top)
        .mark_bar()
        .encode(
            x=alt.X('yearmonth(date):T', title='Month'),
            y=alt.Y('count():Q', title='Deals'),
            color=alt.Color('city:N', title='City', legend=alt.Legend(columns=2)),
            tooltip=[
                alt.Tooltip('yearmonth(date):T', title='Month'),
                alt.Tooltip('city:N', title='City'),
                alt.Tooltip('count():Q', title='Deals')
            ]
        )
        .properties(height=340, title='Monthly deals by city (Top 8)')
    )

    st.altair_chart(stacked, use_container_width=True)
