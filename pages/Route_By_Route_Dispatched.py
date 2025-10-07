import streamlit as st
import duckdb
import pandas as pd
from datetime import date
import urllib.request
import os

col1, col2, col3 = st.columns([1, 2, 1])
with col3:
    st.image("https://raw.githubusercontent.com/samadul2011/Dispatch_Deshboard/main/AtyabLogo.png", width=200)

with col2:
    st.color = "red"
    st.markdown(f"<h1 style='color: {st.color};'>Dispatched Details</h1>", unsafe_allow_html=True)
    st.subheader("Developed by :red[Samadul Hoque]")

st.title("🔍 Sales Data Viewer")

# ---- DATABASE PATH ---- 
# GitHub raw content URL for the database file
GITHUB_DB_URL = "https://raw.githubusercontent.com/samadul2011/Dispatch_Deshboard/main/disptach.duckdb"
LOCAL_DB_PATH = "disptach.duckdb"

# ---- DOWNLOAD DATABASE FROM GITHUB ----
@st.cache_resource
def download_database():
    """Download database from GitHub if not already present."""
    if not os.path.exists(LOCAL_DB_PATH):
        with st.spinner("Downloading database from GitHub..."):
            try:
                urllib.request.urlretrieve(GITHUB_DB_URL, LOCAL_DB_PATH)
                st.success("Database downloaded successfully!")
            except Exception as e:
                st.error(f"Error downloading database: {e}")
                return None
    return LOCAL_DB_PATH

# Download the database
DB_PATH = download_database()

# ---- CACHED CONNECTION ----
@st.cache_resource
def get_connection():
    """Keep a single DuckDB connection alive for the Streamlit session."""
    if DB_PATH:
        con = duckdb.connect(DB_PATH)
        return con
    return None

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
    if not con:
        return pd.DataFrame()
    
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
    if con:
        df_default = con.execute("""
            SELECT Code, Qty, Sales_Date, Route, Description 
            FROM ProductsWithCode 
            ORDER BY CAST(Sales_Date AS DATE) DESC 
            LIMIT 10
        """).fetchdf()
        st.dataframe(df_default, use_container_width=True)
except Exception as e:
    st.error(f"Error loading preview: {e}")
# Sidebar Navigation - WITH ACTUAL PAGE SWITCHING
st.sidebar.title("🌐 Navigation")
st.sidebar.markdown("### Select a Dashboard Page")

# Define page configurations
page_configs = {
    "🏠 Home": "Home_Page",
    "📝 Dispatched Note": "Dispatched_Note", 
    "🛣️ Route By Route Dispatch": "Route_By_Route_Dispatched",
    "📊 Sales vs Orders": "Sales_Vs_Orders",
    "☀️ Sunburst Chart": "Sun_Brust",
    "👨‍💼 Supervisor Wise Products": "Supervisor_Wise_Products",
    "🏆 Top Items By Dispatch": "Top_Items_By_Dispatch",
    "📦 Top Products By Category": "Top_Products_By_Categore",
    "📈 Total Dispatched Chart": "Total_Dispatched_Chat"
}

page_descriptions = {
    "🏠 Home": "Dashboard overview and main menu",
    "📝 Dispatched Note": "View and manage dispatch notes",
    "🛣️ Route By Route Dispatch": "Route-wise dispatch analysis", 
    "📊 Sales vs Orders": "Compare sales and orders data",
    "☀️ Sunburst Chart": "Interactive hierarchical data visualization",
    "👨‍💼 Supervisor Wise Products": "Product analysis by supervisor",
    "🏆 Top Items By Dispatch": "Top dispatched items ranking",
    "📦 Top Products By Category": "Category-wise product performance", 
    "📈 Total Dispatched Chart": "Overall dispatch trends and charts"
}

# Initialize session state for current page
if 'current_page' not in st.session_state:
    st.session_state.current_page = "🏠 Home"

# Simple navigation using radio buttons with actual page switching
st.sidebar.markdown("### 📋 Available Pages")
selected_page = st.sidebar.radio(
    "Choose a page:",
    options=list(page_configs.keys()),
    index=list(page_configs.keys()).index(st.session_state.current_page) if st.session_state.current_page in page_configs.keys() else 0,
    key="page_navigation"
)

# Show page description
if selected_page in page_descriptions:
    st.sidebar.info(f"**{selected_page}**\n\n{page_descriptions[selected_page]}")

# Actually navigate to the selected page if it's different from current
if selected_page != st.session_state.current_page:
    st.session_state.current_page = selected_page
    # Switch to the selected page
    if selected_page == "🏠 Home":
        # Navigate to home page (main app file)
        st.switch_page("Home_Page.py")
    else:
        page_file = f"pages/{page_configs[selected_page]}.py"
        try:
            st.switch_page(page_file)
        except Exception as e:
            st.error(f"Could not navigate to {selected_page}. Error: {str(e)}")
            st.info(f"Please ensure the file exists at: {page_file}")

# Manual navigation instructions
st.sidebar.markdown("---")
st.sidebar.markdown("### 🚀 How to Navigate")
st.sidebar.markdown("""
To navigate between pages:
1. Select a page from the list above (automatically navigates)
2. Or use the Streamlit built-in sidebar menu
3. Pages update automatically when selected
""")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔧 Quick Actions")
if st.sidebar.button("🔄 Refresh All Data"):
    st.cache_data.clear()
    st.success("Data refreshed successfully!")

st.sidebar.markdown("### 📞 Support")
st.sidebar.info("For technical support or feature requests, please contact the Dispatch Supervisor.")
