# How to start this app
# Start the app from the project folder(in terminal):
#   streamlit run app.py
# Your browser should open to:
#   http://localhost:8501
#   (If it doesn’t, copy that URL into your browser.)
# Stop the app: press Ctrl+C in the terminal.

import streamlit as st


intro = st.Page("pages/1_intro_to_Filters.py", title="Intro to Filters")
form  = st.Page("pages/2_form_based_filters.py", title="Form-Based Filters")
patterns = st.Page("pages/3_filter_placement_patterns.py", title="Filter Placement Patterns")

st.navigation([intro, form, patterns]).run()

