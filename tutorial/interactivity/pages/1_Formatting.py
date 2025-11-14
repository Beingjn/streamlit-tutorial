import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from datetime import datetime
from pathlib import Path

st.set_page_config(page_title="Lab 5 — Formatting", layout="wide")
st.title("Lab 5 — Formatting")

CSV_PATH = "sales_records.csv" 
METRIC = "sale_price"        
CATEGORY = "city"           
AGG = "mean"                

# Load data
@st.cache_data
def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Parse the specific fields we rely on
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df[METRIC] = pd.to_numeric(df[METRIC], errors="coerce")
    df[CATEGORY] = df[CATEGORY].astype(str)
    return df

if not Path(CSV_PATH).exists():
    st.error(f"CSV not found at '{CSV_PATH}'. Update CSV_PATH in the script.")
    st.stop()

raw = load_csv(CSV_PATH)

# Keep only the TOP 5 cities by record
TOP_N = 5
top_cities = raw[CATEGORY].value_counts().nlargest(TOP_N).index
raw = raw[raw[CATEGORY].isin(top_cities)].copy()

st.subheader("Data preview")
st.caption("Note: Only the top 5 cities by record count are included in these graphs.")
st.dataframe(raw.head(20), use_container_width=True)

# Prepare long-form data for time series
work = raw.dropna(subset=["date", METRIC])[["date", CATEGORY, METRIC]].copy()
work["month"] = work["date"].dt.to_period("M").dt.to_timestamp()
df = (
    work.groupby(["month", CATEGORY])[METRIC]
    .agg(AGG)
    .reset_index()
    .rename(columns={"month": "date", CATEGORY: "category", METRIC: "value"})
)

# Dynamic formats for currency
is_currency = True
y_axis_format = "$,.0f"
tooltip_format = "$,.2f"
y_title = "Sale Price (mean)"

# Base chart helper
def base_chart(data: pd.DataFrame):
    return (
        alt.Chart(data)
        .mark_line(point=True)
        .encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("value:Q", title=y_title),
            color=alt.Color("category:N", title="City"),
            tooltip=[
                alt.Tooltip("date:T", title="Date", format="%b %Y"),
                alt.Tooltip("category:N", title="City"),
                alt.Tooltip("value:Q", title=y_title, format=tooltip_format),
            ],
        )
    )

st.subheader("Altair field type shorthand (what is :Q / :T / :N / :O?)")
st.markdown(
        "- `:Q` **Quantitative** (numbers, continuous) — e.g., `value:Q`  \n"
        "- `:T` **Temporal** (dates/times) — e.g., `date:T`  \n"
        "- `:N` **Nominal** (unordered categories) — e.g., `category:N`  \n"
        "- `:O` **Ordinal** (ordered categories) — e.g., `stage:O`  \n"
        "Altair can infer types, but be explicit when numbers are actually categories, or when dates are strings."
    )

# 1) Titles & Axis Labels
chart_1 = base_chart(df).properties(
    title=f"{y_title} by City (monthly)"
)
st.altair_chart(chart_1, use_container_width=True)

st.code(
    f'''
chart = (
    alt.Chart(df)
    .mark_line(point=True)
    .encode(
        x=alt.X("date:T", title="Date"),
        y=alt.Y("value:Q", title="{y_title}"),
        color=alt.Color("category:N", title="City"),
    )
    .properties(title="{y_title} by City (monthly)")
)
st.altair_chart(chart, use_container_width=True)
''',
    language="python",
)

st.divider()

# 2) Number & Date Formats
chart_2 = (
    alt.Chart(df)
    .mark_line(point=True)
    .encode(
        x=alt.X("date:T", title="Month", axis=alt.Axis(format="%b %Y")),
        y=alt.Y("value:Q", title=y_title, axis=alt.Axis(format=y_axis_format)),
        color=alt.Color("category:N", title="City"),
        tooltip=[
            alt.Tooltip("date:T", title="Month", format="%b %Y"),
            alt.Tooltip("category:N", title="City"),
            alt.Tooltip("value:Q", title=y_title, format=tooltip_format),
        ],
    )
    .properties(title="Formatted ticks & tooltips")
)
st.altair_chart(chart_2, use_container_width=True)

st.code(
    f'''
chart = (
    alt.Chart(df)
    .mark_line(point=True)
    .encode(
        x=alt.X("date:T", title="Month", axis=alt.Axis(format="%b %Y")),
        y=alt.Y("value:Q", title="{y_title}", axis=alt.Axis(format="{y_axis_format}")),
        tooltip=[
            alt.Tooltip("date:T", title="Month", format="%b %Y"),
            alt.Tooltip("value:Q", title="{y_title}", format="{tooltip_format}"),
        ],
    )
    .properties(title="Formatted ticks & tooltips")
)
''',
    language="python",
)

st.divider()

# 3) Scales (domain, zero, log)
y_min = float(df["value"].min())
y_max = float(df["value"].max())
y_domain = [y_min * 0.9, y_max * 1.05]

chart_3a = (
    base_chart(df)
    .encode(y=alt.Y("value:Q", title=y_title, scale=alt.Scale(domain=y_domain, zero=False)))
    .properties(title="Custom Y domain (no zero)")
)
st.altair_chart(chart_3a, use_container_width=True)

# Log example
chart_3b = (
    base_chart(df)
    .encode(y=alt.Y("value:Q", title=f"{y_title} (log)", scale=alt.Scale(type="log", base=10)))
    .properties(title="Log scale (base 10)")
)
st.altair_chart(chart_3b, use_container_width=True)

st.code(
    '''
# Domain & zero
y_domain = [df["value"].min() * 0.9, df["value"].max() * 1.05]
chart = base_chart(df).encode(
    y=alt.Y("value:Q", scale=alt.Scale(domain=y_domain, zero=False))
)

# Log scale (values must be > 0)
chart_log = base_chart(df).encode(
    y=alt.Y("value:Q", scale=alt.Scale(type="log", base=10))
)
''',
    language="python",
)

st.divider()

# 4) Color & Legend
chart_4 = (
    base_chart(df)
    .encode(
        color=alt.Color(
            "category:N",
            title="City",
            scale=alt.Scale(scheme="tableau10"),
            legend=alt.Legend(orient="bottom", direction="horizontal"),
        )
    )
    .properties(title="Legend at bottom + palette")
)
st.altair_chart(chart_4, use_container_width=True)

st.code(
    '''
chart = base_chart(df).encode(
    color=alt.Color(
        "category:N",
        title="City",
        scale=alt.Scale(scheme="tableau10"),
        legend=alt.Legend(orient="bottom", direction="horizontal"),
    )
)
''',
    language="python",
)

st.divider()


# 5) Annotations (reference lines & bands)
# Horizontal rule at median of the plotted values
target = float(df["value"].median())
h_ref = alt.Chart(pd.DataFrame({"y": [target]})).mark_rule(strokeDash=[4, 4]).encode(y="y:Q")

# Date band
band_df = pd.DataFrame({"start": [pd.Timestamp("2023-04-01")], "end": [pd.Timestamp("2023-06-01")]})
band = alt.Chart(band_df).mark_rect(opacity=0.08).encode(x="start:T", x2="end:T")

chart_5 = (band + base_chart(df) + h_ref).properties(
    title=f"Median target line at {target:,.0f} & recent period highlighted"
)
st.altair_chart(chart_5, use_container_width=True)

st.code(
    '''
# Horizontal rule at median
target = float(df["value"].median())
h_ref = alt.Chart(pd.DataFrame({"y": [target]})).mark_rule(strokeDash=[4,4]).encode(y="y:Q")

# Date band
band_df = pd.DataFrame({"start": [pd.Timestamp("2023-04-01")], "end": [pd.Timestamp("2023-06-01")]})
band = alt.Chart(band_df).mark_rect(opacity=0.08).encode(x="start:T", x2="end:T")

chart = band + base_chart(df) + h_ref
''',
    language="python",
)
