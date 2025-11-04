# How to start this app
# Start the app from the project folder(in terminal):
#   streamlit run app.py
# Your browser should open to:
#   http://localhost:8501
#   (If it doesn’t, copy that URL into your browser.)
# Stop the app: press Ctrl+C in the terminal.

import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Secrets & Connecting Data")
st.title("Secrets & Connecting Data")

st.markdown("""
This tutorial covers reading a public Google Sheet with `st.connection(...)`.
`st.connection` supports a broad range of databases and data services (SQL engines, data warehouses, spreadsheets, cloud storage, and more). 
This tutorial focuses on a single, minimal example: **connecting to a public Google Sheet, with configuration kept in secrets**.\n
Examples connecting to other data sources can be found here: https://docs.streamlit.io/develop/tutorials/databases

""")

st.sidebar.header("Setup checklist")
st.sidebar.markdown(
    """
    1. Create a public Google Sheet (Anyone with the link).  
    2. Copy the share URL.  
    3. Put it in `.streamlit/secrets.toml`.  
    4. Run the demo below.
    """
)

st.sidebar.divider()
st.sidebar.subheader("Why use secrets for a public sheet?")
st.sidebar.write(
    "It's a good practice to put the URL in `secrets` to keeps it out of your code. The same setup is essential when real credentials enter the picture."
)


st.markdown(
    """
    ### What are Secrets?
    - Secrets are key–value settings your app reads at runtime via `st.secrets`.
    - They live outside your code (local: `.streamlit/secrets.toml`; Cloud: *Settings → Advanced → Secrets*).
    - Same code works locally and on Cloud.

    **Examples of things to keep in secrets**
    - A public Google Sheet URL (this tutorial)
    - Database credentials
    - API tokens and webhooks

    **Sample `secrets.toml`**
    ```toml
    [connections.gsheets]
    spreadsheet = "https://docs.google.com/spreadsheets/d/XXXX/edit#gid=0"

    [connections.postgres]
    dialect = "postgresql"
    host = "db.example.net"
    port = 5432
    database = "analytics"
    username = "streamlit_user"
    password = "12345678"

    [api]
    stripe_key = "sk_live_...redacted..."
    openai_key = "sk-..."
    ```

    **Using them in code**
    ```python
    sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    db_user  = st.secrets["connections"]["postgres"]["username"]
    stripe   = st.secrets["api"]["stripe_key"]
    ```
    """
)

st.divider()

st.subheader("Local setup")
st.write("Secrets lives locally in .streamlit/secrets.toml")
st.code(
    """
[connections.gsheets]
# Share link with "Anyone with the link"
spreadsheet = "https://docs.google.com/spreadsheets/d/XXXXXXXXXXXXXXXXXXXXXXXXXXXX/edit#gid=0" """,
    language="toml",
)

st.info("""If you're pushing this project to GitHub (for Streamlit Community Cloud), keep your secrets local and out of the repo.
Add this line to a file named `.gitignore` so Git skips it:

```
.streamlit/secrets.toml
```

This prevents share links or keys from becoming public.
""")

st.subheader("Community Cloud: how secrets/credentials work")
st.markdown("""On Streamlit Community Cloud, secrets live with your app.

1. Open your app → **Settings → Advanced → Secrets**.  
2. Paste the same TOML used locally, for example:

   ```toml
   [connections.gsheets]
   spreadsheet = "https://docs.google.com/spreadsheets/d/XXXXXXXXXXXXXXXXXXXXXXXXXXXX/edit#gid=0"
   ```

3. Click **Save**. Values are stored securely and are available at runtime via `st.secrets[...]`.  
4. Code stays identical locally and on Cloud—no code changes when moving between environments.

You can update secrets anytime; the next run picks up the changes.
""")
st.caption("Community Cloud will be covered in a futrue tutorial.")

st.divider()
st.markdown(
    """
    ### `st.connection`: How we connect data in this example
    `st.connection(name, type=...)` creates a reusable connection object that reads settings from `secrets.toml` 
    and provides simple methods like `.query(...)` or `.read(...)`. \n
    Detailed information: https://docs.streamlit.io/develop/api-reference/connections/st.connection
    """
)

st.divider()

st.subheader("Demo: read a public Google Sheet via secrets")
st.markdown(
    """
    Edit `.streamlit/secrets.toml` to add your own Google sheet link.\n
    This example reads the first worksheet by default; optionally specify a worksheet name.
    """
)

cfg = st.secrets.get("connections", {}).get("gsheets", {})
if "spreadsheet" not in cfg:
    st.info(
        "Add your Google Sheet URL to secrets at:\n\n"
        "[connections.gsheets]\n"
        'spreadsheet = "https://docs.google.com/spreadsheets/d/XXXXXXXXXXXX/edit#gid=0"'
    )
    st.stop()

# Connection
conn = st.connection("gsheets", type=GSheetsConnection)

# Worksheet selector
worksheet = st.text_input("Worksheet name (optional)", placeholder="e.g., Sheet1")

# Read default sheet or a named worksheet
try:
    df = conn.read(worksheet=worksheet.strip()) if worksheet.strip() else conn.read()
except Exception as e:
    st.error(f"Could not read the Google Sheet: {e}")
    st.stop()

# Display and export
st.dataframe(df, use_container_width=True)
st.download_button("Download as CSV", df.to_csv(index=False), "sheet_data.csv", "text/csv")

st.write("Mininal pattern:")
st.code(
    """
    import streamlit as st
    import pandas as pd
    from streamlit_gsheets import GSheetsConnection

    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read()
    st.dataframe(df)
    """
)
st.markdown("""
    `st.connection` handles secrets retrieval, setup, query caching and retries.\n
    You can pass optional parameters to `.read()` to customize your connection. For example:
"""
)
st.code("""
    df = conn.read(
    worksheet="Sheet1", # Selecting sheet
    ttl="10m",  # Set cache refreshing time
    usecols=[0, 1], # pick columns
    nrows=3,    # limit rows
    # Other pandas.read_csv parameters are supported
)
"""
)