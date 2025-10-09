import streamlit as st
import pandas as pd
import duckdb
import plotly.express as px
import os
import requests

# Page configuration
st.set_page_config(page_title="Sales Sunburst Chart", layout="wide")

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

# Get connection
conn = get_duckdb()
st.success("Connected to DuckDB!")

# Load data with caching
@st.cache_data
def load_data():
    sales = pd.read_sql("SELECT Code, Route, Qty, Sales_Date FROM Sales", conn)
    Products = pd.read_sql("SELECT Code, Category3, Category2 FROM Products", conn)
    df = sales.merge(Products, on="Code", how="left")
    df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce')
    df['Sales_Date'] = pd.to_datetime(df['Sales_Date'])
    return df

# Load initial data
df = load_data()

# --- 🔹 Streamlit Date Filter ---
st.sidebar.header("Filter Options")

# Get min & max date from your data
min_date = df['Sales_Date'].min().date()
max_date = df['Sales_Date'].max().date()

# Date range selector
selected_dates = st.sidebar.date_input(
    "Select Date Range",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# Apply date filter - FIXED LOGIC
if len(selected_dates) == 2:
    # User selected a date range
    start_date, end_date = selected_dates
elif len(selected_dates) == 1:
    # User selected only one date, use that single day
    start_date = end_date = selected_dates[0]
else:
    # Fallback to full range
    start_date, end_date = min_date, max_date

# Apply the date filter
mask = (df['Sales_Date'].dt.date >= start_date) & (df['Sales_Date'].dt.date <= end_date)
filtered_df = df.loc[mask]

# Show filter info
st.sidebar.info(f"Showing data from: {start_date} to {end_date}")

# Process data for sunburst chart
@st.cache_data
def process_sunburst_data(_df):
    sunburst_data = _df.groupby(['Category3', 'Category2', 'Code']).agg({
        'Qty': 'sum'
    }).reset_index()

    # Remove rows with missing Category3 or Category2
    sunburst_data = sunburst_data.dropna(subset=['Category3', 'Category2'])

    # Get top 20 products for each Category2
    def get_top_products_per_category(data, n=20):
        top_products = []
        for category2 in data['Category2'].unique():
            category_data = data[data['Category2'] == category2]
            top_category_products = category_data.nlargest(n, 'Qty')
            top_products.append(top_category_products)
        
        return pd.concat(top_products, ignore_index=True)

    # Get top 20 products per Category2
    top_products_data = get_top_products_per_category(sunburst_data, n=20)

    # Create hierarchical structure for sunburst
    # Structure: Root -> Category3 -> Category2 -> Code
    sunburst_final = []

    # Add Category3 level (top parent nodes)
    for category3 in top_products_data['Category3'].unique():
        category3_total = top_products_data[top_products_data['Category3'] == category3]['Qty'].sum()
        sunburst_final.append({
            'ids': category3,
            'labels': category3,
            'parents': '',
            'values': category3_total
        })

    # Add Category2 level (middle nodes)
    for category3 in top_products_data['Category3'].unique():
        category3_data = top_products_data[top_products_data['Category3'] == category3]
        for category2 in category3_data['Category2'].unique():
            category2_total = category3_data[category3_data['Category2'] == category2]['Qty'].sum()
            sunburst_final.append({
                'ids': f"{category3}_{category2}",
                'labels': category2,
                'parents': category3,
                'values': category2_total
            })

    # Add Code level (leaf nodes)
    for _, row in top_products_data.iterrows():
        sunburst_final.append({
            'ids': f"{row['Category3']}_{row['Category2']}_{row['Code']}",
            'labels': row['Code'],
            'parents': f"{row['Category3']}_{row['Category2']}",
            'values': row['Qty']
        })

    return pd.DataFrame(sunburst_final), top_products_data

# Check if filtered data is not empty
if not filtered_df.empty:
    # Process the filtered data
    sunburst_df, top_products_data = process_sunburst_data(filtered_df)
    
    # Check if we have data for the sunburst chart
    if not sunburst_df.empty and not top_products_data.empty:
        # Create the sunburst chart
        fig = px.sunburst(
            sunburst_df,
            ids='ids',
            names='labels',
            parents='parents',
            values='values',
            title=f'Sales Distribution: Category3 → Category2 → Top 20 Products by Quantity ({start_date} to {end_date})',
            color='values',
            color_continuous_scale='Viridis'
        )

        # Customize the layout
        fig.update_layout(
            title_font_size=16,
            title_x=0.5,
            width=800,
            height=600,
            font_size=12
        )

        # Update traces for better visibility
        fig.update_traces(
            textinfo="label+percent parent",
            hovertemplate='<b>%{label}</b><br>Quantity: %{value}<br>Percentage: %{percentParent}<extra></extra>'
        )

        # Display in Streamlit
        st.title("📊 Sales Data Sunburst Chart")
        st.write(f"This chart shows the sales distribution by Category3, Category2, and the top 20 products within each Category2 for the selected date range.")

        # Show some statistics
        st.subheader("Data Summary")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Categories", len(top_products_data['Category3'].unique()))

        with col2:
            st.metric("Total Products", len(top_products_data))

        with col3:
            st.metric("Total Quantity", f"{top_products_data['Qty'].sum():,.0f}")

        with col4:
            st.metric("Date Range", f"{start_date} to {end_date}")

        # Display the chart
        st.plotly_chart(fig, use_container_width=True)

        # Optional: Show the top products table
        if st.checkbox("Show Top Products Data"):
            st.subheader("Top 20 Products per Category2")
            
            # Create a more readable display
            display_data = top_products_data.copy()
            display_data = display_data.sort_values(['Category3', 'Category2', 'Qty'], ascending=[True, True, False])
            display_data['Qty'] = display_data['Qty'].apply(lambda x: f"{x:,.0f}")
            
            st.dataframe(
                display_data,
                column_config={
                    "Category3": "Category 3",
                    "Category2": "Category 2",
                    "Code": "Product Code",
                    "Qty": "Total Quantity"
                },
                hide_index=True,
                use_container_width=True
            )

        # Optional: Category-wise breakdown
        if st.checkbox("Show Category Breakdown"):
            st.subheader("Sales by Category")
            
            category_summary = top_products_data.groupby('Category3')['Qty'].agg(['sum', 'count']).reset_index()
            category_summary.columns = ['Category', 'Total Quantity', 'Number of Products']
            category_summary = category_summary.sort_values('Total Quantity', ascending=False)
            category_summary['Total Quantity'] = category_summary['Total Quantity'].apply(lambda x: f"{x:,.0f}")
            
            st.dataframe(category_summary, hide_index=True, use_container_width=True)

        # Download option
        csv = top_products_data.to_csv(index=False)
        st.download_button(
            label="📥 Download Processed Data",
            data=csv,
            file_name=f"sunburst_data_{start_date}_{end_date}.csv",
            mime="text/csv"
        )
    else:
        st.warning("No data available for the selected date range after processing. Please select a different date range.")
else:
    st.warning("No sales data found for the selected date range. Please select a different date range.")

# Close connection (optional since it's cached)
# conn.close()st.sidebar.title("🌐 Navigation")
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



