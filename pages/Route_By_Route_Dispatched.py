import streamlit as st
import duckdb
import pandas as pd
from datetime import date
import os

col1, col2, col3 = st.columns([1, 2, 1])
with col3:
    st.image("https://raw.githubusercontent.com/samadul2011/Dispatch_Deshboard/main/AtyabLogo.png", width=200)

with col2:
    st.markdown("<h1 style='color: red;'>Dispatched Details</h1>", unsafe_allow_html=True)
    st.subheader("Developed by :red[Samadul Hoque]")

st.title("🔍 Sales Data Viewer")

# ---- DATABASE PATH ----
# Adjust this if your DB is not in the repo root (e.g., add a subfolder like "data/")
db_filename = "dispatch.duckdb"  # Fixed typo
DB_PATH = os.path.join(os.path.dirname(__file__), "..", db_filename)  # Relative to repo root (handles /pages/ structure)

# Ensure the file exists or create it (DuckDB auto-creates on connect if writable)
if not os.path.exists(DB_PATH):
    print(f"Warning: DB file not found at {DB_PATH}. Creating a new one...")

# ---- CACHED CONNECTION ----
@st.cache_resource
def get_connection():
    """Keep a single DuckDB connection alive for the Streamlit session."""
    return duckdb.connect(DB_PATH)

# ---- CREATE TABLE (if not exists) ----
def ensure_join_table(con):
    """Create or replace ProductsWithCode if it doesn't exist."""
    con.execute("""
        CREATE OR REPLACE TABLE ProductsWithCode AS
        SELECT 
            s.Code,
            s.Qty,
            s.Sales_Date,
            s.Route,
            p.Description AS Description
        FROM Sales s
        INNER JOIN Products p
            ON s.Code = p.Code;
    """)

# ---- LOAD FILTERED DATA ----
@st.cache_data
def load_data(start_date=None, end_date=None, code_filter=None):
    """Load filtered data safely."""
    con = get_connection()
    ensure_join_table(con)

    query = """
        SELECT 
            Code,
            Description,
            Qty,
            Route,
            Sales_Date
        FROM ProductsWithCode
        WHERE 1=1
    """
    params = []

    if start_date and end_date:
        query += " AND CAST(Sales_Date AS DATE) BETWEEN ? AND ?"
        params += [str(start_date), str(end_date)]

    if code_filter:
        query += " AND LOWER(Code) LIKE LOWER(?)"
        params.append(f"%{code_filter}%")

    query += " ORDER BY CAST(Sales_Date AS DATE) DESC"

    return con.execute(query, params).fetchdf()

# ---- SIDEBAR FILTERS ----
st.sidebar.header("Filter Options")

col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input("Start Date", value=date(2025, 1, 1))
with col2:
    end_date = st.date_input("End Date", value=date.today())

code_filter = st.sidebar.text_input("Search Code")

# ---- FETCH DATA ----
df = load_data(start_date, end_date, code_filter)

# ---- DISPLAY DATA ----
st.subheader("Filtered Results")
st.write(f"Records found: {len(df)}")

if not df.empty:
    st.dataframe(df, use_container_width=True)
else:
    st.info("No records found for the selected filters.")

# ---- DOWNLOAD OPTION ----
if not df.empty:
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download CSV",
        data=csv,
        file_name="filtered_sales.csv",
        mime="text/csv",
    )

# ---- DEFAULT PREVIEW (optional) ----
st.divider()
st.subheader("🔸 Latest 10 Records")
try:
    con = get_connection()
    ensure_join_table(con)  # Ensure table exists for preview too
    df_default = con.execute("""
        SELECT Code, Qty, Sales_Date, Route, Description 
        FROM ProductsWithCode 
        ORDER BY CAST(Sales_Date AS DATE) DESC 
        LIMIT 10
    """).fetchdf()
    st.dataframe(df_default, use_container_width=True)
except Exception as e:
    st.error(f"Error loading preview: {e}")
