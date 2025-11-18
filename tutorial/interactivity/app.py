import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from pathlib import Path
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Interactivity & Linked Charts", layout="wide")
st.title("Interactivity & Linked Charts")

st.markdown(
    """
    This app shows examples of interactive charts in Altair, including linked views, cross filtering,
    legend-based filtering, and page-wide shared state between charts.
    
    For more examples of interactive charts, please check out the Interactive Charts section under Altair Example Gallery: https://altair-viz.github.io/gallery/index.html
    """
)

         
CATEGORY = "city"                                  
METRIC = st.sidebar.selectbox("Metric", ["sale_price", "profit"], index=0)
AGG = st.sidebar.selectbox("Aggregation", ["mean", "median"], index=0)
TOP_N_CITIES = st.sidebar.slider("Top N", 4, 15, 7)

# Load data
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

# Keep only the top categories by record
df_time = df.dropna(subset=["date"])
top_cities = df["city"].value_counts().nlargest(TOP_N_CITIES).index
df_top_cities = df[df["city"].isin(top_cities)]

df_monthly = df_top_cities.dropna(subset=["date", METRIC])[["date", CATEGORY, METRIC]].copy()
df_monthly["month"] = df_monthly["date"].dt.to_period("M").dt.to_timestamp()
df_monthly = (
    df_monthly.groupby(["month", CATEGORY])[METRIC]
    .agg(AGG)
    .reset_index()
    .rename(columns={"month": "date", CATEGORY: "category", METRIC: "value"})
)

METRIC_LABEL = METRIC.replace("_", " ").title()
AGG_LABEL = AGG.title()
CAT_LABEL = CATEGORY.replace("_", " ").title()

st.subheader("Data preview")
st.caption(
    f"This app uses the same real estate dataset, restricted to the top {TOP_N_CITIES} cities by record count."
)
st.dataframe(df_top_cities.head(20), use_container_width=True)

st.markdown(
    """
### How interactivity works in Altair

In Altair, interactivity is driven by parameters (including selections). `add_params()` attaches a parameter to a chart so user actions 
(clicks, brushes, sliders, etc.) can update that parameter, while `transform_filter()` uses the current value of that parameter to filter the chart’s data.

A common pattern is:
1. Define a selection/parameter.
2. Attach it to a “driver” chart with `add_params` so interaction updates it.
3. Use `transform_filter` with the same parameter on one or more “linked” charts so they respond to that interaction.
4. Use a composition operator to combine those charts into a single interactive visualization.
"""
)

st.code(
    """
# Define a selection / parameter
sel = alt.selection_point(fields=["category"])  # or selection_interval(), or alt.param(...)

# Attach it to a chart so user interaction updates `sel`
driver_chart = (
    alt.Chart(data)
    .mark_bar()
    .encode(
        x="category:N",
        y="value:Q",
        # Optional: use `sel` in encodings (e.g. color) to highlight selected values
    )
    .add_params(sel)  # enable interaction on this chart to update the selection
)

# Use the same parameter to filter another chart’s data
linked_chart = (
    alt.Chart(data)
    .mark_line()
    .encode(
        x="date:T",
        y="value:Q",
        color="category:N",
    )
    .transform_filter(sel)  # keep only rows that match the current selection
)

# Compose charts so they share the same interactive spec
combined = driver_chart & linked_chart  # or driver_chart | linked_chart

st.altair_chart(combined, use_container_width=True)
""",
    language="python",
)



# 1) Linked line + bar horizontal concat
st.header("1) One-way linked charts")
st.markdown(
    """
This example uses one chart to filter another.  

`add_params()` on the first chart attaches a selection to it, so user interactions on that chart update that selection.  
`transform_filter()` on the second chart uses the same selection to filter its data, so it only shows rows that match the current selection.
    """
)

brush1 = alt.selection_interval(name="brush1")

lines1 = (
    alt.Chart(df_monthly, title=f"{METRIC_LABEL} over Time by {CAT_LABEL} — brush to filter")
    .mark_line(point=True)
    .encode(
        x=alt.X("date:T", title="Month"),
        y=alt.Y("value:Q", title=f"{AGG_LABEL} {METRIC_LABEL}"),
        color=alt.condition(brush1, "category:N", alt.value("lightgray")),
        tooltip=[alt.Tooltip("date:T", title="Month"), "category:N", alt.Tooltip("value:Q", title=f"{AGG_LABEL} {METRIC_LABEL}")],
    )
    .add_params(brush1)
)

bars1 = (
    alt.Chart(df_monthly, title=f"{AGG_LABEL} {METRIC_LABEL} by {CAT_LABEL} (filtered by brush)")
    .mark_bar()
    .encode(
        x=alt.X("category:N", title=CAT_LABEL),
        y=alt.Y("mean(value):Q", title=f"{AGG_LABEL} {METRIC_LABEL}"),
        color="category:N",
        tooltip=["category:N", alt.Tooltip("mean(value):Q", title=f"{AGG_LABEL} {METRIC_LABEL}")],
    )
    .transform_filter(brush1)
)

st.altair_chart((lines1 | bars1).resolve_scale(color="independent"), use_container_width=True)

st.code(
    f'''
brush1 = alt.selection_interval(name="brush1")

lines1 = (
    alt.Chart(df_monthly, title=f"{METRIC_LABEL} over Time by {CAT_LABEL} — brush to filter")
    .mark_line(point=True)
    .encode(
        x=alt.X("date:T", title="Month"),
        y=alt.Y("value:Q", title=f"{AGG_LABEL} {METRIC_LABEL}"),
        color=alt.condition(brush1, "category:N", alt.value("lightgray")),
        tooltip=[alt.Tooltip("date:T", title="Month"), "category:N", alt.Tooltip("value:Q", title=f"{AGG_LABEL} {METRIC_LABEL}")],
    )
    .add_params(brush1)
)

bars1 = (
    alt.Chart(df_monthly, title=f"{AGG_LABEL} {METRIC_LABEL} by {CAT_LABEL} (filtered by brush)")
    .mark_bar()
    .encode(
        x=alt.X("category:N", title=CAT_LABEL),
        y=alt.Y("mean(value):Q", title=f"{AGG_LABEL} {METRIC_LABEL}"),
        color="category:N",
        tooltip=["category:N", alt.Tooltip("mean(value):Q", title=f"{AGG_LABEL} {METRIC_LABEL}")],
    )
    .transform_filter(brush1)
)

st.altair_chart((lines1 | bars1).resolve_scale(color="independent"), use_container_width=True)
''',
    language="python",
)

# 2) Cross filltering bar + line vertical concat
st.header("2) Cross-filtering charts")

st.markdown(
    """
Here both charts control one interaction and respond to the other.  

Each chart calls `add_params()` with its own selection: the bars own the “clicked category” state, 
and the lines own the “brushed time range” state.  

Each chart then uses `transform_filter()` with the other chart’s selection: bars are filtered by the brush, 
and lines are filtered by the clicked category.  
"""
)

click_cat = alt.selection_point(name="cat_click", fields=["category"], on="click", clear="dblclick")
brush2 = alt.selection_interval(name="brush2")

bars2 = (
    alt.Chart(df_monthly, title=f"{AGG_LABEL} {METRIC_LABEL} by {CAT_LABEL} — click to filter")
    .mark_bar()
    .encode(
        y=alt.Y("category:N", sort="-x", title=CAT_LABEL),
        x=alt.X("mean(value):Q", title=f"{AGG_LABEL} {METRIC_LABEL}"),
        color=alt.condition(click_cat, "category:N", alt.value("lightgray")),
        tooltip=["category:N", alt.Tooltip("mean(value):Q", title=f"{AGG_LABEL} {METRIC_LABEL}")],
    )
    .add_params(click_cat)
    .transform_filter(brush2)  # brush on the lines to these bars
    .properties(height=160)
)

lines2 = (
    alt.Chart(df_monthly, title=f"{AGG_LABEL} {METRIC_LABEL} over Time — brush to filter")
    .mark_line(point=True)
    .encode(
        x=alt.X("date:T", title="Month"),
        y=alt.Y("value:Q", title=f"{AGG_LABEL} {METRIC_LABEL}"),
        color="category:N",
        tooltip=[alt.Tooltip("date:T", title="Month"), "category:N", alt.Tooltip("value:Q", title=f"{AGG_LABEL} {METRIC_LABEL}")],
    )
    .add_params(brush2) 
    .transform_filter(click_cat)    # click on the bars to filter the lines
)

st.altair_chart((bars2 & lines2).resolve_scale(color="independent"), use_container_width=True)

st.code(
    f'''
click_cat = alt.selection_point(name="cat_click", fields=["category"], on="click", clear="dblclick")
brush2 = alt.selection_interval(name="brush2")

bars2 = (
    alt.Chart(df_monthly, title=f"{AGG_LABEL} {METRIC_LABEL} by {CAT_LABEL} — click to filter")
    .mark_bar()
    .encode(...)
    .add_params(click_cat)
    .transform_filter(brush2)  # brush on the lines constrains the bars
    .properties(height=160)
)

lines2 = (
    alt.Chart(df_monthly, title=f"{AGG_LABEL} {METRIC_LABEL} over Time — brushed; filtered by bar click")
    .mark_line(point=True)
    .encode(...)
    .add_params(brush2)
    .transform_filter(click_cat) # click on the bars constrains the lines
)

st.altair_chart((bars2 & lines2).resolve_scale(color="independent"), use_container_width=True)
''',
    language="python",
)

st.info(
    """
    **Altair composition operators**  
    Notice how the charts in the fist example are side by side and the second stacked? This is achieved using different composition operators.
    * `|` — **Horizontal concat** (charts side-by-side)
    * `&` — **Vertical concat** (charts stacked)
    * `+` — **Layering** (treat multiple marks as one chart on the same axes)
    """
)

st.markdown(
    """
You can extend the same idea to more than two charts: reuse the same parameters across multiple views, 
attach them with `add_params` where interactions should update them, and apply `transform_filter` in each chart that should respond. 
"""
)



# 3) Legend-click filtering
st.header("3) Legend filtering")
st.markdown(
    """
    In earlier tutorials, most of our filtering was done before the charts: Streamlit widgets updated a pandas Dataframe, and then we passed that filtered data into Altair.  

    In this section, we look at how some of that interaction can live entirely inside Altair instead. By binding a selection to the legend, 
    clicking legend entries updates an Altair parameter that the chart can use to highlight or filter categories, without needing extra Streamlit widgets or DataFrame logic.
    """
)

legend = alt.selection_point(name="legend", fields=["category"], bind="legend")

lines3 = (
    alt.Chart(df_monthly, title=f"{AGG_LABEL} {METRIC_LABEL} over Time by {CAT_LABEL} — click legend to filter")
    .mark_line(point=True)
    .encode(
        x=alt.X("date:T", title="Month"),
        y=alt.Y("value:Q", title=f"{AGG_LABEL} {METRIC_LABEL}"),
        color="category:N",
        tooltip=[alt.Tooltip("date:T", title="Month"), "category:N", alt.Tooltip("value:Q", title=f"{AGG_LABEL} {METRIC_LABEL}")],
    )
    .add_params(legend)
    .transform_filter(legend)
)

st.altair_chart(lines3, use_container_width=True)

st.code(
    f'''
legend = alt.selection_point(name="legend", fields=["category"], bind="legend")

lines3 = (
    alt.Chart(df_monthly, title=f"{AGG_LABEL} {METRIC_LABEL} over Time by {CAT_LABEL} — legend click to filter")
    .mark_line(point=True)
    .encode(
        x=alt.X("date:T", title="Month"),
        y=alt.Y("value:Q", title=f"{AGG_LABEL} {METRIC_LABEL}"),
        color="category:N",
        tooltip=[alt.Tooltip("date:T", title="Month"), "category:N", alt.Tooltip("value:Q", title=f"{AGG_LABEL} {METRIC_LABEL}")],
    )
    .add_params(legend)
    .transform_filter(legend)
)

st.altair_chart(lines3, use_container_width=True)
''',
    language="python",
)


# 4) Page-wide linking
st.header("4) Page-wide linking")
st.markdown(
    """
    In this section, instead of using `add_params` + `transform_filter` + composition operators to connect charts, we:

    1. Render a chart that exposes a named selection parameter.
    2. Let Streamlit capture that selection via `on_select="rerun"`.
    3. Build a filtered Dataframe based on the current selection.
    4. Render follow-up charts (and any other content) elsewhere on the page, all using this filtered DataFrame.

    This pattern keeps charts connected while allowing content in between.
    """
)


sel = alt.selection_point(name="cat", fields=["category"], on="click", clear="dblclick")

bars4 = (
    alt.Chart(df_monthly, title=f"Select {CAT_LABEL}")
    .mark_bar()
    .encode(
        y=alt.Y("category:N", sort="-x", title=CAT_LABEL),
        x=alt.X("count()", title="Monthly Records"),
        color=alt.condition(sel, "category:N", alt.value("lightgray")),
        tooltip=["category:N", "count()"],
    )
    .add_params(sel)
    .properties(height=260)
)

# Capture the selection
selection_event = st.altair_chart(bars4, key="bars4", on_select="rerun", selection_mode=["cat"], use_container_width=True)

selected = []
if selection_event:
    selected = [d["category"] for d in selection_event.get("selection", {}).get("cat", [])]

fdf = df_monthly[df_monthly["category"].isin(selected)] if selected else df_monthly

st.markdown(
    """### Example Content: the charts don't have to be at the same location
The charts below are filtered by the selection above. Use this space creative formatting without breaking the interaction.
"""
)

# Follow-up charts that read the same shared selection
line4 = (
    alt.Chart(fdf, title=f"{AGG_LABEL} {METRIC_LABEL} over Time")
    .mark_line(point=True)
    .encode(
        x=alt.X("date:T", title="Month"),
        y=alt.Y("value:Q", title=f"{AGG_LABEL} {METRIC_LABEL}"),
        color="category:N",
        tooltip=[alt.Tooltip("date:T", title="Month"), "category:N", alt.Tooltip("value:Q", title=f"{AGG_LABEL} {METRIC_LABEL}")],
    )
)

hist4 = (
    alt.Chart(fdf, title=f"Distribution of {METRIC_LABEL}")
    .mark_bar()
    .encode(
        x=alt.X("value:Q", bin=alt.Bin(maxbins=30), title=METRIC_LABEL),
        y=alt.Y("count()", title="Count"),
        tooltip=[alt.Tooltip("count()", title="Count")],
    )
)

st.altair_chart(line4, use_container_width=True)
st.altair_chart(hist4, use_container_width=True)

st.code(
"""# Define a selection on 'category'
sel = alt.selection_point(name="cat", fields=["category"], on="click", clear="dblclick")

# Top chart publishes the selection
bars4 = alt.Chart(df_monthly).mark_bar().encode(...).add_params(sel)

# Capture selection in Streamlit and read it
selection_event = st.altair_chart(bars, key="bars", on_select="rerun", selection_mode=["cat"])

selected = []
if selection_event:
    selected = [d["category"] for d in selection_event.get("selection", {}).get("cat", [])]
    
fdf = df_monthly[df_monthly["category"].isin(selected)] if selected else df_monthly

# Downstream charts share the same filtered data
line4 = alt.Chart(fdf).mark_line(point=True).encode(...)
hist4 = alt.Chart(fdf).mark_bar().encode(...)

st.altair_chart(line4, use_container_width=True)
st.altair_chart(hist4, use_container_width=True)
""",
language="python",
)

