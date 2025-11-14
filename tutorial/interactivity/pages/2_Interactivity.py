import streamlit as st
import pandas as pd
import altair as alt
from pathlib import Path

st.set_page_config(page_title="Lab 5 — Interactivity", layout="wide")
st.title("Lab 5 — Interactivity & Linked Charts")

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

# Keep only the TOP 5 categories by record
TOP_N = 5
_top = raw[CATEGORY].value_counts().nlargest(TOP_N).index
raw = raw[raw[CATEGORY].isin(_top)].copy()

work = raw.dropna(subset=["date", METRIC])[["date", CATEGORY, METRIC]].copy()
work["month"] = work["date"].dt.to_period("M").dt.to_timestamp()

df = (
    work.groupby(["month", CATEGORY])[METRIC]
    .agg(AGG)
    .reset_index()
    .rename(columns={"month": "date", CATEGORY: "category", METRIC: "value"})
)

METRIC_LABEL = METRIC.replace("_", " ").title()
AGG_LABEL = AGG.title()
CAT_LABEL = CATEGORY.replace("_", " ").title()

st.subheader("Data preview")
st.caption(
    "This app uses the same dataset as the Formatting section, restricted to the top 5 cities by record count."
)
st.dataframe(raw.head(20), use_container_width=True)

# 1) Brush-linked line + bar (horizontal concat with `|`)
st.header("1) Brush-linked line + bar (using `|`) ")
st.markdown(
    f"""
    **Goal:** Use a brush on the time-vs-{METRIC_LABEL.lower()} line to filter the bar chart.

    * Brush across the line to focus a specific time range and value region.
    * The bar chart summarizes **{AGG_LABEL} {METRIC_LABEL}** by **{CAT_LABEL}** for the brushed subset.
    """
)

brush1 = alt.selection_interval(name="brush1")

lines1 = (
    alt.Chart(df, title=f"{METRIC_LABEL} over Time by {CAT_LABEL} — brush to filter")
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
    alt.Chart(df, title=f"{AGG_LABEL} {METRIC_LABEL} by {CAT_LABEL} (filtered by brush)")
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
    alt.Chart(df, title=f"{METRIC_LABEL} over Time by {CAT_LABEL} — brush to filter")
    .mark_line(point=True)
    .encode(...)
    .add_params(brush1)
)

bars1 = (
    alt.Chart(df, title=f"{AGG_LABEL} {METRIC_LABEL} by {CAT_LABEL} (filtered by brush)")
    .mark_bar()
    .encode(...)
    .transform_filter(brush1)
)

st.altair_chart((lines1 | bars1).resolve_scale(color="independent"), use_container_width=True)
''',
    language="python",
)

# 2) Legend-click filtering
st.header("2) Legend filtering")
st.markdown(
    "Click legend entries to filter categories without altering the chart layout."
)

legend = alt.selection_point(name="legend", fields=["category"], bind="legend")

lines2 = (
    alt.Chart(df, title=f"{AGG_LABEL} {METRIC_LABEL} over Time by {CAT_LABEL} — legend click to filter")
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

st.altair_chart(lines2, use_container_width=True)

st.code(
    f'''
legend = alt.selection_point(name="legend", fields=["category"], bind="legend")

lines2 = (
    alt.Chart(df, title=f"{AGG_LABEL} {METRIC_LABEL} over Time by {CAT_LABEL} — legend click to filter")
    .mark_line(point=True)
    .encode(...)
    .add_params(legend)
    .transform_filter(legend)
)

st.altair_chart(lines2, use_container_width=True)
''',
    language="python",
)

# 3) Click-linked bars ↔ line (vertical concat with `&`)
st.header("3) Click-linked bars ↔ line (using `&`)")
st.markdown(
    """
    **Altair composition operators:**

    * `|` — **Horizontal concat** (charts side-by-side)
    * `&` — **Vertical concat** (charts stacked)
    * `+` — **Layering** (treat multiple marks as **one chart** on the same axes)

    In this section, click a **category** in the bar chart to filter the line below.
    You can also **brush** on the line to constrain the bars above. Two linked
    interactions, two directions of filtering.
    """
)

click_cat = alt.selection_point(name="cat_click", fields=["category"], on="click", clear="dblclick")
brush3 = alt.selection_interval(name="brush3")

bars3 = (
    alt.Chart(df, title=f"{AGG_LABEL} {METRIC_LABEL} by {CAT_LABEL} — click to filter")
    .mark_bar()
    .encode(
        y=alt.Y("category:N", sort="-x", title=CAT_LABEL),
        x=alt.X("mean(value):Q", title=f"{AGG_LABEL} {METRIC_LABEL}"),
        color=alt.condition(click_cat, "category:N", alt.value("lightgray")),
        tooltip=["category:N", alt.Tooltip("mean(value):Q", title=f"{AGG_LABEL} {METRIC_LABEL}")],
    )
    .add_params(click_cat)
    .transform_filter(brush3)  # brush on the line constrains these bars
    .properties(height=160)
)

lines3 = (
    alt.Chart(df, title=f"{AGG_LABEL} {METRIC_LABEL} over Time — brushed; filtered by bar click")
    .mark_line(point=True)
    .encode(
        x=alt.X("date:T", title="Month"),
        y=alt.Y("value:Q", title=f"{AGG_LABEL} {METRIC_LABEL}"),
        color="category:N",
        tooltip=[alt.Tooltip("date:T", title="Month"), "category:N", alt.Tooltip("value:Q", title=f"{AGG_LABEL} {METRIC_LABEL}")],
    )
    .add_params(brush3)
    .transform_filter(click_cat)
)

st.altair_chart((bars3 & lines3).resolve_scale(color="independent"), use_container_width=True)

st.code(
    f'''
click_cat = alt.selection_point(name="cat_click", fields=["category"], on="click", clear="dblclick")
brush3 = alt.selection_interval(name="brush3")

bars3 = (
    alt.Chart(df, title=f"{AGG_LABEL} {METRIC_LABEL} by {CAT_LABEL} — click to filter")
    .mark_bar()
    .encode(...)
    .add_params(click_cat)
    .transform_filter(brush3)  # brush on the line constrains these bars
    .properties(height=160)
)

lines3 = (
    alt.Chart(df, title=f"{AGG_LABEL} {METRIC_LABEL} over Time — brushed; filtered by bar click")
    .mark_line(point=True)
    .encode(...)
    .add_params(brush3)
    .transform_filter(click_cat)
)

st.altair_chart((bars3 & lines3).resolve_scale(color="independent"), use_container_width=True)
''',
    language="python",
)

# 4) Page-wide linking via Streamlit events
st.header("4) Page-wide linking via shared state")
st.markdown(
    f"""
    In this section, we **do not** use Altair's concat operators. Instead, we:

    1. Create a top bar chart of **{CAT_LABEL}** and expose a named selection param.
    2. Capture that selection in Streamlit (`on_select="rerun"`).
    3. Recompute a filtered DataFrame in Python.
    4. Render follow-up charts **elsewhere on the page**, all filtered by the same state.

    **Why this pattern?** It keeps charts **connected** while allowing rich text and layout in between, ideal for tutorials and storytelling.
    """
)

sel = alt.selection_point(name="cat", fields=["category"], on="click", clear="dblclick")

bars4 = (
    alt.Chart(df, title=f"Select {CAT_LABEL} (dbl-click to clear)")
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

# Capture the selection state so we can filter arbitrary charts below
selection_event = st.altair_chart(bars4, key="bars4", on_select="rerun", selection_mode=["cat"], use_container_width=True)

selected = []
if selection_event:
    selected = [d["category"] for d in selection_event.get("selection", {}).get("cat", [])]

fdf = df[df["category"].isin(selected)] if selected else df

st.markdown(
    """### Narrative space: explain what the reader should notice
The charts below are filtered by the selection above. Use this space to add context, callouts, or inline instructions without breaking the interaction.
"""
)

# Follow-up charts that read the same shared selection state
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

# Boiled-down essentials
st.code(
"""# Define a selection on 'category'
sel = alt.selection_point(name="cat", fields=["category"], on="click", clear="dblclick")

# Top chart publishes the selection
bars4 = alt.Chart(df).mark_bar().encode(...).add_params(sel)

# Capture selection in Streamlit and read it
selection_event = st.altair_chart(bars, key="bars", on_select="rerun", selection_mode=["cat"])

selected = []
if selection_event:
    selected = [d["category"] for d in selection_event.get("selection", {}).get("cat", [])]
    
fdf = df[df["category"].isin(selected)] if selected else df

# Downstream charts share the same filtered data
line4 = alt.Chart(fdf).mark_line(point=True).encode(...)
hist4 = alt.Chart(fdf).mark_bar().encode(...)

st.altair_chart(line4, use_container_width=True)
st.altair_chart(hist4, use_container_width=True)
""",
language="python",
)

