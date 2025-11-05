import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.set_page_config(page_title="Filter Placement Patterns", layout="wide")

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

# Inventory dataset
warehouses = ["East", "West", "Central"]
inv_rows = []
for w in warehouses:
    base = 500 + np.linspace(0, -60, len(days))
    noise = np.random.normal(0, 6, len(days)).cumsum()
    stock = np.maximum(0, base + noise)
    inv_rows.extend({"date": d, "warehouse": w, "stock": float(s)} for d, s in zip(days, stock))
df_inventory = pd.DataFrame(inv_rows)

# Title & Overview 
st.title("Filter Placement Patterns Beyond the Sidebar")

st.markdown(
    """
When pages get long and widgets pile up, the sidebar isn’t your only option.

Three practical patterns:
1) Global filter bar at the top — one set of filters that affects everything.  
2) Section/tab–scoped filters — each section controls only its own charts.  
3) Per-chart expanders — light, local controls that stay out of the way.

Below, we’ll build a top toolbar for global date filtering, then give each tab its own local filters.
"""
)

# Global filter bar (top toolbar)
st.header("1) Global filter bar (applies across the page)")
st.markdown(
    """
We place a form at the top so changes are batched — nothing updates until you click Apply.
The global filter keeps the page consistent when *all* charts share a common dimension (dates, region, etc.).
"""
)

# Defaults for global dates (shared by both datasets)
g_min = min(df["date"].min(), df_inventory["date"].min()).date()
g_max = max(df["date"].max(), df_inventory["date"].max()).date()

if "global" not in st.session_state:
    st.session_state["global"] = {"start": pd.to_datetime(g_min), "end": pd.to_datetime(g_max)}

with st.form("global_toolbar"):
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        g_start = st.date_input("Global start date", value=st.session_state["global"]["start"].date(), min_value=g_min, max_value=g_max)
    with c2:
        g_end = st.date_input("Global end date", value=st.session_state["global"]["end"].date(), min_value=g_min, max_value=g_max)
    with c3:
        apply_global = st.form_submit_button("Apply")

if apply_global:
    st.session_state["global"]["start"] = pd.to_datetime(g_start)
    st.session_state["global"]["end"] = pd.to_datetime(g_end)

g_start_ts, g_end_ts = st.session_state["global"]["start"], st.session_state["global"]["end"]

# These two filtered frames are reused by every section below
sales_global = df[df["date"].between(g_start_ts, g_end_ts)]
inv_global   = df_inventory[df_inventory["date"].between(g_start_ts, g_end_ts)]

st.caption(f"Global date window: {g_start_ts.date()} → {g_end_ts.date()}")

# Section-scoped filters (tabs)
st.header("2) Section-scoped filters (each tab controls its own charts)")
st.markdown(
    """
Use tabs to separate topic areas (e.g., Sales vs. Inventory).  
Each tab has a form with local filters. They start from the global window, then apply their own masks.
"""
)

tab1, tab2 = st.tabs(["Sales", "Inventory"])

# Tab 1: Sales
with tab1:
    st.subheader("Sales — local filters (on top of the global date window)")

    if "sales_filters" not in st.session_state:
        st.session_state["sales_filters"] = {
            "cats": sorted(sales_global["category"].unique().tolist()),
            "low": float(sales_global["value"].min()) if not sales_global.empty else 0.0,
            "high": float(sales_global["value"].max()) if not sales_global.empty else 1.0,
        }

    s_current = st.session_state["sales_filters"]
    s_all_cats = sorted(df["category"].unique().tolist())

    with st.form("sales_form"):
        c1, c2 = st.columns([2, 1])
        with c1:
            s_cats = st.multiselect("Category (local)", options=s_all_cats, default=s_current["cats"])
        with c2:
            s_low, s_high = st.slider(
                "Value range (local)",
                min_value=float(df["value"].min()),
                max_value=float(df["value"].max()),
                value=(s_current["low"], s_current["high"]),
            )
        colA, colB = st.columns(2)
        s_apply = colA.form_submit_button("Apply sales filters")
        s_reset = colB.form_submit_button("Reset sales filters")

    if s_reset:
        st.session_state["sales_filters"] = {
            "cats": sorted(df["category"].unique().tolist()),
            "low": float(df["value"].min()),
            "high": float(df["value"].max()),
        }
    elif s_apply:
        st.session_state["sales_filters"] = {"cats": s_cats, "low": float(s_low), "high": float(s_high)}

    s_vals = st.session_state["sales_filters"]

    # One mask, local to this tab (applies on top of global)
    s_mask = pd.Series(True, index=sales_global.index)
    if s_vals["cats"]:
        s_mask &= sales_global["category"].isin(s_vals["cats"])
    s_mask &= sales_global["value"].between(s_vals["low"], s_vals["high"])
    sales_filtered = sales_global.loc[s_mask].copy()

    if sales_filtered.empty:
        st.info("No rows match the Sales local filters (within the global date window).")
    else:
        c1, c2 = st.columns([2, 3])
        with c1:
            st.markdown("Filtered Sales Table")
            st.dataframe(sales_filtered, use_container_width=True, hide_index=True)
            st.caption(
                f"Rows: {len(sales_filtered):,} • Categories: {', '.join(sorted(map(str, sales_filtered['category'].unique())))}"
            )
        with c2:
            st.markdown("Sales Chart")
            chart = (
                alt.Chart(sales_filtered)
                .mark_line()
                .encode(
                    x="date:T",
                    y="value:Q",
                    color="category:N",
                    tooltip=["date:T", "category:N", "value:Q"],
                )
                .interactive()
            )
            st.altair_chart(chart, use_container_width=True)

# Tab 2: Inventory
with tab2:
    st.subheader("Inventory — local filters (on top of the global date window)")

    if "inv_filters" not in st.session_state:
        st.session_state["inv_filters"] = {
            "wh": sorted(inv_global["warehouse"].unique().tolist()),
            "low": float(inv_global["stock"].min()) if not inv_global.empty else 0.0,
            "high": float(inv_global["stock"].max()) if not inv_global.empty else 1.0,
        }

    i_current = st.session_state["inv_filters"]
    i_all_wh = sorted(df_inventory["warehouse"].unique().tolist())

    with st.form("inventory_form"):
        c1, c2 = st.columns([2, 1])
        with c1:
            i_wh = st.multiselect("Warehouse (local)", options=i_all_wh, default=i_current["wh"])
        with c2:
            i_low, i_high = st.slider(
                "Stock range (local)",
                min_value=float(df_inventory["stock"].min()),
                max_value=float(df_inventory["stock"].max()),
                value=(i_current["low"], i_current["high"]),
            )
        colA, colB = st.columns(2)
        i_apply = colA.form_submit_button("Apply inventory filters")
        i_reset = colB.form_submit_button("Reset inventory filters")

    if i_reset:
        st.session_state["inv_filters"] = {
            "wh": sorted(df_inventory["warehouse"].unique().tolist()),
            "low": float(df_inventory["stock"].min()),
            "high": float(df_inventory["stock"].max()),
        }
    elif i_apply:
        st.session_state["inv_filters"] = {"wh": i_wh, "low": float(i_low), "high": float(i_high)}

    i_vals = st.session_state["inv_filters"]

    # One mask, local to this tab (applies on top of global)
    i_mask = pd.Series(True, index=inv_global.index)
    if i_vals["wh"]:
        i_mask &= inv_global["warehouse"].isin(i_vals["wh"])
    i_mask &= inv_global["stock"].between(i_vals["low"], i_vals["high"])
    inv_filtered = inv_global.loc[i_mask].copy()

    if inv_filtered.empty:
        st.info("No rows match the Inventory local filters (within the global date window).")
    else:
        c1, c2 = st.columns([2, 3])
        with c1:
            st.markdown("Filtered Inventory Table")
            st.dataframe(inv_filtered, use_container_width=True, hide_index=True)
            st.caption(
                f"Rows: {len(inv_filtered):,} • Warehouses: {', '.join(sorted(map(str, inv_filtered['warehouse'].unique())))}"
            )
        with c2:
            st.markdown("Inventory Chart")
            # Aggregate mean stock by warehouse in the filtered date window
            inv_agg = inv_filtered.groupby(["date", "warehouse"], as_index=False)["stock"].mean()
            chart = (
                alt.Chart(inv_agg)
                .mark_line()
                .encode(
                    x="date:T",
                    y="stock:Q",
                    color="warehouse:N",
                    tooltip=["date:T", "warehouse:N", "stock:Q"],
                )
                .interactive()
            )
            st.altair_chart(chart, use_container_width=True)

# Per-chart expanders
st.header("3) Per-chart expanders (local controls per visualization)")
st.markdown(
    """
If a chart needs one or two special controls, tuck them into an expander right above
that chart. That keeps the page clean while still allowing fine-tuning.

When to use:
- A chart has unique filters not shared elsewhere  
- You want controls close to the thing they affect  
- The page already has a global or section filter you don’t want to duplicate
"""
)

st.markdown(
    """
Summary:  
- Put global filters in a top toolbar when a single set should affect the whole page.  
- Use tabs/sections with local forms when different chart groups need different filters.  
- Use expanders for chart-specific tweaks to keep the UI tidy.  
- Still follow the one-mask idea within each scope (global → section → chart).
"""
)
