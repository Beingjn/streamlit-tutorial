# How to start this app
#
# Start the app from the project folder(in terminal):
#   streamlit run formatting_basics.py
# Your browser should open to:
#   http://localhost:8501
#   (If it doesn’t, copy that URL into your browser.)
# Stop the app: press Ctrl+C in the terminal.

import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Formatting Basics", layout="wide")

st.title("Formatting Basics")

st.markdown("""
### What this page covers

This quick guide shows how to format Streamlit apps: 
headings and body text, KPI tiles with `st.metric`, and the core layout primitives: columns, tabs, expanders, containers,
and the sidebar. Every snippet is minimal and copy-pasteable, so you can remix them into dashboards fast.

For detailed descriptions and all function parameters, see the [official Streamlit docs](https://docs.streamlit.io).
""")



# Sample data
np.random.seed(0)
dates = pd.date_range("2024-01-01", periods=24, freq="M")
regions = np.random.choice(["East", "West", "North", "South"], size=len(dates))
sales = np.random.randint(50, 200, size=len(dates))
df = pd.DataFrame({"date": dates, "region": regions, "sales": sales})

# 1) Titles, Headings & Body Text
st.subheader("1) Titles, Headings & Body Text")

# Title / Header hierarchy
st.title("Page Title (H1)")
st.code("st.title()", language="python")
st.header("Section Title (H2)")
st.code("st.header()", language="python")
st.subheader("Subsection (H3)")
st.code("st.subheader()", language="python")

# Body text
st.write("This is regular body text with `st.write()`. Use it for paragraphs and inline code like `x = 42`.")
st.caption("Captions `st.caption()` are for small, supporting notes.")
st.info("Use `st.info()` for info boxes.")
st.write("Other flavours:")
st.success("`st.success()`")
st.warning("`st.warning()`")
st.error("`st.error()`")

st.write("Links:")
st.markdown("[markdown links](https://docs.streamlit.io)")
st.code('st.markdown("[markdown links](https://docs.streamlit.io)")')
st.link_button("button links", "https://docs.streamlit.io")
st.code('st.link_button("button links", "https://docs.streamlit.io")')


st.divider()
st.write("Divider like this:")
st.divider()
st.code("st.divider()")
st.divider()


# Markdown basics
st.markdown("""`st.markdown` supports GitHub-flavored Markdown. Syntax information can be found at: 
[https://github.github.com/gfm](https://github.github.com/gfm).\n
**Markdown** supports _italics_, **bold**, `inline code`, and lists:""")
st.code('st.markdown("**Markdown** supports _italics_, **bold**, `inline code`, and lists:")')
st.markdown("- Bullet 1\n- Bullet 2\n- Bullet 3")
st.code('st.markdown("- Bullet 1\\n- Bullet 2\\n- Bullet 3")')

st.markdown("### Markdown headings (H3)")
st.code('st.markdown("### Markdown headings (H3)")', language="python")
st.markdown('markdown supports H1-H6 headings')
st.markdown("#### H4 (Markdown only)")
st.code('st.markdown("#### H4 (Markdown only)")', language="python")
st.markdown("##### H5 (Markdown only)")
st.code('st.markdown("##### H5 (Markdown only)")', language="python")
st.markdown("###### H6 (Markdown only)")
st.code('st.markdown("###### H6 (Markdown only)")', language="python")

st.divider()

# Sidebar variants
st.sidebar.header("Sidebar Heading")
st.sidebar.subheader("Sidebar Subheading")
st.sidebar.caption("Sidebar helper text")
st.sidebar.code('st.sidebar.header/subheader/...")', language="python")



# 2) metrics 
st.subheader("2) Metrics")
st.write("Use columns and `st.metric` for quick KPI tiles.")

# KPI row using columns
m = (
    df.groupby(pd.Grouper(key="date", freq="M"))["sales"]
    .sum()
    .sort_index()
)

last = m.iloc[-1] if len(m) else 0
prev = m.iloc[-2] if len(m) > 1 else 0
delta = last - prev
delta_pct = ((last / prev) - 1) * 100 if prev else 0

k1, k2, k3 = st.columns(3)
with k1:
    st.metric("Total Sales", f"{int(m.sum()):,}", f"{delta:+.0f}")
with k2:
    st.metric("Avg / Month", f"{m.mean():.1f}", f"{delta_pct:+.1f}%")
with k3:
    st.metric("Last Month", f"{last:,.0f}", f"{delta:+.0f}")

st.metric(
label="Revenue",
value="$12,340",
delta="+320",                 # arrow from sign: "+" up, "-" down
delta_color="normal",         # "normal" | "inverse" | "off"
help="Current vs previous period",
label_visibility="visible",   # "visible" | "hidden" | "collapsed"
)

# All argumnts
st.code(
    '''st.metric(
    label="Revenue",
    value="$12,340",
    delta="+320",
    delta_color="normal",         # "normal" | "inverse" | "off"
    help="Current vs previous period",
    label_visibility="visible",   # "visible" | "hidden" | "collapsed"
    )'''
    , language="python")

st.divider()

# 3) Columns
st.subheader("3) Columns")
st.write("Place content side-by-side. Control relative widths and nest as needed.")

left, right = st.columns([2, 1])
with left:
    st.markdown("**Left (2x width)**")
    st.line_chart(df.set_index("date")["sales"])
with right:
    st.markdown("**Right (1x width)**")
    st.write("Summary table:")
    st.dataframe(df.groupby("region", as_index=False)["sales"].sum())

st.code(
    """
left, right = st.columns([2, 1])
with left:
    st.markdown("**Left (2x width)**")
    st.line_chart(...)
with right:
    st.markdown("**Right (1x width)**")
    st.write("Summary table:")
    st.dataframe(...)
    """
)

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
st.code(
    """
outer1, outer2 = st.columns(2)
with outer1:
    st.write("Outer col 1")
    inner1, inner2, inner3 = st.columns(3)
    inner1.write("Inner 1")
    inner2.write("Inner 2")
    inner3.write("Inner 3")
with outer2:
    st.write("Outer col 2 (use for related widgets or notes)")
    """
)
st.divider()

# 4) Tabs
st.subheader("4) Tabs")
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
st.write("The structure for tabs are similar to columns:")
st.code(
    """
    tab1, tab2, tab3 = st.tabs(["Trend", "Breakdown", "Notes"])

    with tab1:
        # content
    with tab2:
        # content
    with tab3:
        # content"""
)


# 5) Expanders (progressive disclosure of details)
st.subheader("5) Expanders")
st.write("Hide advanced or optional details until the user opens them.")

with st.expander("Raw data (first 10 rows)"):
    st.dataframe(df.head(10), use_container_width=True)

st.code(
    """
    with st.expander("Raw data (first 10 rows)"):
        st.dataframe(df.head(10), use_container_width=True)
    """
)
st.divider()

# 6) Containers & placeholders (grouping + dynamic areas)
st.subheader("6) Containers & placeholders")
st.write("`st.container()` groups related UI. `st.empty()` reserves a spot you can fill later.")

with st.container():
    c1, c2 = st.columns(2)
    with c1:
        st.write("Left: quick stat")
        st.metric("Max monthly sales", int(df.sales.max()))
    with c2:
        st.write("Right: quick chart")
        st.area_chart(df.set_index("date")["sales"])

st.code(
    """
    with st.container():
    c1, c2 = st.columns(2)
    with c1:
        # content
    with c2:
        # content
    """
)

# Placeholder that fills on button click
holder = st.empty()
holder.caption("Nothing here yet. click the button to load the table.")

if st.button("Fill placeholder with a table"):
    holder.dataframe(df.tail(6), use_container_width=True)
st.code(
    """
    holder = st.empty()
    holder.caption("Nothing here yet. click the button to load the table.")

    if st.button("Fill placeholder with a table"):
        holder.dataframe(df.tail(6), use_container_width=True)
    """
)    

st.divider()

# 7) Sidebar vs Main pattern
st.subheader("7) Sidebar vs Main")
st.write("A common dashboard pattern: inputs in the sidebar, outputs in the main area.")

# Sidebar controls
st.sidebar.subheader("Filters")
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

st.write("How to put widges in the sidebar:")
st.code(
    """
st.sidebar.subheader("Filters")
pick_region = st.sidebar.multiselect("Region", sorted(df["region"].unique()))
n_cols = st.sidebar.slider("KPI columns", min_value=2, max_value=4, value=3)
    """
)
