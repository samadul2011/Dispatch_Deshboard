import streamlit as st
import pandas as pd
import duckdb
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests

# Page configuration
st.set_page_config(page_title="Sales Dashboard", layout="wide")

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

# Cache data loading function
@st.cache_data
def load_data():
    """Load and merge sales data with product information"""
    try:
        # Connect to DuckDB using the new connection method
        conn = get_duckdb()
        
        # Load Sales and Products data
        sales = conn.execute("SELECT Code, Route, Qty, Sales_Date FROM Sales").df()
        Products = conn.execute("SELECT Code, Category3 FROM Products").df()
        
        # Join (like SQL LEFT JOIN)
        df = sales.merge(Products, on="Code", how="left")
        
        # Convert Sales_Date to datetime if it's not already
        df['Sales_Date'] = pd.to_datetime(df['Sales_Date'])
        
        # Convert Qty to numeric, handling any non-numeric values
        df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce').fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

# Load data
df = load_data()

# Streamlit App
st.title("📊 Sales Dashboard")
st.sidebar.header("Filters")

# Check if data loaded successfully
if df.empty:
    st.error("No data available. Please check your database connection.")
    st.stop()

# Sales_Date filter
st.sidebar.subheader("Sales Date Filter")
min_date = df['Sales_Date'].min().date()
max_date = df['Sales_Date'].max().date()

date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Handle date range selection
if len(date_range) == 2:
    start_date, end_date = date_range
else:
    # If only one date selected, use that single day
    start_date = end_date = date_range

# Category3 dropdown filter
st.sidebar.subheader("Category Filter")
categories = ['All'] + sorted(df['Category3'].dropna().unique().tolist())
selected_category = st.sidebar.selectbox("Select Category3", categories)

# Apply filters
filtered_df = df.copy()

# Filter by date range
filtered_df = filtered_df[
    (filtered_df['Sales_Date'].dt.date >= start_date) & 
    (filtered_df['Sales_Date'].dt.date <= end_date)
]

# Filter by Category3
if selected_category != 'All':
    filtered_df = filtered_df[filtered_df['Category3'] == selected_category]

# Create pivot table with Code as rows and sum of Qty as values
if not filtered_df.empty:
    pivot_table = filtered_df.groupby('Code')['Qty'].sum().reset_index()
    pivot_table.columns = ['Code', 'Total Qty']
    pivot_table = pivot_table.sort_values('Total Qty', ascending=False)
    
    # Display results
    st.header("📈 Sales Summary")
    
    # Show filter information
    st.info(f"📅 Showing data from {start_date} to {end_date} | 📂 Category: {selected_category}")
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Records", len(filtered_df))
    with col2:
        total_qty = pd.to_numeric(filtered_df['Qty'], errors='coerce').sum()
        st.metric("Total Quantity", f"{total_qty:,.0f}")
    with col3:
        st.metric("Unique Codes", filtered_df['Code'].nunique())
    with col4:
        st.metric("Date Range Days", (end_date - start_date).days + 1)
    
    # Display pivot table
    st.subheader("📋 Code Summary (Qty Sum)")
    st.dataframe(
        pivot_table,
        use_container_width=True,
        height=400,
        column_config={
            "Code": st.column_config.TextColumn("Product Code"),
            "Total Qty": st.column_config.NumberColumn("Total Quantity", format="%d")
        }
    )
    
    # Top 10 Codes Chart
    st.subheader("🏆 Top 10 Codes by Quantity")
    top_10 = pivot_table.head(10)
    
    fig_bar = px.bar(
        top_10,
        x='Code',
        y='Total Qty',
        title='Top 10 Products by Total Quantity',
        labels={'Total Qty': 'Total Quantity', 'Code': 'Product Code'},
        color='Total Qty',
        color_continuous_scale='Viridis'
    )
    fig_bar.update_layout(height=400)
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # Animated Charts Section
    st.header("🎬 Animated Sales Trends")
    
    # Prepare data for animated charts
    daily_sales = filtered_df.groupby('Sales_Date')['Qty'].sum().reset_index()
    daily_sales['Sales_Date'] = pd.to_datetime(daily_sales['Sales_Date'])
    daily_sales = daily_sales.sort_values('Sales_Date')
    
    if not daily_sales.empty:
        # Method 1: Progressive Line Animation
        st.subheader("📈 Progressive Sales Trend")
        
        # Create progressive animation data
        progressive_data = []
        for i in range(1, len(daily_sales) + 1):
            temp_df = daily_sales.iloc[:i].copy()
            temp_df['frame'] = i
            temp_df['frame_label'] = f"Day {i}: {daily_sales.iloc[i-1]['Sales_Date'].strftime('%Y-%m-%d')}"
            progressive_data.append(temp_df)
        
        if progressive_data:
            progressive_combined = pd.concat(progressive_data, ignore_index=True)
            
            fig_progressive = px.line(
                progressive_combined,
                x='Sales_Date',
                y='Qty',
                animation_frame='frame_label',
                title='Daily Sales Quantity - Progressive Build',
                markers=True,
                labels={
                    'Sales_Date': 'Sales Date',
                    'Qty': 'Quantity Sold'
                }
            )
            
            fig_progressive.update_layout(
                xaxis_title="Sales Date",
                yaxis_title="Quantity Sold",
                height=450,
                yaxis=dict(range=[0, daily_sales['Qty'].max() * 1.1])
            )
            
            # Customize animation settings
            fig_progressive.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 300
            fig_progressive.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 50
            
            # Style the line
            fig_progressive.update_traces(
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=6, color='#ff7f0e')
            )
            
            st.plotly_chart(fig_progressive, use_container_width=True)
        
        # Method 2: Moving Dot Animation
        st.subheader("🔴 Moving Point Animation")
        
        # Create moving dot animation
        dot_frames = []
        for i, row in daily_sales.iterrows():
            frame_data = pd.DataFrame({
                'Sales_Date': [row['Sales_Date']],
                'Qty': [row['Qty']],
                'frame': [f"Date: {row['Sales_Date'].strftime('%Y-%m-%d')}"],
                'all_dates': [daily_sales['Sales_Date'].tolist()],
                'all_qty': [daily_sales['Qty'].tolist()]
            })
            dot_frames.append(frame_data)
        
        dot_combined = pd.concat(dot_frames, ignore_index=True)
        
        fig_dot = px.scatter(
            dot_combined,
            x='Sales_Date',
            y='Qty',
            animation_frame='frame',
            title='Sales Movement - Point by Point',
            size_max=15,
            range_x=[daily_sales['Sales_Date'].min(), daily_sales['Sales_Date'].max()],
            range_y=[0, daily_sales['Qty'].max() * 1.1]
        )
        
        # Add background line
        fig_dot.add_trace(
            go.Scatter(
                x=daily_sales['Sales_Date'],
                y=daily_sales['Qty'],
                mode='lines',
                line=dict(color='lightgray', width=1, dash='dash'),
                name='Complete Trend',
                showlegend=False
            )
        )
        
        fig_dot.update_traces(
            marker=dict(size=12, color='#F24236', line=dict(width=2, color='white')),
            selector=dict(mode='markers')
        )
        
        fig_dot.update_layout(
            xaxis_title="Sales Date",
            yaxis_title="Quantity Sold",
            height=500
        )
        
        # Animation settings
        fig_dot.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 400
        fig_dot.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 200
        
        st.plotly_chart(fig_dot, use_container_width=True)
        
        # Category-wise animated chart
        st.subheader("📊 Sales by Category (Animated)")
        
        # Prepare category data
        category_daily = filtered_df.groupby(['Sales_Date', 'Category3'])['Qty'].sum().reset_index()
        category_daily['Sales_Date'] = pd.to_datetime(category_daily['Sales_Date'])
        category_daily = category_daily.sort_values(['Sales_Date', 'Category3'])
        
        if not category_daily.empty:
            # Get unique dates for animation frames
            unique_dates = sorted(category_daily['Sales_Date'].unique())
            
            # Create animation data for categories
            cat_animation_data = []
            for date in unique_dates:
                temp_df = category_daily[category_daily['Sales_Date'] <= date].copy()
                temp_df['frame'] = date.strftime('%Y-%m-%d')
                cat_animation_data.append(temp_df)
            
            if cat_animation_data:
                cat_combined_df = pd.concat(cat_animation_data, ignore_index=True)
                
                fig_cat = px.line(
                    cat_combined_df,
                    x='Sales_Date',
                    y='Qty',
                    color='Category3',
                    animation_frame='frame',
                    title='Daily Sales by Category Over Time',
                    labels={
                        'Sales_Date': 'Sales Date',
                        'Qty': 'Quantity Sold',
                        'Category3': 'Category'
                    }
                )
                
                fig_cat.update_traces(mode='lines+markers')
                fig_cat.update_layout(
                    xaxis_title="Sales Date",
                    yaxis_title="Quantity Sold",
                    height=500,
                    showlegend=True
                )
                
                # Update animation settings
                fig_cat.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 500
                fig_cat.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 100
                
                st.plotly_chart(fig_cat, use_container_width=True)
    
    # Play button instructions
    st.info("💡 **Tip:** Click the ▶️ play button on the animated charts to see the progression over time!")
    
    # Download options
    st.subheader("📥 Download Data")
    col1, col2 = st.columns(2)
    
    with col1:
        # Download summary data
        csv_summary = pivot_table.to_csv(index=False)
        st.download_button(
            label="Download Summary Data (CSV)",
            data=csv_summary,
            file_name=f"sales_summary_{start_date}_{end_date}.csv",
            mime="text/csv"
        )
    
    with col2:
        # Download filtered raw data
        csv_raw = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download Raw Data (CSV)",
            data=csv_raw,
            file_name=f"sales_raw_{start_date}_{end_date}.csv",
            mime="text/csv"
        )

else:
    st.warning("⚠️ No data available for the selected filters.")

# Show raw filtered data (optional)
if st.sidebar.checkbox("Show Raw Data"):
    st.subheader("🔍 Filtered Raw Data")
    display_df = filtered_df.copy()
    display_df['Sales_Date'] = pd.to_datetime(display_df['Sales_Date']).dt.date
    st.dataframe(display_df, use_container_width=True)

# Display total records info in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown(f"**📊 Total Records in DB:** {len(df):,}")
st.sidebar.markdown(f"**🔍 Filtered Records:** {len(filtered_df):,}")

# Debug info (optional)
if st.sidebar.checkbox("Show Debug Info"):
    st.sidebar.write("Daily Sales Data Shape:", daily_sales.shape if not filtered_df.empty else "N/A")
    if not filtered_df.empty:
        st.sidebar.write("Date Range:", daily_sales['Sales_Date'].min(), "to", daily_sales['Sales_Date'].max())
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
