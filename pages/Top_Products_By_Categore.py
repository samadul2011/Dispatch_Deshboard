import streamlit as st
import pandas as pd
import duckdb
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Connect to DuckDB
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
conn = get_connection()

# Load Sales with Sales_Date
sales = conn.execute("SELECT Code, Route, Qty, Sales_Date FROM Sales").df()

# Load Product mapping
Products = conn.execute("SELECT Code, Category3 FROM Products").df()

# Join (like SQL LEFT JOIN)
df = sales.merge(Products, on="Code", how="left")

# Convert Sales_Date to datetime if it's not already
df['Sales_Date'] = pd.to_datetime(df['Sales_Date'])

# Convert Qty to numeric, handling any non-numeric values
df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce').fillna(0)

# Close connection
conn.close()

# Streamlit App
st.title("Sales Dashboard")
st.sidebar.header("Filters")

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

# Handle single date selection
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
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
    st.header("Sales Summary")
    
    # Show filter information
    st.info(f"Showing data from {start_date} to {end_date} | Category: {selected_category}")
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Records", len(filtered_df))
    with col2:
        total_qty = pd.to_numeric(filtered_df['Qty'], errors='coerce').sum()
        st.metric("Total Quantity", f"{total_qty:,.0f}")
    with col3:
        st.metric("Unique Codes", filtered_df['Code'].nunique())
    
    # Display pivot table
    st.subheader("Code Summary (Qty Sum)")
    st.dataframe(
        pivot_table,
        use_container_width=True,
        height=400
    )
    
    # Optional: Add a chart
    st.subheader("Top 10 Codes by Quantity")
    top_10 = pivot_table.head(10)
    st.bar_chart(top_10.set_index('Code')['Total Qty'])
    
    # Animated Line Chart by Sales_Date
    st.subheader("Sales Trend Over Time (Animated)")
    
    # Animated Line Chart by Sales_Date
    st.subheader("Sales Trend Over Time (Animated)")
    
    # Prepare data for animated line chart - Progressive reveal
    daily_sales = filtered_df.groupby('Sales_Date')['Qty'].sum().reset_index()
    daily_sales['Sales_Date'] = pd.to_datetime(daily_sales['Sales_Date'])
    daily_sales = daily_sales.sort_values('Sales_Date')
    
    if not daily_sales.empty:
        # Method 1: Progressive line reveal
        animation_frames = []
        for i in range(1, len(daily_sales) + 1):
            frame_data = daily_sales.iloc[:i].copy()
            frame_data['frame'] = i
            animation_frames.append(frame_data)
        
        combined_data = pd.concat(animation_frames, ignore_index=True)
        
        fig = px.line(
            combined_data,
            x='Sales_Date',
            y='Qty',
            animation_frame='frame',
            title='Daily Sales - Progressive Animation',
            markers=True,
            range_x=[daily_sales['Sales_Date'].min(), daily_sales['Sales_Date'].max()],
            range_y=[0, daily_sales['Qty'].max() * 1.1]
        )
        
        fig.update_traces(
            line=dict(color='#2E86AB', width=3),
            marker=dict(size=8, color='#F24236')
        )
        
        fig.update_layout(
            xaxis_title="Sales Date",
            yaxis_title="Quantity Sold",
            height=500
        )
        
        # Animation settings
        fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 500
        fig.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 100
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Method 2: Moving dot animation
    st.subheader("Sales Trend - Moving Point Animation")
    
    if not daily_sales.empty:
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
    
    # Alternative: Category-wise animated chart
    st.subheader("Sales by Category (Animated)")
    
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
    
    # Animated Sales Trend (Progressive Line Building)
    st.subheader("Sales Trend (Animated Progressive)")
    
    if not daily_sales.empty:
        # Create progressive animation data
        progressive_data = []
        for i in range(1, len(daily_sales) + 1):
            temp_df = daily_sales.iloc[:i].copy()
            temp_df['animation_frame'] = f"Day {i}: {daily_sales.iloc[i-1]['Sales_Date'].strftime('%Y-%m-%d')}"
            progressive_data.append(temp_df)
        
        if progressive_data:
            progressive_combined = pd.concat(progressive_data, ignore_index=True)
            
            fig_progressive = px.line(
                progressive_combined,
                x='Sales_Date',
                y='Qty',
                animation_frame='animation_frame',
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
                # Fix y-axis range to prevent jumping
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
    
    # Play button instructions
    st.info("💡 Click the ▶️ play button on the animated charts to see the progression over time!")
    
    # Debug info (optional - you can remove this later)
    if st.sidebar.checkbox("Show Debug Info"):
        st.write("Daily Sales Data Shape:", daily_sales.shape)
        st.write("Date Range:", daily_sales['Sales_Date'].min(), "to", daily_sales['Sales_Date'].max())
        st.write("Sample Data:")
        st.write(daily_sales.head())
    
else:
    st.warning("No data available for the selected filters.")

# Show raw filtered data (optional)
if st.sidebar.checkbox("Show Raw Data"):
    st.subheader("Filtered Raw Data")
    st.dataframe(filtered_df)

# Display total records info
st.sidebar.markdown(f"**Total Records in DB:** {len(df)}")
st.sidebar.markdown(f"**Filtered Records:** {len(filtered_df)}")
