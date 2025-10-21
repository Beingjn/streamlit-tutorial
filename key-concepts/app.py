# How to start this app
#
# Start the app from the project folder(in terminal):
#   streamlit run key_concepts.py
# Your browser should open to:
#   http://localhost:8501
#   (If it doesn’t, copy that URL into your browser.)
# Stop the app: press Ctrl+C in the terminal.

import streamlit as st
from datetime import datetime

# Page config
st.set_page_config(page_title="Key Concepts")

st.title("Key Concepts")
st.header("How Streamlit runs your app")

st.markdown("""
Streamlit apps have a client-server structure. The Python backend of your app is the server. 
The frontend you view through a browser is the client. When you develop an app locally, your computer runs both the server and the client. 
If someone views your app across a local or global network, the server and client run on different machines.
"""
)


st.divider()

st.markdown("## How Streamlit reruns your script")

st.markdown("""
Streamlit is reactive. Your script runs top to bottom to produce the current page.
When something the page depends on changes, most often a widget value, Streamlit reruns the
script from the start to render an updated view.
""")

st.subheader("What triggers a rerun")
st.markdown("""
- **Widget changes:** Sliders, selects, text inputs, and other widgets rerun the script as soon as their value changes.  
- **Forms:** Inputs inside a form are buffered; the script reruns once when the **Submit** button is pressed. This is useful for batching multiple fields and avoiding “recompute on every keystroke.”  
- **Programmatic rerun:** You can explicitly request a rerun after clearing state or finishing a step (`st.rerun()`).  
- **Lifecycle events:** Refreshing the page, editing the script, or restarting the server also produces a fresh run.  
- **Data and files:** Uploading a file or changing a data source that your script reads can lead to a rerun on the next execution.
""")

# runs so far readout
if "run_count" not in st.session_state:
    st.session_state.run_count = 0
st.session_state.run_count += 1
st.write(f"*Reruns this session:* **{st.session_state.run_count}** • Time: {datetime.now().strftime('%H:%M:%S')}")

cols = st.columns([2, 1])
with cols[1]:
    st.metric("Script reruns (this session)", st.session_state.run_count)
    st.caption(
        "Every time a widget value changes (outside a form), "
        "Streamlit reruns the whole script. Session state is your memory."
    )

with cols[0]:
    st.subheader("A) Instant reruns (full script rerun when widget changes)")
    instant_val = st.slider(
        "Move the slider, notice run counter increment",
        0, 100, 30, key="rerun_instant_slider"
    )
    st.write(f"Current value: {instant_val}")

    st.divider()

    st.subheader("B) Deferred reruns with forms")
    
    # Add A + B only when submitted
    with st.form("add_form"):
        a = st.number_input("A", value=0.0)
        b = st.number_input("B", value=0.0)
        submitted = st.form_submit_button("Add")

    if submitted:
        st.session_state["rerun_last_submit"] = datetime.now().strftime('%H:%M:%S')
        st.write("Sum:", a + b)

    st.markdown(
        """
        `st.form` lets you group multiple input widgets into a single “transaction” so the app doesn’t rerun on every 
        keystroke, nothing updates until the user clicks `st.form_submit_button`. This is perfect for filters and multi-field 
        inputs.
        """
    )
    st.caption(
        "We will cover form-based applications with greater detail in future tutorials."
    )

    st.divider()

    st.subheader("C) Manual reruns")
    if st.button("Manual rerun now", key="rerun_manual_button"):
        st.rerun()

    left, right = st.columns(2)
    with left:
        if st.button("Reset this section's state", key="rerun_reset_button"):
            for k in list(st.session_state.keys()):
                if k.startswith("rerun_") or k in {"run_count"}:
                    del st.session_state[k]
            st.toast("State cleared. Rerunning…")
            st.rerun()
    with right:
        st.write(
            "Last form submit:",
            st.session_state.get("rerun_last_submit", "—")
        )

st.divider()
st.markdown("## Session State, Caching and Fragments")
st.subheader("Sessions: per-user execution")
st.markdown("""
Each browser tab gets its own **session**. Reruns happen within that session only, so users don’t interfere
with each other. Local Python variables are recreated on every run; if you need values to survive reruns,
store them in a place designed for that (see **Session State** below).
""")

st.subheader("Managing work across reruns")
st.markdown("""
Reruns are by design, what you control is **how much work gets repeated** and **which parts of the page react**.
The features below don’t stop reruns; they shape *what* needs to happen during each run so the app stays fast
and predictable.
""")

st.markdown("### Session State (per-user memory)")
st.markdown("""
**`st.session_state`** is a small, persistent dictionary that lives for the duration of a user’s session.
Use it to remember choices, flags, and lightweight results so the
page doesn’t reset on every interaction. Session State keeps meaning steady while the script refreshes around it.\n
The rerun counter reads run_count from session state:
""")
st.code(
    'st.write(f"Reruns this session: {st.session_state.run_count}")'
)

with st.expander("What's inside of session state:"):
    if st.session_state:
        st.json({k: st.session_state[k] for k in sorted(st.session_state.keys())})
    else:
        st.caption("Empty — interact with the app to populate session_state.")

st.markdown("### Caching (skip repeated computation)")
st.markdown("""
- **`st.cache_data`** memoizes the return value of a *pure* function based on its inputs. Ideal for reading files,
  calling APIs, or deterministic transformations. On rerun, if inputs haven’t changed, the cached result is returned immediately.  
- **`st.cache_resource`** holds on to long-lived objects such as database clients or ML models across reruns (and often across sessions),
  so you don’t reconnect or reload on every frame.\n
Small example decorating a cached function:
""")
st.code(
    """
    @st.cache_data
    def load_big_dataset(param1, param2):
        return …
    """
)

# Fragment
st.markdown("### Fragments (isolate updates to a block)")
st.markdown("""
**Fragments** let you structure a page into independently updatable sections. When inputs inside a fragment change,
Streamlit can re-execute just that block and its dependencies, reducing flicker and unnecessary work on large pages.\n
When a user call a fragment function that contains a widget function, 
a fragment rerun is triggered instead of a full rerun when the user interact with that fragment's widget.
""")

@st.fragment
def fragment_function():
    frag_slider = st.slider(
        "Move the slider, notice run counter doens't change",
        0, 100, 30
    )

fragment_function()
st.write(f"*Reruns this session:* **{st.session_state.run_count}** • Time: {datetime.now().strftime('%H:%M:%S')}")

st.code(
    """
    @st.fragment
    def fragment_function():
        …
    """
)

st.caption("Upcoming tutorials cover Session State, caching, and fragments in more detail")

