import os
import requests
import duckdb
import streamlit as st
import pandas as pd  # Missing import

@st.cache_resource
def get_duckdb():
    db_filename = "dispatch.duckdb"
    # Direct download link from Google Drive
    url = "https://drive.google.com/uc?export=download&id=1tYt3Z5McuQYifmNImZyACPHW9C9ju7L4"

    if not os.path.exists(db_filename):
        st.write("Downloading database from Google Drive...")
        resp = requests.get(url, allow_redirects=True)
        if resp.status_code != 200:
            st.error(f"Failed to download database. Status code = {resp.status_code}")
            st.stop()
        with open(db_filename, "wb") as f:
            f.write(resp.content)

    return duckdb.connect(db_filename)

# Get connection
con = get_duckdb()
st.success("Connected to DuckDB!")

# Page configuration
st.markdown("<h1 style='color: red;'>Dispatched Note</h1>", unsafe_allow_html=True)
st.subheader("Developed by :green[Samadul Hoque]")

# Load and prepare data
@st.cache_data
def load_data():
    # Create the joined table
    con.execute("""
        CREATE OR REPLACE TABLE SalesWithSupervisors AS
        SELECT 
            s.Code,
            s.Qty,
            s.Sales_Date,
            s.Route,
            sup.Supervisor AS SupervisorName
        FROM Sales s
        INNER JOIN Supervisors sup ON s.Route = sup.Route;
    """)
    
    # Fetch all data
    df = con.execute("SELECT * FROM SalesWithSupervisors;").fetchdf()
    return df

# Get unique values for filters
@st.cache_data
def get_filter_values(df):
    supervisors = sorted(df['SupervisorName'].unique().tolist())
    # Convert dates to datetime for proper date handling
    df['Sales_Date'] = pd.to_datetime(df['Sales_Date'], errors='coerce')
    dates = df['Sales_Date'].dropna().unique()
    return supervisors, dates

# Main app
st.markdown("---")

# Load data
try:
    df = load_data()
    supervisors, dates = get_filter_values(df)
    
    # Sidebar filters
    st.sidebar.header("🔍 Filters")
    
    # Supervisor filter
    selected_supervisor = st.sidebar.selectbox(
        "Select Supervisor:",
        options=["All"] + supervisors,
        index=0
    )
    
    # Sales Date filter - Calendar type
    date_filter_type = st.sidebar.radio(
        "Date Filter Type:",
        options=["All Dates", "Single Date", "Date Range"],
        index=0
    )
    
    selected_dates = None
    if date_filter_type == "Single Date":
        # Convert numpy datetime64 to Python datetime for date_input
        min_date = pd.to_datetime(dates.min()).date() if len(dates) > 0 else None
        max_date = pd.to_datetime(dates.max()).date() if len(dates) > 0 else None
        default_date = max_date if max_date else None
        
        selected_date = st.sidebar.date_input(
            "Select Sales Date:",
            value=default_date,
            min_value=min_date,
            max_value=max_date
        )
        selected_dates = [pd.Timestamp(selected_date)]
    elif date_filter_type == "Date Range":
        # Convert numpy datetime64 to Python datetime for date_input
        min_date = pd.to_datetime(dates.min()).date() if len(dates) > 0 else None
        max_date = pd.to_datetime(dates.max()).date() if len(dates) > 0 else None
        default_start = min_date if min_date else None
        default_end = max_date if max_date else None
        
        date_range = st.sidebar.date_input(
            "Select Date Range:",
            value=(default_start, default_end) if default_start and default_end else None,
            min_value=min_date,
            max_value=max_date
        )
        if len(date_range) == 2:
            selected_dates = pd.date_range(start=date_range[0], end=date_range[1])
    
    # Apply filters
    filtered_df = df.copy()
    filtered_df['Sales_Date'] = pd.to_datetime(filtered_df['Sales_Date'], errors='coerce')
    
    if selected_supervisor != "All":
        filtered_df = filtered_df[filtered_df['SupervisorName'] == selected_supervisor]
    
    if date_filter_type != "All Dates" and selected_dates is not None:
        if date_filter_type == "Single Date":
            filtered_df = filtered_df[filtered_df['Sales_Date'].dt.date == selected_dates[0].date()]
        else:  # Date Range
            filtered_df = filtered_df[
                (filtered_df['Sales_Date'].dt.date >= selected_dates[0].date()) & 
                (filtered_df['Sales_Date'].dt.date <= selected_dates[-1].date())
            ]
    
    # Display filter summary
    st.sidebar.markdown("---")
    st.sidebar.metric("Total Records", len(filtered_df))
    
    # Create pivot table
    if len(filtered_df) > 0:
        # Ensure Qty is numeric, convert if needed
        filtered_df['Qty'] = pd.to_numeric(filtered_df['Qty'], errors='coerce').fillna(0)
        
        pivot_table = filtered_df.pivot_table(
            index='Code',
            columns='Route',
            values='Qty',
            aggfunc='sum',
            fill_value=0
        )
        
        # Add Total column
        pivot_table['Total'] = pivot_table.sum(axis=1)
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_qty = filtered_df['Qty'].sum()
            st.metric("Total Quantity", f"{total_qty:,.0f}")
        with col2:
            st.metric("Unique Codes", len(pivot_table.index))
        with col3:
            st.metric("Unique Routes", len(pivot_table.columns) - 1)  # Subtract 1 for Total column
        with col4:
            avg_qty = filtered_df['Qty'].mean()
            st.metric("Avg Qty per Code", f"{avg_qty:,.1f}")
        
        st.markdown("---")
        
        # Display pivot table
        st.subheader("📈 Pivot Table: Code (Rows) × Route (Columns)")
        
        # Display the pivot table with basic styling
        st.dataframe(pivot_table, use_container_width=True, height=600)
        
        # Download button
        st.markdown("---")
        csv = pivot_table.to_csv()
        filename_date = selected_dates[0].strftime('%Y%m%d') if date_filter_type == "Single Date" and selected_dates else "all_dates"
        supervisor_name = selected_supervisor.replace(" ", "_") if selected_supervisor != "All" else "all_supervisors"
        st.download_button(
            label="📥 Download Pivot Table as CSV",
            data=csv,
            file_name=f"sales_pivot_{supervisor_name}_{filename_date}.csv",
            mime="text/csv"
        )
        
        # Show raw filtered data
        with st.expander("🔍 View Filtered Raw Data"):
            st.dataframe(filtered_df, use_container_width=True)
    else:
        st.warning("⚠️ No data available for the selected filters.")
        
except Exception as e:
    st.error(f"❌ Error loading data: {str(e)}")
    st.info("Please ensure the DuckDB file path is correct and the database contains the required tables (Sales and Supervisors).")

# Footer
st.markdown("---")

st.markdown("*Sales Pivot Dashboard - Built with Streamlit & DuckDB*")
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










