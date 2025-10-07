import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import os

# Page configuration
st.set_page_config(page_title="Sales Dashboard", layout="wide")

st.title("📊 Sales Dashboard")

# Connect to DuckDB
@st.cache_resource
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
con = get_connection()
# If the file doesn't exist yet, DuckDB will create it on first write:
# con.execute("CREATE TABLE IF NOT EXISTS your_table (...)")

# Get date range from data
@st.cache_data
def get_date_range():
    query = "SELECT MIN(CAST(Sales_Date AS DATE)) as min_date, MAX(CAST(Sales_Date AS DATE)) as max_date FROM Sales"
    result = con.execute(query).fetchone()
    return result[0], result[1]

try:
    min_date, max_date = get_date_range()
except Exception as e:
    st.error(f"Error connecting to database: {e}")
    st.stop()

# Sidebar filters
st.sidebar.header("Filters")

# Date range selector
col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input(
        "Start Date",
        value=max_date - timedelta(days=30) if max_date else datetime.now() - timedelta(days=30),
        min_value=min_date,
        max_value=max_date
    )

with col2:
    end_date = st.date_input(
        "End Date",
        value=max_date if max_date else datetime.now(),
        min_value=min_date,
        max_value=max_date
    )

# Search box for Code
search_code = st.sidebar.text_input("🔍 Search Code", "")

# Fetch data based on filters
@st.cache_data
def load_data(start, end, search=""):
    search_condition = f"AND Code LIKE '%{search}%'" if search else ""
    
    query = f"""
        SELECT 
            Code,
            CAST(Sales_Date AS DATE) AS Sales_Date,
            SUM(CAST(Qty AS INTEGER)) AS Qty
        FROM Sales
        WHERE CAST(Sales_Date AS DATE) BETWEEN '{start}' AND '{end}'
        {search_condition}
        GROUP BY Code, Sales_Date
        ORDER BY Sales_Date DESC, Code
    """
    return con.execute(query).df()

# Load data
try:
    df = load_data(start_date, end_date, search_code)
    
    if df.empty:
        st.warning("No data found for the selected filters.")
        st.stop()
    
    # Summary metrics
    st.subheader("📈 Summary Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    total_qty = df['Qty'].sum()
    unique_codes = df['Code'].nunique()
    date_range_days = (end_date - start_date).days + 1
    avg_daily_qty = total_qty / date_range_days if date_range_days > 0 else 0
    
    col1.metric("Total Quantity", f"{total_qty:,.0f}")
    col2.metric("Unique Codes", f"{unique_codes:,}")
    col3.metric("Date Range", f"{date_range_days} days")
    col4.metric("Avg Daily Qty", f"{avg_daily_qty:,.0f}")
    
    # Top 20 Codes Chart
    st.subheader("📊 Top 20 Products by Quantity")
    
    top_20 = df.groupby('Code')['Qty'].sum().sort_values(ascending=False).head(20).reset_index()
    
    fig = px.bar(
        top_20,
        x='Code',
        y='Qty',
        title='Top 20 Products by Total Quantity',
        labels={'Qty': 'Total Quantity', 'Code': 'Product Code'},
        color='Qty',
        color_continuous_scale='Blues'
    )
    fig.update_layout(
        xaxis_tickangle=-45,
        height=500,
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Sales trend over time
    st.subheader("📅 Sales Trend Over Time")
    
    daily_sales = df.groupby('Sales_Date')['Qty'].sum().reset_index()
    
    fig2 = px.line(
        daily_sales,
        x='Sales_Date',
        y='Qty',
        title='Daily Sales Quantity Trend',
        labels={'Qty': 'Total Quantity', 'Sales_Date': 'Date'},
        markers=True
    )
    fig2.update_layout(height=400)
    st.plotly_chart(fig2, use_container_width=True)
    
    # Detailed data table
    st.subheader("📋 Detailed Sales Data")
    
    # Group by Code for summary view
    summary_df = df.groupby('Code').agg({
        'Qty': 'sum',
        'Sales_Date': ['min', 'max', 'count']
    }).reset_index()
    
    summary_df.columns = ['Code', 'Total_Qty', 'First_Date', 'Last_Date', 'Transaction_Count']
    summary_df = summary_df.sort_values('Total_Qty', ascending=False)
    
    # Convert datetime to date only
    summary_df['First_Date'] = pd.to_datetime(summary_df['First_Date']).dt.date
    summary_df['Last_Date'] = pd.to_datetime(summary_df['Last_Date']).dt.date
    
    # Display options
    view_option = st.radio("View:", ["Summary by Code", "Detailed Transactions"], horizontal=True)
    
    if view_option == "Summary by Code":
        st.dataframe(
            summary_df.style.format({
                'Total_Qty': '{:,.0f}',
                'Transaction_Count': '{:.0f}'
            }),
            use_container_width=True,
            height=400
        )
        
        # Download button
        csv = summary_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Summary as CSV",
            data=csv,
            file_name=f"sales_summary_{start_date}_{end_date}.csv",
            mime="text/csv"
        )
    else:
        st.dataframe(
            df.style.format({'Qty': '{:,.0f}'}),
            use_container_width=True,
            height=400
        )
        
        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Details as CSV",
            data=csv,
            file_name=f"sales_details_{start_date}_{end_date}.csv",
            mime="text/csv"
        )

except Exception as e:
    st.error(f"Error loading data: {e}")
    st.info("Please check your database connection and query.")

# Footer
st.sidebar.markdown("---")

st.sidebar.info(f"Data range: {min_date} to {max_date}")

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

