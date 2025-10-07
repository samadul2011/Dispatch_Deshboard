import streamlit as st
import duckdb
import pandas as pd
from datetime import datetime, timedelta
import os
import urllib.request

# Page configuration
st.set_page_config(page_title="Orders vs Sales Difference", layout="wide")

if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()  # clears cache

col1, col2, col3 = st.columns([1, 2, 1])
with col3:
    st.image("https://raw.githubusercontent.com/samadul2011/Dispatch_Deshboard/main/AtyabLogo.png", width=200)

# Header
color = "Blue"
st.markdown(f"<h1 style='color: {color};'>📊 Orders vs Sales Difference Analysis</h1>", unsafe_allow_html=True)
st.markdown("Developed by :red[Samad Hoque]. Analyze the difference between Orders and Sales quantities over a selected date range.")

# Database configuration
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

con = get_connection()

# Get date range from the database
@st.cache_data
def get_date_range():
    query = """
    SELECT 
        MIN(CAST(Sales_Date AS DATE)) as min_date,
        MAX(CAST(Sales_Date AS DATE)) as max_date
    FROM (
        SELECT Sales_Date FROM Sales
        UNION ALL
        SELECT Sales_Date FROM Orders
    )
    """
    result = con.execute(query).fetchone()
    return result[0], result[1]

# Get all unique codes
@st.cache_data
def get_all_codes():
    query = """
    SELECT DISTINCT Code
    FROM (
        SELECT Code FROM Sales
        UNION
        SELECT Code FROM Orders
    )
    ORDER BY Code
    """
    result = con.execute(query).fetchdf()
    return result['Code'].tolist()

try:
    min_date, max_date = get_date_range()
    all_codes = get_all_codes()
    
    # Sidebar Filters
    st.sidebar.header("🔍 Filters")
    
    # Date range selector
    st.sidebar.subheader("📅 Date Range")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input(
            "From Date",
            value=max_date - timedelta(days=30) if max_date else datetime.now() - timedelta(days=30),
            min_value=min_date,
            max_value=max_date
        )
    
    with col2:
        end_date = st.date_input(
            "To Date",
            value=max_date if max_date else datetime.now(),
            min_value=min_date,
            max_value=max_date
        )
    
    # Validate date range
    if start_date > end_date:
        st.error("⚠️ Error: 'From Date' must be before 'To Date'")
        st.stop()
    
    # Code filter
    st.sidebar.subheader("🔖 Product Code")
    
    filter_option = st.sidebar.radio(
        "Filter Type:",
        ["All Codes", "Search Code", "Select Multiple Codes"],
        index=0
    )
    
    selected_codes = []
    
    if filter_option == "Search Code":
        search_code = st.sidebar.text_input(
            "Search for Code:",
            placeholder="Enter product code..."
        )
        if search_code:
            # Filter codes that contain the search term
            matching_codes = [code for code in all_codes if search_code.upper() in str(code).upper()]
            if matching_codes:
                selected_codes = matching_codes
                st.sidebar.success(f"Found {len(matching_codes)} matching code(s)")
            else:
                st.sidebar.warning("No matching codes found")
    
    elif filter_option == "Select Multiple Codes":
        selected_codes = st.sidebar.multiselect(
            "Select Code(s):",
            options=all_codes,
            default=None
        )
    
    # Query data with date filter
    @st.cache_data
    def fetch_data(start, end):
        sales_query = f"""
        SELECT
            Code,
            CAST(Sales_Date AS DATE) AS Sales_Date,
            SUM(CAST(Qty AS INTEGER)) AS Total
        FROM Sales
        WHERE CAST(Sales_Date AS DATE) BETWEEN '{start}' AND '{end}'
        GROUP BY Code, Sales_Date
        """
        
        orders_query = f"""
        SELECT
            Code,
            CAST(Sales_Date AS DATE) AS Sales_Date,
            SUM(CAST(Qty AS INTEGER)) AS Total
        FROM Orders
        WHERE CAST(Sales_Date AS DATE) BETWEEN '{start}' AND '{end}'
        GROUP BY Code, Sales_Date
        """
        
        sales_df = con.execute(sales_query).fetchdf()
        orders_df = con.execute(orders_query).fetchdf()
        
        return sales_df, orders_df
    
    sales_df, orders_df = fetch_data(start_date, end_date)
    
    # FIX: Convert Code columns to string to ensure matching data types
    sales_df['Code'] = sales_df['Code'].astype(str)
    orders_df['Code'] = orders_df['Code'].astype(str)
    
    # Merge and calculate difference
    merged_df = orders_df.merge(
        sales_df,
        on=['Code', 'Sales_Date'],
        how='outer',
        suffixes=('_Orders', '_Sales')
    ).fillna(0)
    
    merged_df['Difference'] = merged_df['Total_Sales'] - merged_df['Total_Orders']
    
    # Apply code filter
    if filter_option != "All Codes" and selected_codes:
        # Convert selected_codes to string as well for comparison
        selected_codes_str = [str(code) for code in selected_codes]
        merged_df = merged_df[merged_df['Code'].isin(selected_codes_str)]
    
    merged_df = merged_df.sort_values(['Sales_Date', 'Code'], ascending=[False, True])
    
    # Display difference table
    display_df = merged_df[['Code', 'Sales_Date', 'Total_Orders', 'Total_Sales', 'Difference']].copy()
    display_df.columns = ['Code', 'Date', 'Orders Qty', 'Sales Qty', 'Difference']
    
    # Convert numeric columns to integers for cleaner display
    display_df['Orders Qty'] = display_df['Orders Qty'].astype(int)
    display_df['Sales Qty'] = display_df['Sales Qty'].astype(int)
    display_df['Difference'] = display_df['Difference'].astype(int)
    
    # Main content
    st.subheader("📊 Difference Analysis (Sales - Orders)")
    
    # Summary metrics with different colors
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Records", len(display_df))
    
    with col2:
        total_orders = display_df['Orders Qty'].sum()
        # Using orange color for Orders
        st.markdown(f"""
        <div style="text-align: center; padding: 10px; border-radius: 10px; background-color: #f0f2f6;">
            <div style="font-size: 14px; color: #666;">Total Orders Qty</div>
            <div style="font-size: 24px; font-weight: bold; color: #FF6B00;">{total_orders:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        total_sales = display_df['Sales Qty'].sum()
        # Using green color for Sales
        st.markdown(f"""
        <div style="text-align: center; padding: 10px; border-radius: 10px; background-color: #f0f2f6;">
            <div style="font-size: 14px; color: #666;">Total Sales Qty</div>
            <div style="font-size: 24px; font-weight: bold; color: #00AA00;">{total_sales:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        total_diff = display_df['Difference'].sum()
        # Determine color for difference (red for negative, green for positive)
        diff_color = "#FF4B4B" if total_diff < 0 else "#00AA00" if total_diff > 0 else "#666666"
        st.markdown(f"""
        <div style="text-align: center; padding: 10px; border-radius: 10px; background-color: #f0f2f6;">
            <div style="font-size: 14px; color: #666;">Total Difference</div>
            <div style="font-size: 24px; font-weight: bold; color: {diff_color};">{total_diff:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Display table with colored numbers
    st.dataframe(
        display_df,
        use_container_width=True,
        height=500,
        column_config={
            "Code": st.column_config.TextColumn("Code", width="medium"),
            "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
            "Orders Qty": st.column_config.NumberColumn("Orders Qty", format="%d"),
            "Sales Qty": st.column_config.NumberColumn("Sales Qty", format="%d"),
            "Difference": st.column_config.NumberColumn("Difference", format="%d"),
        }
    )
    
    # Additional statistics
    st.divider()
    st.subheader("📈 Summary Statistics")
    
    summary_col1, summary_col2, summary_col3 = st.columns(3)
    
    with summary_col1:
        st.metric("Unique Products", display_df['Code'].nunique())
    
    with summary_col2:
        fulfillment_rate = (total_sales / total_orders * 100) if total_orders > 0 else 0
        # Color based on fulfillment rate
        rate_color = "#FF4B4B" if fulfillment_rate < 80 else "#FF6B00" if fulfillment_rate < 100 else "#00AA00"
        st.markdown(f"""
        <div style="text-align: center; padding: 10px; border-radius: 10px; background-color: #f0f2f6;">
            <div style="font-size: 14px; color: #666;">Fulfillment Rate</div>
            <div style="font-size: 24px; font-weight: bold; color: {rate_color};">{fulfillment_rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with summary_col3:
        st.metric("Date Range (Days)", (end_date - start_date).days + 1)
    
    # Download option
    st.divider()
    difference_csv = display_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Difference Data (CSV)",
        data=difference_csv,
        file_name=f"difference_{start_date}_{end_date}.csv",
        mime="text/csv"
    )

except Exception as e:
    st.error(f"❌ Error: {str(e)}")
    st.info("Please ensure the database file exists and contains the required tables (Orders and Sales).")
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
