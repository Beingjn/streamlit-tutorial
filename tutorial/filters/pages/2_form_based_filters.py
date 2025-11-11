import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.set_page_config(page_title="Form-Based Filters", layout="wide")

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
st.title("Form-Based Filters")

st.markdown(
    """
This part focuses on form-based filters. Unlike widgets which re-run the script
on every change, a form batches changes and only applies them when you click Apply.
That’s useful when filtering large datasets or when each change would trigger expensive work.
"""
)

# Why forms for filters
st.header("1) Why form-based filters?")
st.markdown(
    """
- Reactive: Every change re-runs the app immediately. Great for small data and fast feedback.  
- Form-based: Users can adjust several controls and then click Apply once.  
  - Fewer re-runs while tweaking inputs  
  - Clear “Apply / Reset” interaction  
  - Useful when loading/aggregating is expensive
"""
)
st.header("2) About Session State")
st.markdown(
    """
We briefly discussed Session State in Key Concepts, feel free to check it again.  
Session State in Streamlit docs: https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state
    
What it is: Session State is Streamlit’s small, per-user memory. Your script reruns top-to-bottom on every interaction; 
Session State keeps chosen values (like selected dates or “Apply/Reset” choices) alive across those reruns.

Why here: forms batch changes, nothing updates until Apply. Keep the “applied” values in
Session State; charts read from that until you overwrite it.
"""
)

# Example: Apply/Reset with one mask
st.header("3) Example")
st.markdown(
    """
Use the form in the sidebar to pick categories, dates, and a value range.  
Click Apply to update the outputs in one shot, or Reset to restore defaults.
"""
)

# Defaults (used to initialize and to reset)
all_categories = sorted(df["category"].unique().tolist())
min_d, max_d = df["date"].min().date(), df["date"].max().date()
vmin, vmax = float(df["value"].min()), float(df["value"].max())
default_filters = {
    "cats": all_categories,
    "start": pd.to_datetime(min_d),
    "end": pd.to_datetime(max_d),
    "low": float(vmin),
    "high": float(vmax),
}

# Ensure defaults in session_state
if "applied_filters" not in st.session_state:
    st.session_state["applied_filters"] = default_filters.copy()

current = st.session_state["applied_filters"]

# Form
st.sidebar.header("Filters")

with st.sidebar.form("filters_form"):
    selected_cats = st.multiselect(
        "Category",
        options=all_categories,
        default=current["cats"],
    )

    date_range = st.date_input(
        "Date range",
        (current["start"].date(), current["end"].date()),
        min_value=min_d,
        max_value=max_d,
    )

    low_high = st.slider(
        "Value range",
        min_value=float(vmin),
        max_value=float(vmax),
        value=(float(current["low"]), float(current["high"])),
    )

    col_apply, col_reset = st.columns(2)
    applied = col_apply.form_submit_button("Apply")
    reset = col_reset.form_submit_button("Reset")

# Update the applied filters when Apply or Reset is pressed
if reset:
    st.session_state["applied_filters"] = default_filters.copy()
elif applied:
    if isinstance(date_range, tuple):
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range
    st.session_state["applied_filters"] = {
        "cats": selected_cats if selected_cats else [],
        "start": pd.to_datetime(start_date),
        "end": pd.to_datetime(end_date),
        "low": float(low_high[0]),
        "high": float(low_high[1]),
    }

# Always read from the last applied values
applied_vals = st.session_state["applied_filters"]

# Boolean mask
mask = pd.Series(True, index=df.index)
if applied_vals["cats"]:  # if empty, everything is included
    mask &= df["category"].isin(applied_vals["cats"])
start_ts, end_ts = applied_vals["start"], applied_vals["end"]
mask &= df["date"].between(start_ts, end_ts)
mask &= df["value"].between(applied_vals["low"], applied_vals["high"])

filtered = df.loc[mask].copy()

# Outputs: table + chart 
c1, c2 = st.columns([2, 3])

with c1:
    st.subheader("Filtered table")
    st.dataframe(filtered, use_container_width=True, hide_index=True)
    st.caption(
        f"Rows: {len(filtered):,} • Categories: {', '.join(sorted(map(str, filtered['category'].unique())))}"
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
        .interactive()
    )
    st.altair_chart(chart, use_container_width=True)

# Structure of a form-based filter
st.header("4) Structure of a form-based filter")
st.markdown(
    """
We keep one source of truth in `st.session_state["applied_filters"]`.  
The form shows the current values, and only when the user clicks Apply do we update those values and rebuild the mask.  
Conceptal Pattern:
"""
)
st.code(
    """
# 1) Ensure defaults in session_state
if "applied_filters" not in st.session_state:
    st.session_state["applied_filters"] = default_filters

# 2) Build the form
with st.sidebar.form("filters_form"):
    # controls...
    applied = st.form_submit_button("Apply")
    reset = st.form_submit_button("Reset")

# 3) On submit, update session_state (or restore defaults on Reset)
if applied:
    st.session_state["applied_filters"] = {...from form...}
elif reset:
    st.session_state["applied_filters"] = default_filters

# 4) Build boolean mask from st.session_state["applied_filters"]
mask = ...
filtered = df.loc[mask]
    """,
    language="python",
)
st.write("And here's the code used in this example")
st.code(
    """
# 1) Defaults and ensure defaults in session_state
# Defaults
all_categories = sorted(df["category"].unique().tolist())
min_d, max_d = df["date"].min().date(), df["date"].max().date()
vmin, vmax = float(df["value"].min()), float(df["value"].max())
default_filters = {
    "cats": all_categories,
    "start": pd.to_datetime(min_d),
    "end": pd.to_datetime(max_d),
    "low": float(vmin),
    "high": float(vmax),
}

# Ensure defaults in session_state
if "applied_filters" not in st.session_state:
    st.session_state["applied_filters"] = default_filters.copy()
current = st.session_state["applied_filters"]

# 2) Build the form
with st.sidebar.form("filters_form"):
    selected_cats = st.multiselect(
        "Category",
        options=all_categories,
        default=current["cats"],
    )

    date_range = st.date_input(
        "Date range",
        (current["start"].date(), current["end"].date()),
        min_value=min_d,
        max_value=max_d,
    )

    low_high = st.slider(
        "Value range",
        min_value=float(vmin),
        max_value=float(vmax),
        value=(float(current["low"]), float(current["high"])),
    )

    col_apply, col_reset = st.columns(2)
    applied = col_apply.form_submit_button("Apply")
    reset = col_reset.form_submit_button("Reset")

# 3) On submit, update session_state (or restore defaults on Reset)
if reset:
    st.session_state["applied_filters"] = default_filters.copy()
elif applied:
    if isinstance(date_range, tuple):
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range
    st.session_state["applied_filters"] = {
        "cats": selected_cats if selected_cats else [],
        "start": pd.to_datetime(start_date),
        "end": pd.to_datetime(end_date),
        "low": float(low_high[0]),
        "high": float(low_high[1]),
    }

# 4) Build boolean mask from st.session_state["applied_filters"]
applied_vals = st.session_state["applied_filters"]
mask = pd.Series(True, index=df.index)
if applied_vals["cats"]:  # if empty, everything is included
    mask &= df["category"].isin(applied_vals["cats"])
start_ts, end_ts = applied_vals["start"], applied_vals["end"]
mask &= df["date"].between(start_ts, end_ts)
mask &= df["value"].between(applied_vals["low"], applied_vals["high"])

filtered = df.loc[mask]
    """,
    language="python",
)
