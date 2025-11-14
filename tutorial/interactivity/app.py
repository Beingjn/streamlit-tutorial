# Lab 5 — Formatting & Interactivity
# How to start this app
#
# 1) Install required libraries:
#       pip install streamlit pandas numpy altair
#
# 2) Run the app
#    - Start the app from the project folder(in terminal):
#        streamlit run lab5_home.py
#    - Your browser should open to:
#        http://localhost:8501
#      (If it doesn’t, copy that URL into your browser.)
#    - Stop the app: press Ctrl+C in the terminal.

import streamlit as st
from datetime import date, timedelta

st.set_page_config(
    page_title="Lab 5 — Formatting & Interactivity",
    page_icon="5️⃣",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Title & Overview
st.title("Lab 5 — Formatting & Interactivity")

st.markdown(
"""
Welcome! In this lab we'll explore these topics:

1. **Formatting** — titles, labels, scales, legends, colors, layout
2. **Linked Charts using Concats** — build views with horizontal (`|`) and vertical (`&`) concatenation
3. **Page-wide linking** — share one selection state across multiple charts/sections so all views respond together

"""

)


# Navigate to Pages
st.header("Pages")

st.page_link("pages/1_Formatting.py",   label="1\\. Formatting")
st.page_link("pages/2_Interactivity.py", label="2\\. Interactivity")


