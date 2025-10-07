import streamlit as st
import duckdb
import pandas as pd
from datetime import date
import os

col1, col2, col3 = st.columns([1, 2, 1])
with col3:
    st.image("https://github.com/samadul2011/Dispatch_Deshboard/blob/main/AtyabLogo.png", width=200)

with col2:
    st.color = "red"
    st.markdown(f"<h1 style='color: {st.color};'>Dispatched Details</h1>", unsafe_allow_html=True)
    #st.set_page_config(page_title="Dispatched Note", layout="wide")
    st.subheader("Developed by :red[Samadul Hoque]")

# ---- PAGE CONFIG ----
#st.set_page_config(page_title="Sales Viewer", layout="wide")

st.title("🔍 Sales Data Viewer")

# ---- DATABASE PATH ----
#DB_PATH = r"D:\OneDriveBackUp\Dispatch\disptach.duckdb"
def get_connection():
    # Option 1: Relative to the repo root (simplest, assumes DB file is in root)
    db_filename = "disptach.duckdb"  # Fix typo to "dispatch.duckdb" if needed
    db_path = os.path.join(os.getcwd(), db_filename)  # Full path from current working dir
    
    # Option 2: Relative to the script's directory (if DB is in a subfolder)
    # db_path = os.path.join(os.path.dirname(__file__), "..", db_filename)  # e.g., if script is in /pages/
    
    # Ensure the file exists or create it (DuckDB auto-creates on connect if writable)
    if not os.path.exists(db_path):
        print(f"Warning: DB file not found at {db_path}. Creating a new one...")
    
    return duckdb.connect(db_path)

# Load and prepare data

DB_PATH =et_connection()
# ---- CACHED CONNECTION ----
@st.cache_resource
def get_connection():
    """Keep a single DuckDB connection alive for the Streamlit session."""
    con = duckdb.connect(DB_PATH)
    return con

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
    df_default = con.execute("""
        SELECT Code, Qty, Sales_Date, Route, Description 
        FROM ProductsWithCode 
        ORDER BY CAST(Sales_Date AS DATE) DESC 
        LIMIT 10
    """).fetchdf()
    st.dataframe(df_default, use_container_width=True)
except Exception as e:
    st.error(f"Error loading preview: {e}")
