import streamlit as st
import duckdb
import pandas as pd
from datetime import datetime, timedelta
import os


if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()  # clears cache

# Page configuration
st.set_page_config(page_title="Orders vs Sales Difference", layout="wide")
color="Blue"
st.markdown(f"<h1 style='color: {color};'>📊 Orders vs Sales Difference Analysis</h1>", unsafe_allow_html=True)
#st.title("📊 Orders vs Sales Difference Analysis")

# Database connection
@st.cache_resource
#def get_connection():
    #return duckdb.connect("/workspaces/Dispatch_Deshboard/disptach.duckdb")
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
        merged_df = merged_df[merged_df['Code'].isin(selected_codes)]
    
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
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Records", len(display_df))
    
    with col2:
        total_orders = display_df['Orders Qty'].sum()
        st.metric("Total Orders Qty", f"{total_orders:,}")
    
    with col3:
        total_sales = display_df['Sales Qty'].sum()
        st.metric("Total Sales Qty", f"{total_sales:,}")
    
    with col4:
        total_diff = display_df['Difference'].sum()
        st.metric(
            "Total Difference", 
            f"{total_diff:,}",
            delta=f"{total_diff:,}",
            delta_color="normal"
        )
    
    st.divider()
    
    # Display table
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
        st.metric("Fulfillment Rate", f"{fulfillment_rate:.1f}%")
    
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

