# Lab 1 — Getting Started & Layout Basics

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# 1) Page config & intro
st.set_page_config(page_title="Lab 1 — Getting Started & Layout Basics", page_icon="1️⃣", layout="wide")

st.title("Lab 1 — Getting Started & Layout Basics")
st.caption("Install, run, understand the re-run model, and explore common layout patterns for dashboards.")
st.subheader("1.Getting Started")

with st.expander("How to run this app (CLI)"):
    st.code(
        "pip install streamlit pandas numpy\n"
        "streamlit run lab1.py\n\n"
        "# Stop with Ctrl+C in the terminal.", language="bash"
    )

# runs so far readout
if "runs" not in st.session_state:
    st.session_state.runs = 0
st.session_state.runs += 1
st.write(f"*Reruns this session:* **{st.session_state.runs}** • Time: {datetime.now().strftime('%H:%M:%S')}")

st.divider()

# 2) Re-run model
st.subheader("2.How Streamlit’s re-run model works")

st.markdown(
    """
- Streamlit **executes this script top-to-bottom** on any interaction:
  - changing a widget, clicking a button, uploading a file, or saving this file.
- **Variables reset** each run unless you store them in `st.session_state`.
- Widgets **return values** (like function calls) that you can use immediately in your code.
- Think: “every interaction = a fresh run with the latest inputs,” not an event loop.
"""
)

# Demo 1 — a persistent counter vs a per-run random number
if "counter" not in st.session_state:
    st.session_state.counter = 0

colA, colB, colC = st.columns([1, 1, 2])
with colA:
    if st.button("Increment counter"):
        st.session_state.counter += 1
with colB:
    if st.button("Reset counter"):
        st.session_state.counter = 0
with colC:
    st.write(f"**Persistent counter (session_state):** {st.session_state.counter}")

# This value changes every run to prove code re-executes
random_per_run = np.random.randint(0, 1000)
st.write(f"**Per-run value (resets each run):** {random_per_run}")

# Demo 2 — widget changes trigger re-runs; callbacks can record events
def _mark_event():
    st.session_state.last_event = f"{datetime.now():%H:%M:%S}"

st.text_input("Your name (changing me re-runs the app)", key="name", on_change=_mark_event)
st.slider("Pick a number", 0, 10, 5, key="num", on_change=_mark_event)

st.caption(
    "Tip: Use `key=` to name widget values in `st.session_state`. "
    "Callbacks like `on_change` run before the next full re-run."
)

# Show a snapshot of session_state
_safe_state = {k: v for k, v in st.session_state.items() if isinstance(v, (int, float, str, bool))}
with st.expander("Session state snapshot"):
    st.write(_safe_state)

if "last_event" in st.session_state:
    st.info(f"Last widget change recorded at: {st.session_state.last_event}")

st.divider()

# Sample data used across layout demos
np.random.seed(0)
dates = pd.date_range("2024-01-01", periods=24, freq="M")
regions = np.random.choice(["East", "West", "North", "South"], size=len(dates))
sales = np.random.randint(50, 200, size=len(dates))
df = pd.DataFrame({"date": dates, "region": regions, "sales": sales})

# Sidebar toggles to show/hide layout sections
st.sidebar.header("Show/Hide Sections")
show_titles = st.sidebar.checkbox("3.Titles & Headings", True)
show_basic = st.sidebar.checkbox("4.Basic text & metrics", True)
show_columns = st.sidebar.checkbox("5.Columns", True)
show_tabs = st.sidebar.checkbox("6.Tabs", True)
show_expanders = st.sidebar.checkbox("7.Expanders", True)
show_container = st.sidebar.checkbox("8.Containers & placeholders", True)
show_sidebar_vs_main = st.sidebar.checkbox("9.Sidebar vs Main pattern", True)


# 3) Titles, Headings & Body Text
if show_titles:
    st.subheader("3.Titles, Headings & Body Text")
    st.caption("Use these building blocks to structure your Streamlit app clearly.")

    # Title / Header hierarchy
    st.title("st.title — Page Title (H1)")
    st.header("st.header — Section Title (H2)")
    st.subheader("st.subheader — Subsection (H3)")

    # Body text
    st.write("This is regular body text with `st.write()`. Use it for paragraphs and inline code like `x = 42`.")
    st.caption("Captions are for small, supporting notes—timestamps, data sources, caveats.")

    st.divider()

    # Markdown basics (inline + headings beyond H3)
    st.markdown("**Markdown** supports _italics_, **bold**, `inline code`, and lists:")
    st.markdown("- Bullet 1\n- Bullet 2\n- Bullet 3")

    st.markdown("### Markdown headings (H3)")
    st.markdown("#### H4 (Markdown only)")
    st.markdown("##### H5 (Markdown only)")
    st.markdown("###### H6 (Markdown only)")

    st.divider()

    # Sidebar variants (optional)
    st.sidebar.header("Sidebar Heading")
    st.sidebar.subheader("Sidebar Subheading")
    st.sidebar.caption("Sidebar helper text")


# 4) Basic text & metrics (simple blocks + KPI tiles)
if show_basic:
    st.subheader("4.Basic text & metrics")
    st.write("Use headings, paragraphs, and `st.metric` for quick KPI tiles.")

    # KPI row using columns
    k1, k2, k3 = st.columns(3)
    with k1:
        st.metric("Total Sales", f"{int(df.sales.sum()):,}")
    with k2:
        st.metric("Avg / Month", f"{df.sales.mean():.1f}")
    with k3:
        delta = (df.sales.iloc[-1] - df.sales.iloc[-2]) if len(df) > 1 else 0
        st.metric("Last Month Δ", f"{delta:+}")

    st.info("Tip: Use a KPI row near the top of a dashboard.")
    st.divider()

# 5) Columns (side-by-side content, custom widths, nesting)
if show_columns:
    st.subheader("5.Columns")
    st.write("Place content side-by-side. Control relative widths and nest as needed.")

    left, right = st.columns([2, 1])
    with left:
        st.markdown("**Left (2x width)**")
        st.line_chart(df.set_index("date")["sales"])
    with right:
        st.markdown("**Right (1x width)**")
        st.write("Summary table:")
        st.dataframe(df.groupby("region", as_index=False)["sales"].sum())

    st.markdown("**Nested columns**")
    outer1, outer2 = st.columns(2)
    with outer1:
        st.write("Outer col 1")
        inner1, inner2, inner3 = st.columns(3)
        inner1.write("Inner 1")
        inner2.write("Inner 2")
        inner3.write("Inner 3")
    with outer2:
        st.write("Outer col 2 (use for related widgets or notes)")
    st.divider()

# 6) Tabs (alternate views in the same screen real estate)
if show_tabs:
    st.subheader("6.Tabs")
    st.write("Tabs let you present alternate views without changing pages.")
    tab1, tab2, tab3 = st.tabs(["Trend", "Breakdown", "Notes"])

    with tab1:
        st.write("**Trend view** — focus on the time-series.")
        st.line_chart(df.set_index("date")["sales"], use_container_width=True)

    with tab2:
        st.write("**Breakdown view** — compare categories.")
        grouped = df.groupby("region", as_index=False)["sales"].sum().sort_values("sales", ascending=False)
        st.bar_chart(grouped.set_index("region")["sales"], use_container_width=True)

    with tab3:
        st.write("**Notes** — Put context, caveats, or instructions here.")
        st.text_area("Notes", "Add your observations here…")
    st.divider()

# 7) Expanders (progressive disclosure of details)
if show_expanders:
    st.subheader("7.Expanders")
    st.write("Hide advanced or optional details until the user opens them.")

    with st.expander("Raw data (first 10 rows)"):
        st.dataframe(df.head(10), use_container_width=True)

    with st.expander("Computation details"):
        st.write("- Sales is synthetic here; in class you’ll load real data.")
        st.write("- Use expanders for long text, FAQs, or secondary visuals.")
    st.divider()

# 8) Containers & placeholders (grouping + dynamic areas)
if show_container:
    st.subheader("8.Containers & placeholders")
    st.write("`st.container()` groups related UI. `st.empty()` reserves a spot you can fill later.")

    with st.container():
        st.write("Container start → good for grouping a mini-section.")
        c1, c2 = st.columns(2)
        with c1:
            st.write("Left: quick stat")
            st.metric("Max monthly sales", int(df.sales.max()))
        with c2:
            st.write("Right: quick chart")
            st.area_chart(df.set_index("date")["sales"])

        st.write("Container end.")

    # Placeholder that fills on button click
    holder = st.empty()
    if st.button("Fill placeholder with a table"):
        holder.dataframe(df.tail(6), use_container_width=True)
    st.divider()

# 9) Sidebar vs Main pattern (controls on left, visuals on right)
if show_sidebar_vs_main:
    st.subheader("9.Sidebar vs Main")
    st.write("A common dashboard pattern: inputs in the sidebar, outputs in the main area.")

    # Sidebar controls
    st.sidebar.subheader("Filters (demo)")
    pick_region = st.sidebar.multiselect("Region", sorted(df["region"].unique()))
    n_cols = st.sidebar.slider("KPI columns", min_value=2, max_value=4, value=3)

    # Filtered data view
    filt = df[df["region"].isin(pick_region)] if pick_region else df

    # KPI row with dynamic number of columns
    kpi_cols = st.columns(n_cols)
    totals = [
        ("Rows", f"{len(filt):,}"),
        ("Total Sales", f"{int(filt.sales.sum()):,}"),
        ("Avg Sales", f"{filt.sales.mean():.1f}"),
        ("Max Sales", f"{int(filt.sales.max())}"),
    ]
    for (label, val), col in zip(totals, kpi_cols):
        with col:
            st.metric(label, val)

    # Main visuals react to sidebar
    t1, t2 = st.columns([3, 2])
    with t1:
        st.write("Filtered time-series")
        st.line_chart(filt.set_index("date")["sales"], use_container_width=True)
    with t2:
        st.write("Filtered by region")
        grouped = filt.groupby("region", as_index=False)["sales"].sum().sort_values("sales", ascending=False)
        st.bar_chart(grouped.set_index("region")["sales"], use_container_width=True)

