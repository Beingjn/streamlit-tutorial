import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.set_page_config(page_title="Intro to Filters in Streamlit", layout="wide")

# Generate dataset
np.random.seed(0)
days = pd.date_range("2024-01-01", periods=180, freq="D")
cats = ["Alpha", "Beta", "Gamma"]
rows = []
for c in cats:
    base = 100 + np.linspace(0, 20, len(days))          
    noise = np.random.normal(0, 4, len(days)).cumsum()  
    vals = np.maximum(0, base + noise)
    rows.extend({"date": d, "category": c, "value": float(v)} for d, v in zip(days, vals))
df = pd.DataFrame(rows)

# Title & Overview
st.title("Intro to Filters in Streamlit")

st.markdown(
    """
This app shows how to add simple filters and use one boolean mask to update
multiple outputs at once.
"""
)

# How the filter is achieved
st.header("1) How filtering is achieved")
st.markdown(
    """
- Widgets in the sidebar collect the user's choices (category, date range, value range).
- On each change, Streamlit re-runs the script from top to bottom.
- We build one boolean mask based on the widget values.
- That mask filters the Dataframe, and we the filtered data for visualizations.
"""
)

# Example: plot + table with filters
st.header("2) Example")

st.markdown(
    """
Use the filters in the sidebar. Notice how both the table and the chart below update together,
because they’re fed by the same filtered DataFrame.
"""
)

# Sidebar controls
st.sidebar.header("Filters")

all_categories = sorted(df["category"].unique().tolist())
selected_cats = st.sidebar.multiselect(
    "Category",
    options=all_categories,
    default=all_categories,                # start with everything selected
    key="cats",
)

min_d, max_d = df["date"].min().date(), df["date"].max().date()
date_range = st.sidebar.date_input(
    "Date range",
    (min_d, max_d),
    min_value=min_d,
    max_value=max_d,
    key="date_rng",
)

vmin, vmax = float(df["value"].min()), float(df["value"].max())
low, high = st.sidebar.slider(
    "Value range",
    min_value=float(vmin),
    max_value=float(vmax),
    value=(float(vmin), float(vmax)),
    key="val_rng",
)

# Build the mask
mask = pd.Series(True, index=df.index)

# Category filter
if selected_cats:
    mask &= df["category"].isin(selected_cats)

# Date filter
gf = st.session_state.get("global_filters")
if isinstance(date_range, tuple):
    start_date, end_date = date_range
else:
    start_date = end_date = date_range
start_ts = pd.to_datetime(start_date)
end_ts = pd.to_datetime(end_date)
mask &= df["date"].between(start_ts, end_ts)

# Numeric range filter
mask &= df["value"].between(float(low), float(high))

filtered = df.loc[mask].copy()

# Empty state
if filtered.empty:
    st.info("No rows match the current filters. Try widening your selections.")
    st.stop()

# Outputs
c1, c2 = st.columns([2, 3])

with c1:
    st.subheader("Filtered table")
    st.dataframe(filtered, use_container_width=True, hide_index=True)
    st.caption(
        f"Rows: **{len(filtered):,}**  •  Categories: **{', '.join(sorted(map(str, filtered['category'].unique())))}**"
    )

with c2:
    st.subheader("Filtered chart")
    chart = (
        alt.Chart(filtered)
        .mark_line()
        .encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("value:Q", title="Value"),
            color=alt.Color("category:N", title="Category"),
            tooltip=["date:T", "category:N", "value:Q"],
        )
    )
    st.altair_chart(chart, use_container_width=True)

# Structure of this example filter
st.header("3) Structure of this example filter")
st.markdown(
    """
Below is the pattern of this filter. We gather widget values, build a mask step-by-step,
and apply it.  
First, we have input widgets to take user input. Here are the widgets used in this example.  
For more widgts, check Streamlit documentation: https://docs.streamlit.io/develop/api-reference/widgets
"""
)
st.code(
    """
# 1) Widgets for inputing values
# Category selection widget
selected_cats = st.sidebar.multiselect(
    "Category",
    options=all_categories,
    default=all_categories,                # start with everything selected
    key="cats",
)

# Date input widget
min_d, max_d = df["date"].min().date(), df["date"].max().date()
start_date, end_date = st.sidebar.date_input(
    "Date range",
    (min_d, max_d),
    min_value=min_d,
    max_value=max_d,
    key="date_rng",
)

# Value slider widget
vmin, vmax = float(df["value"].min()), float(df["value"].max())
low, high = st.sidebar.slider(
    "Value range",
    min_value=float(vmin),
    max_value=float(vmax),
    value=(float(vmin), float(vmax)),
    key="val_rng",
)
    """,
    language="python",
)

st.markdown(
    """
Then, we bulid filtered mask and apply it:
"""
)
st.code(
    """
# 2) Start with a mask that is True for every row
mask = pd.Series(True, index=df.index)

# 3) Narrow the mask step-by-step
mask &= df["category"].isin(selected_cats)
mask &= df["date"].between(start_date, end_date)
mask &= df["value"].between(low, high)

# 4) Apply once, reuse everywhere
filtered = df.loc[mask]
    """,
    language="python",
)

st.markdown(
    """
We can now use the filtered dataframe for visualizations and further use.
"""
)
st.code(
    """
# Line chart used in this example
chart = (
    alt.Chart(filtered)
    .mark_line()
    .encode(
        x=alt.X("date:T", title="Date"),
        y=alt.Y("value:Q", title="Value"),
        color=alt.Color("category:N", title="Category"),
        tooltip=["date:T", "category:N", "value:Q"],
    )
)
st.altair_chart(chart, use_container_width=True)
    """,
    language="python",
)

