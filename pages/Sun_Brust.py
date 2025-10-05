import streamlit as st
import pandas as pd
import duckdb
import plotly.express as px

# Connect to DuckDB
conn = duckdb.connect("/workspaces/Dispatch_Deshboard/disptach.duckdb")

# Load Sales with Sales_Date
sales = pd.read_sql("SELECT Code, Route, Qty, Sales_Date FROM Sales", conn)

# Load Product mapping
Products = pd.read_sql("SELECT Code, Category3, Category2 FROM Products", conn)

# Join (like SQL LEFT JOIN)
df = sales.merge(Products, on="Code", how="left")

# Convert Qty to numeric (in case it's stored as text)
df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce')

# Convert Sales_Date to datetime if it's not already
df['Sales_Date'] = pd.to_datetime(df['Sales_Date'])

# Close the database connection
conn.close()

# Aggregate data by Category3, Category2 and Code
sunburst_data = df.groupby(['Category3', 'Category2', 'Code']).agg({
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

# Convert to DataFrame
sunburst_df = pd.DataFrame(sunburst_final)

# Create the sunburst chart
fig = px.sunburst(
    sunburst_df,
    ids='ids',
    names='labels',
    parents='parents',
    values='values',
    title='Sales Distribution: Category3 → Category2 → Top 20 Products by Quantity',
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
st.title("Sales Data Sunburst Chart")
st.write("This chart shows the sales distribution by Category3, Category2, and the top 20 products within each Category2.")

# Show some statistics
st.subheader("Data Summary")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Categories", len(top_products_data['Category3'].unique()))

with col2:
    st.metric("Total Products", len(top_products_data))

with col3:
    st.metric("Total Quantity", f"{top_products_data['Qty'].sum():,.0f}")

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
        hide_index=True
    )

# Optional: Category-wise breakdown
if st.checkbox("Show Category Breakdown"):
    st.subheader("Sales by Category")
    
    category_summary = top_products_data.groupby('Category3')['Qty'].agg(['sum', 'count']).reset_index()
    category_summary.columns = ['Category', 'Total Quantity', 'Number of Products']
    category_summary = category_summary.sort_values('Total Quantity', ascending=False)
    category_summary['Total Quantity'] = category_summary['Total Quantity'].apply(lambda x: f"{x:,.0f}")
    
    st.dataframe(category_summary, hide_index=True)

print("Sunburst chart created successfully!")
print(f"Total categories: {len(top_products_data['Category3'].unique())}")
print(f"Total products displayed: {len(top_products_data)}")
print(f"Data shape: {top_products_data.shape}")

df['Sales_Date'] = pd.to_datetime(df['Sales_Date'])

# --- 🔹 Streamlit Date Filter ---
st.sidebar.header("Filter Options")

# Get min & max date from your data
min_date = df['Sales_Date'].min().date()
max_date = df['Sales_Date'].max().date()

# Date range selector
start_date, end_date = st.sidebar.date_input(
    "Select Date Range",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# Apply date filter
if isinstance(start_date, list):  # If user selects a range
    start_date, end_date = start_date[0], start_date[1]

mask = (df['Sales_Date'].dt.date >= start_date) & (df['Sales_Date'].dt.date <= end_date)

df = df.loc[mask]
