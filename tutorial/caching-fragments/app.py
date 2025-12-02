import time
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection
import altair as alt

st.set_page_config(page_title="Caching and Fragments", layout="centered")

# Counters
if "app_runs" not in st.session_state:
    st.session_state.app_runs = 0
if "fragment_runs" not in st.session_state:
    st.session_state.fragment_runs = 0

st.session_state.app_runs += 1

st.title("Caching and Fragments")


st.markdown(
    """
This app showcases caching and fragments, two tools that help keep your Streamlit apps fast and responsive as they grow more complex.
"""
)

st.caption(f"Full app runs this session: **{st.session_state.app_runs}**")

# Load data
def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    numeric_cols = [
        "beds",
        "baths",
        "area",
        "price",
        "lotArea",
        "year",
        "zestimate",
        "taxAssessedValue",
        "timeOnZillow",
        "price/SF",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "sold_date" in df.columns:
        df["sold_date"] = pd.to_datetime(df["sold_date"], errors="coerce")

    if "sold_date" in df.columns:
        df["sold_year_month"] = (
            df["sold_date"].dt.to_period("M").dt.to_timestamp()
        )

    return df


with st.spinner("Loading data from Google Sheets via st.connection(...)"):
    conn = st.connection("gsheets", type=GSheetsConnection)
    raw_df = conn.read()
    df = preprocess_data(raw_df)

all_cities = df["city"].dropna().unique().tolist()
n_cities = len(all_cities)

st.subheader("Data preview")
st.dataframe(df.head(20), use_container_width=True)

st.header("Caching")

st.markdown(
    """
**What problem does this solve?**  
Every interaction reruns your script. If you repeatedly read files or do heavy transforms, the app feels slow.  
Data caching stores the result so identical calls can be served from memory instead of recomputing.

**Use cases**  
Caching is typically used for expensive but repeatable work where the inputs don’t change often: 
loading data, running heavy aggregations, or doing complex transformations on a DataFrame.

To cache a function in Streamlit, simply decorate it with one of two decorators (st.cache_data or st.cache_resource):
    """
)

st.code(
    """@st.cache_data
def expensive_function(param1, param2):
    return …
    """
        , language= "python",)


st.info(
    """`st.cache_data` is for functions that return data: loading a DataFrame, transforming arrays, calling APIs, or anything that 
gives you a serializable result (numbers, strings, lists, DataFrames, etc.). 

`st.cache_resource` is for long-lived, non-serializable resources like ML models or database connections that you want to create 
once and reuse. It returns the same object each time, shared across reruns and sessions, so changes to it affect the single cached instance.
"""
)
st.markdown(
    """
We've been useing `st.connect` to connect to data sources in the previous examples. When you use `st.connection`, Streamlit is already 
caching that data for you behind the scenes.

For more details about caching, please check out Streamlit Docs: https://docs.streamlit.io/develop/concepts/architecture/caching
"""
)
# Controls
st.subheader("Caching Demo")
st.markdown(
    """
In this demo, we have an big aggregation function that summarizes the data, and we can choose to either
 cache it or run it fresh on every rerun. Switch between caching and non-caching modes and play with the 
 chart controls below and see how quickly the app responds in each mode.
"""
)

cache_mode = st.radio(
    "Aggregation mode",
    ["Use caching", "No caching"],
    horizontal=True,
)

top_n_cities = st.slider(
    "Number of top cities in charts",
    min_value=3,
    max_value=min(30, max(3, n_cities)),
    value=min(10, max(3, n_cities)),
    help=(
        "Top cities are chosen by total number of sales. "
        "This only filters the *visualizations*, not the cached aggregations."
    ),
)

st.caption(
    "All heavy aggregations are computed once for the whole dataset. "
    "Caching controls whether that pipeline is reused or recomputed. "
    "The slider above just slices those precomputed results."
)


# Aggregation pipeline
MIN_CITY_SALES = 10 

def _compute_aggregations() -> dict:
    data = df.copy()

    required_cols = ["city", "price", "zpid"]
    if "sold_year_month" in data.columns:
        required_cols.append("sold_year_month")

    data = data.dropna(subset=[c for c in required_cols if c in data.columns])

    if data.empty:
        return {
            "filtered_data": data,
            "city_summary": pd.DataFrame(),
            "monthly_stats": pd.DataFrame(),
            "price_index_norm": pd.DataFrame(),
            "correlation": pd.DataFrame(),
        }

    # City-level summary on full data
    city_summary_all = (
        data.groupby("city", dropna=False)
        .agg(
            total_sales=("zpid", "count"),
            median_price=("price", "median"),
            mean_price=("price", "mean"),
            median_area=("area", "median"),
            avg_beds=("beds", "mean"),
            avg_baths=("baths", "mean"),
        )
        .reset_index()
    )

    big_cities = city_summary_all[
        city_summary_all["total_sales"] >= MIN_CITY_SALES
    ]["city"]

    data = data[data["city"].isin(big_cities)]

    if data.empty:
        return {
            "filtered_data": data,
            "city_summary": city_summary_all[0:0],
            "monthly_stats": pd.DataFrame(),
            "price_index_norm": pd.DataFrame(),
            "correlation": pd.DataFrame(),
        }

    # Recompute city_summary on filtered data
    city_summary = (
        data.groupby("city", dropna=False)
        .agg(
            total_sales=("zpid", "count"),
            median_price=("price", "median"),
            mean_price=("price", "mean"),
            median_area=("area", "median"),
            avg_beds=("beds", "mean"),
            avg_baths=("baths", "mean"),
        )
        .reset_index()
    )

    # Monthly stats per city
    if "sold_year_month" not in data.columns:
        monthly_stats = pd.DataFrame()
        price_index_norm = pd.DataFrame()
        corr = pd.DataFrame()
    else:
        # Multi-agg groupby
        agg_dict = {
            "zpid": "count",
            "price": ["median", "mean"],
        }
        if "price/SF" in data.columns:
            agg_dict["price/SF"] = ["median", "mean"]

        grouped = (
            data.groupby(["city", "sold_year_month"])
            .agg(agg_dict)
        )

        # Flatten MultiIndex columns
        grouped.columns = [
            "_".join([c for c in col if c]) for col in grouped.columns.to_flat_index()
        ]
        grouped = grouped.rename(
            columns={
                "zpid_count": "sales_count",
                "price_median": "median_price",
                "price_mean": "mean_price",
                "price/SF_median": "median_price_sf",
                "price/SF_mean": "mean_price_sf",
            }
        ).reset_index()

        # Quantiles for price
        q = (
            data.groupby(["city", "sold_year_month"])["price"]
            .quantile([0.25, 0.75])
            .unstack(level=-1)
            .rename(columns={0.25: "q25_price", 0.75: "q75_price"})
            .reset_index()
        )

        monthly_stats = grouped.merge(
            q, on=["city", "sold_year_month"], how="left"
        )

        # Rolling stats per city
        def add_rolling(g: pd.DataFrame) -> pd.DataFrame:
            g = g.sort_values("sold_year_month")
            g["median_price_6m"] = (
                g["median_price"]
                .rolling(window=6, min_periods=3)
                .median()
            )
            g["sales_6m"] = (
                g["sales_count"]
                .rolling(window=6, min_periods=3)
                .sum()
            )
            g["mom_change"] = g["median_price"].pct_change()
            return g

        monthly_stats = (
            monthly_stats.groupby("city", group_keys=False)
            .apply(add_rolling)
            .reset_index(drop=True)
        )

        # Price index
        price_index = monthly_stats.pivot_table(
            index="sold_year_month",
            columns="city",
            values="median_price",
        ).sort_index()

        def normalize_series(s: pd.Series) -> pd.Series:
            s = s.copy()
            if s.notna().any():
                first = s.dropna().iloc[0]
                if first != 0:
                    s = 100 * s / first
            return s

        price_index_norm = price_index.apply(normalize_series, axis=0)

        # City-to-city correlation of normalized price indices
        corr = price_index_norm.corr()

    return {
        "filtered_data": data,
        "city_summary": city_summary,
        "monthly_stats": monthly_stats,
        "price_index_norm": price_index_norm,
        "correlation": corr,
    }


@st.cache_data(show_spinner=False)
def get_aggregations_cached() -> dict:
    return _compute_aggregations()


def get_aggregations_nocache() -> dict:
    return _compute_aggregations()

# Run aggregations & measure time
if cache_mode.startswith("Use caching"):
    start = time.perf_counter()
    agg = get_aggregations_cached()
    elapsed = time.perf_counter() - start
    mode_label = "Cached"
else:
    start = time.perf_counter()
    agg = get_aggregations_nocache()
    elapsed = time.perf_counter() - start
    mode_label = "Non-cached"

filtered = agg["filtered_data"]
city_summary = agg["city_summary"]
monthly_stats = agg["monthly_stats"]
price_index_norm = agg["price_index_norm"]
corr = agg["correlation"]

col_info1, col_info2 = st.columns(2)
col_info1.markdown(f"**Mode:** {mode_label}")
col_info2.metric("Aggregation time (seconds)", f"{elapsed:.3f}")

# Visualizations
st.subheader("Top cities by total sales")

if not city_summary.empty:
    top_cities_list = (
        city_summary.sort_values("total_sales", ascending=False)
        .head(top_n_cities)["city"]
        .tolist()
    )

    top_city_summary = city_summary[
        city_summary["city"].isin(top_cities_list)
    ]

    bar_chart = (
        alt.Chart(top_city_summary)
        .mark_bar()
        .encode(
            x=alt.X("total_sales:Q", title="Total number of sales"),
            y=alt.Y("city:N", sort="-x", title="City"),
            tooltip=[
                "city",
                "total_sales",
                alt.Tooltip("median_price:Q", format=",.0f", title="Median price"),
                alt.Tooltip("mean_price:Q", format=",.0f", title="Mean price"),
                alt.Tooltip("median_area:Q", format=",.0f", title="Median area (sqft)"),
                alt.Tooltip("avg_beds:Q", format=".2f", title="Avg beds"),
                alt.Tooltip("avg_baths:Q", format=".2f", title="Avg baths"),
            ],
        )
    )
    st.altair_chart(bar_chart, use_container_width=True)
else:
    st.info(
        "No city-level data available after filtering out cities with fewer than "
        f"{MIN_CITY_SALES} records."
    )

st.subheader("Price index over time (normalized to 100 at first month)")

if not price_index_norm.empty and not city_summary.empty:
    top_cities_list = (
        city_summary.sort_values("total_sales", ascending=False)
        .head(top_n_cities)["city"]
        .tolist()
    )

    price_index_subset = price_index_norm[top_cities_list]
    price_index_long = price_index_subset.reset_index().melt(
        id_vars="sold_year_month",
        var_name="city",
        value_name="price_index",
    )

    index_chart = (
        alt.Chart(price_index_long)
        .mark_line()
        .encode(
            x=alt.X("sold_year_month:T", title="Sold month"),
            y=alt.Y("price_index:Q", title="Price index (first month = 100)"),
            color="city:N",
            tooltip=[
                "city",
                alt.Tooltip("sold_year_month:T", title="Month"),
                alt.Tooltip("price_index:Q", format=".1f", title="Index"),
            ],
        )
    )
    st.altair_chart(index_chart, use_container_width=True)
else:
    st.info("No time-series data available to build a price index.")

st.subheader("Within-city price distribution over time")

if not monthly_stats.empty and not city_summary.empty:
    focus_cities = (
        city_summary.sort_values("total_sales", ascending=False)["city"].tolist()
    )
    default_city = focus_cities[0] if focus_cities else None

    focus_city = st.selectbox(
        "Choose a city to inspect (monthly stats)",
        options=focus_cities,
        index=0 if default_city else 0,
    )

    city_ts = monthly_stats[monthly_stats["city"] == focus_city].dropna(
        subset=["sold_year_month"]
    )

    if not city_ts.empty:
        base = alt.Chart(city_ts).encode(
            x=alt.X("sold_year_month:T", title="Sold month")
        )

        band = base.mark_area(opacity=0.3).encode(
            y=alt.Y("q25_price:Q", title="Sale price (USD)"),
            y2="q75_price:Q",
            tooltip=[
                alt.Tooltip("sold_year_month:T", title="Month"),
                alt.Tooltip("q25_price:Q", format=",.0f", title="25th percentile"),
                alt.Tooltip("q75_price:Q", format=",.0f", title="75th percentile"),
            ],
        )

        median_line = base.mark_line().encode(
            y="median_price:Q",
            tooltip=[
                alt.Tooltip("sold_year_month:T", title="Month"),
                alt.Tooltip("median_price:Q", format=",.0f", title="Median price"),
            ],
        )

        rolling_line = base.mark_line(strokeDash=[4, 2]).encode(
            y="median_price_6m:Q",
            tooltip=[
                alt.Tooltip("sold_year_month:T", title="Month"),
                alt.Tooltip(
                    "median_price_6m:Q", format=",.0f", title="6-month median (rolling)"
                ),
            ],
        )

        st.altair_chart(band + median_line + rolling_line, use_container_width=True)
    else:
        st.info(f"No monthly data for {focus_city}.")
else:
    st.info("No monthly stats available to build the band chart.")

st.subheader("Correlation between city price indices")

if not corr.empty and not city_summary.empty:
    top_cities_list = (
        city_summary.sort_values("total_sales", ascending=False)
        .head(top_n_cities)["city"]
        .tolist()
    )

    corr_subset = corr.loc[top_cities_list, top_cities_list]

    corr_long = (
        corr_subset
        .rename_axis(index="city1", columns="city2")
        .stack()
        .rename("correlation")
        .reset_index()
    )

    heatmap = (
        alt.Chart(corr_long)
        .mark_rect()
        .encode(
            x=alt.X("city1:N", title="City"),
            y=alt.Y("city2:N", title="City"),
            color=alt.Color("correlation:Q", title="Correlation"),
            tooltip=[
                "city1",
                "city2",
                alt.Tooltip("correlation:Q", format=".2f", title="Correlation"),
            ],
        )
    )

    st.altair_chart(heatmap, use_container_width=True)
else:
    st.info("Not enough data to compute a correlation matrix.")

# Fragment
st.header("Fragments")
st.markdown(
    """
**What is Fragment?**  
`st.fragment` lets you wrap part of your app in a function so that only that part reruns when its widgets change, 
instead of rerunning the entire script. Widgets defined inside a fragment still trigger reruns, but those reruns are 
local to the fragment, leaving the rest of the app (and any heavy global work) untouched. This is separate from caching: 
caching controls *what* work is reused, fragments control where reruns happen.

**Use cases**
- Local drill-down panels that shouldn’t trigger full-page reruns.  
- Expensive, interactive sub-sections (tables, charts) that operate on already-cached data.  
- Side-by-side panels where one updates independently of the rest of the app.

Fragments on Streamlit Docs: https://docs.streamlit.io/develop/concepts/architecture/fragments
"""
)
st.subheader("Fragment Demo")
@st.fragment
def simple_city_fragment():
    st.session_state.fragment_runs += 1

    st.write(
        f"**Full app runs this session:** {st.session_state.app_runs}  \n"
        f"**Fragment runs this session:** {st.session_state.fragment_runs}"
    )

    if filtered.empty:
        st.info("No data available after global aggregations.")
        return

    city_options = sorted(filtered["city"].dropna().unique().tolist())
    city = st.selectbox(
        "Choose a city (fragment-local widget)",
        options=city_options,
    )

    city_rows = filtered[filtered["city"] == city].head(10)
    st.write("First 10 rows for this city (from globally cached data):")
    st.dataframe(city_rows)

simple_city_fragment()

st.markdown(
    """
To use fragment in Streamlit, decorate a function with st.fragment. Here's the pattern of the demo.

```python
def fragment_function():
    city = st.selectbox(
        "Choose a city (fragment-local widget)",
        sorted(df["city"].dropna().unique())
    )

    city_data = df[df["city"] == city]

    chart = (
        alt.Chart(city_data)
        .mark_line()
        .encode(
            x="sold_date:T",
            y="price:Q",
            tooltip=["sold_date:T", "price:Q"],
        )
    )

    st.altair_chart(chart, use_container_width=True)
"""
)
