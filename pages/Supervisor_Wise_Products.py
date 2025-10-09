import os
import streamlit as st
import pandas as pd
import duckdb
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import requests

# Page configuration
st.set_page_config(
    page_title="Sales Dashboard", 
    page_icon="📊", 
    layout="wide"
)

# ---- DATABASE CONNECTION (Same as your working code) ----
@st.cache_resource
def get_duckdb():
    db_filename = "dispatch.duckdb"
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

# Cache the data loading function
@st.cache_data
def load_data():
    """Load and merge sales data with supervisor information"""
    try:
        # Connect to DuckDB using the new connection method
        conn = get_duckdb()
        
        # Load Sales and Supervisor mapping
        sales = pd.read_sql("SELECT Code, Route, Sales_Date, Qty FROM Sales", conn)
        supervisors = pd.read_sql("SELECT Route, Supervisor FROM Supervisors", conn)
        
        # Merge Supervisor info
        df = sales.merge(supervisors, on="Route", how="left")
        
        # Convert Sales_Date to datetime
        df['Sales_Date'] = pd.to_datetime(df['Sales_Date'])
        
        # Convert Qty to numeric, handling any non-numeric values
        df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce')
        
        # Fill NaN values with 0
        df['Qty'] = df['Qty'].fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

# Main app
def main():
    st.title("📊 Sales Dashboard")
    st.markdown("---")
    
    # Load data
    df = load_data()
    
    if df is None:
        st.error("Unable to load data. Please check your database connection.")
        return
    
    # Sidebar filters
    st.sidebar.header("🔧 Filters")
    
    # Code filter/search
    st.sidebar.subheader("Product Code Filter")
    code_filter_type = st.sidebar.radio(
        "Filter Type:",
        ["All Codes", "Select Specific Codes", "Search Codes"]
    )
    
    selected_codes = []
    if code_filter_type == "Select Specific Codes":
        all_codes = sorted(df['Code'].unique().tolist())
        selected_codes = st.sidebar.multiselect(
            "Select Codes:", 
            all_codes,
            default=[]
        )
    elif code_filter_type == "Search Codes":
        search_term = st.sidebar.text_input(
            "Search Code (contains):", 
            placeholder="Enter code to search..."
        )
        if search_term:
            # Convert to string for safe comparison
            df['Code'] = df['Code'].astype(str)
            matching_codes = df[df['Code'].str.contains(search_term, case=False, na=False)]['Code'].unique().tolist()
            if matching_codes:
                st.sidebar.write(f"Found {len(matching_codes)} matching codes:")
                selected_codes = st.sidebar.multiselect(
                    "Select from matching codes:",
                    matching_codes,
                    default=matching_codes[:10]  # Auto-select first 10
                )
            else:
                st.sidebar.warning("No codes found matching your search.")
    
    # Supervisor dropdown
    supervisors = ['All'] + sorted(df['Supervisor'].dropna().unique().tolist())
    selected_supervisor = st.sidebar.selectbox("Select Supervisor:", supervisors)
    
    # Date range selector
    min_date = df['Sales_Date'].min().date()
    max_date = df['Sales_Date'].max().date()
    
    selected_date_range = st.sidebar.date_input(
        "Select Date Range:",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Apply filters
    filtered_df = df.copy()
    
    # Filter by code
    if code_filter_type != "All Codes" and selected_codes:
        # Ensure both are strings for comparison
        filtered_df['Code'] = filtered_df['Code'].astype(str)
        selected_codes_str = [str(code) for code in selected_codes]
        filtered_df = filtered_df[filtered_df['Code'].isin(selected_codes_str)]
    elif code_filter_type == "Search Codes" and not selected_codes and 'search_term' in locals() and search_term:
        # If search was performed but no codes were selected, show empty result
        filtered_df = filtered_df[filtered_df['Code'].isin([])]
    
    # Filter by supervisor
    if selected_supervisor != 'All':
        filtered_df = filtered_df[filtered_df['Supervisor'] == selected_supervisor]
    
    # Filter by date range
    if len(selected_date_range) == 2:
        start_date, end_date = selected_date_range
        filtered_df = filtered_df[
            (filtered_df['Sales_Date'].dt.date >= start_date) & 
            (filtered_df['Sales_Date'].dt.date <= end_date)
        ]
    
    # Create aggregated data for table (Code as rows, Qty as sum)
    if not filtered_df.empty:
        table_data = filtered_df.groupby(['Code', 'Supervisor']).agg({
            'Qty': 'sum',
            'Sales_Date': ['min', 'max']
        }).reset_index()
        
        # Flatten column names
        table_data.columns = ['Code', 'Supervisor', 'Total_Qty', 'First_Sale_Date', 'Last_Sale_Date']
        table_data = table_data.round(2)
        
        # Ensure dates are properly formatted
        table_data['First_Sale_Date'] = pd.to_datetime(table_data['First_Sale_Date']).dt.date
        table_data['Last_Sale_Date'] = pd.to_datetime(table_data['Last_Sale_Date']).dt.date
    else:
        table_data = pd.DataFrame(columns=['Code', 'Supervisor', 'Total_Qty', 'First_Sale_Date', 'Last_Sale_Date'])
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if not filtered_df.empty:
            total_qty = float(filtered_df['Qty'].sum())  # Ensure it's a float
            st.metric("Total Quantity", f"{total_qty:,.0f}")
        else:
            st.metric("Total Quantity", "0")
    
    with col2:
        if not filtered_df.empty:
            unique_codes = filtered_df['Code'].nunique()
            st.metric("Unique Codes", f"{unique_codes:,}")
        else:
            st.metric("Unique Codes", "0")
    
    with col3:
        if not filtered_df.empty:
            unique_supervisors = filtered_df['Supervisor'].nunique()
            st.metric("Supervisors", f"{unique_supervisors:,}")
        else:
            st.metric("Supervisors", "0")
    
    with col4:
        if code_filter_type != "All Codes":
            filtered_codes = len(selected_codes) if selected_codes else 0
            st.metric("Filtered Codes", f"{filtered_codes:,}")
        else:
            if not filtered_df.empty:
                date_range_days = (filtered_df['Sales_Date'].max() - filtered_df['Sales_Date'].min()).days
                st.metric("Date Range (Days)", f"{date_range_days:,}")
            else:
                st.metric("Date Range (Days)", "0")
    
    # Create two columns for layout
    col_table, col_chart = st.columns([1, 1])
    
    with col_table:
        st.subheader("📋 Sales Summary Table")
        
        # Display the table
        if not table_data.empty:
            st.dataframe(
                table_data,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Code": "Product Code",
                    "Supervisor": "Supervisor",
                    "Total_Qty": st.column_config.NumberColumn(
                        "Total Quantity",
                        format="%.0f"
                    ),
                    "First_Sale_Date": st.column_config.DateColumn("First Sale"),
                    "Last_Sale_Date": st.column_config.DateColumn("Last Sale")
                }
            )
            
            # Download button for table data
            csv = table_data.to_csv(index=False)
            st.download_button(
                label="📥 Download Table as CSV",
                data=csv,
                file_name=f"sales_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No data available for the selected filters.")
    
    with col_chart:
        st.subheader("📈 Quantity by Code")
        
        if not table_data.empty:
            # Create bar chart
            fig = px.bar(
                table_data.head(15),  # Show top 15 codes
                x='Code',
                y='Total_Qty',
                color='Supervisor',
                title="Top 15 Codes by Total Quantity",
                labels={'Total_Qty': 'Total Quantity', 'Code': 'Product Code'},
                height=400
            )
            
            fig.update_layout(
                xaxis_tickangle=-45,
                showlegend=True,
                margin=dict(b=100)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available for chart.")
    
    # Additional charts section
    st.markdown("---")
    st.subheader("📊 Additional Analytics")
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        # Time series chart
        if not filtered_df.empty:
            daily_sales = filtered_df.groupby(['Sales_Date'])['Qty'].sum().reset_index()
            
            fig_time = px.line(
                daily_sales,
                x='Sales_Date',
                y='Qty',
                title='Daily Sales Trend',
                labels={'Qty': 'Total Quantity', 'Sales_Date': 'Date'}
            )
            
            fig_time.update_layout(height=300)
            st.plotly_chart(fig_time, use_container_width=True)
        else:
            st.info("No data for time series chart.")
    
    with chart_col2:
        # Supervisor performance pie chart
        if not filtered_df.empty:
            supervisor_totals = filtered_df.groupby('Supervisor')['Qty'].sum().reset_index()
            
            fig_pie = px.pie(
                supervisor_totals,
                values='Qty',
                names='Supervisor',
                title='Sales by Supervisor'
            )
            
            fig_pie.update_layout(height=300)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No data for pie chart.")
    
    # Raw data section (collapsible)
    with st.expander("🔍 View Raw Data"):
        if not filtered_df.empty:
            # Format dates for display
            display_df = filtered_df.copy()
            display_df['Sales_Date'] = pd.to_datetime(display_df['Sales_Date']).dt.date
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # Download button for raw data
            csv_raw = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Raw Data as CSV",
                data=csv_raw,
                file_name=f"raw_sales_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No raw data available for the selected filters.")

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

if __name__ == "__main__":
    main()


