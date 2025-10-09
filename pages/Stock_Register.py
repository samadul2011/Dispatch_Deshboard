import streamlit as st
import duckdb
import pandas as pd
from datetime import datetime
import os
import requests

# Page configuration
st.set_page_config(page_title="Inventory Management System", layout="wide")

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
con = get_duckdb()
st.success("Connected to DuckDB!")

# Define queries for different tables
@st.cache_data
def get_sales_data(start_date, end_date, search_code=""):
    query = """
    SELECT 
        CAST(Sales_Date AS DATE) AS Date,
        CAST(Code AS VARCHAR) AS Code,
        SUM(CAST(Qty AS DECIMAL)) AS Sales_Qty
    FROM Sales 
    WHERE CAST(Sales_Date AS DATE) BETWEEN CAST(? AS DATE) AND CAST(? AS DATE)
    GROUP BY CAST(Sales_Date AS DATE), Code
    ORDER BY Date, Code
    """
    df = con.execute(query, [start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')]).df()
    
    # Ensure Date column is properly formatted without time
    if not df.empty and 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date']).dt.date
    
    if search_code:
        df = df[df['Code'].str.contains(search_code, case=False, na=False)]
    return df

@st.cache_data
def get_cost_center_data(start_date, end_date, search_code=""):
    query = """
    SELECT 
        CAST(Date AS DATE) AS Date,
        CAST(Code AS VARCHAR) AS Code,
        SUM(CAST(Qty AS DECIMAL)) AS CostCenter_Qty
    FROM CostCenter 
    WHERE CAST(Date AS DATE) BETWEEN CAST(? AS DATE) AND CAST(? AS DATE)
    GROUP BY CAST(Date AS DATE), Code
    ORDER BY Date, Code
    """
    df = con.execute(query, [start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')]).df()
    
    # Ensure Date column is properly formatted without time
    if not df.empty and 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date']).dt.date
    
    if search_code:
        df = df[df['Code'].str.contains(search_code, case=False, na=False)]
    return df

@st.cache_data
def get_received_data(start_date, end_date, search_code=""):
    query = """
    SELECT 
        CAST(Received_Date AS DATE) AS Date,
        CAST(Code AS VARCHAR) AS Code,
        SUM(CAST(Received_Qty AS DECIMAL)) AS Received_Qty
    FROM Received 
    WHERE CAST(Received_Date AS DATE) BETWEEN CAST(? AS DATE) AND CAST(? AS DATE)
    GROUP BY CAST(Received_Date AS DATE), Code
    ORDER BY Date, Code
    """
    df = con.execute(query, [start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')]).df()
    
    # Ensure Date column is properly formatted without time
    if not df.empty and 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date']).dt.date
    
    if search_code:
        df = df[df['Code'].str.contains(search_code, case=False, na=False)]
    return df

@st.cache_data
def get_adjustment_data(start_date, end_date, search_code=""):
    query = """
    SELECT 
        CAST(Adjuctment_Date AS DATE) AS Date,
        CAST(Code AS VARCHAR) AS Code,
        SUM(CAST(Adjustment_Qty AS DECIMAL)) AS Adjustment_Qty
    FROM Adjustment 
    WHERE CAST(Adjuctment_Date AS DATE) BETWEEN CAST(? AS DATE) AND CAST(? AS DATE)
    GROUP BY CAST(Adjuctment_Date AS DATE), Code
    ORDER BY Date, Code
    """
    df = con.execute(query, [start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')]).df()
    
    # Ensure Date column is properly formatted without time
    if not df.empty and 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date']).dt.date
    
    if search_code:
        df = df[df['Code'].str.contains(search_code, case=False, na=False)]
    return df

@st.cache_data
def get_inventory_summary(start_date, end_date, search_code=""):
    query = """
    WITH Received_Data AS (
        SELECT 
            CAST(Received_Date AS DATE) AS Date,
            CAST(Code AS VARCHAR) AS Code,
            COALESCE(Received_Qty, 0) AS Received_Qty
        FROM Received
        
        UNION ALL
        
        SELECT 
            CAST(Adjuctment_Date AS DATE) AS Date,
            CAST(Code AS VARCHAR) AS Code,
            COALESCE(Adjustment_Qty, 0) AS Received_Qty
        FROM Adjustment
    ),
    Sales_Data AS (
        SELECT 
            CAST(Date AS DATE) AS Date,
            CAST(Code AS VARCHAR) AS Code,
            SUM(Sales_Qty) + SUM(CostCenter_Qty) AS Sales_Qty
        FROM (
            SELECT 
                CAST(Sales_Date AS DATE) AS Date,
                CAST(Code AS VARCHAR) AS Code,
                SUM(CAST(Qty AS DECIMAL)) AS Sales_Qty,
                0 AS CostCenter_Qty
            FROM Sales 
            GROUP BY Code, CAST(Sales_Date AS DATE)

            UNION ALL

            SELECT 
                CAST(Date AS DATE) AS Date,
                CAST(Code AS VARCHAR) AS Code,
                0 AS Sales_Qty,
                SUM(CAST(Qty AS DECIMAL)) AS CostCenter_Qty
            FROM CostCenter 
            GROUP BY Code, CAST(Date AS DATE)
        ) combined
        GROUP BY Code, Date
    ),
    Combined AS (
        SELECT 
            COALESCE(r.Date, s.Date) AS Date,
            COALESCE(r.Code, s.Code) AS Code,
            COALESCE(r.Received_Qty, 0) AS Received_Qty,
            COALESCE(s.Sales_Qty, 0) AS Sales_Qty
        FROM Received_Data r
        FULL OUTER JOIN Sales_Data s
            ON r.Code = s.Code AND r.Date = s.Date
    ),
    RunningStock AS (
        SELECT 
            Code,
            Date,
            SUM(Received_Qty - Sales_Qty) OVER (
                PARTITION BY Code 
                ORDER BY Date
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) AS CumulativeStock
        FROM Combined
    ),
    PrevStock AS (
        SELECT 
            Code,
            MAX(CumulativeStock) AS Previous_Stock
        FROM RunningStock
        WHERE Date < CAST(? AS DATE)
        GROUP BY Code
    ),
    PeriodTotals AS (
        SELECT 
            Code,
            SUM(Received_Qty) AS Total_Received,
            SUM(Sales_Qty) AS Total_Sales
        FROM Combined
        WHERE Date BETWEEN CAST(? AS DATE) AND CAST(? AS DATE)
        GROUP BY Code
    )
    SELECT 
        COALESCE(p.Code, t.Code) AS Code,
        COALESCE(p.Previous_Stock, 0) AS Previous_Stock,
        COALESCE(t.Total_Received, 0) AS Total_Received,
        COALESCE(t.Total_Sales, 0) AS Total_Sales,
        COALESCE(p.Previous_Stock, 0) + COALESCE(t.Total_Received, 0) - COALESCE(t.Total_Sales, 0) AS Stock
    FROM PrevStock p
    FULL OUTER JOIN PeriodTotals t
        ON p.Code = t.Code
    ORDER BY Code
    """
    df = con.execute(query, [
        start_date.strftime('%Y-%m-%d'), 
        start_date.strftime('%Y-%m-%d'), 
        end_date.strftime('%Y-%m-%d')
    ]).df()
    
    if search_code:
        df = df[df['Code'].str.contains(search_code, case=False, na=False)]
    return df

# Streamlit UI
st.title("📊 Inventory Management System")

# Sidebar filters
st.sidebar.header("Filters")

# Table selection dropdown
table_options = {
    "Inventory Summary": "summary",
    "Sales": "sales", 
    "Cost Center": "cost_center",
    "Received": "received",
    "Adjustment": "adjustment"
}

selected_table = st.sidebar.selectbox(
    "Select Table to View",
    options=list(table_options.keys()),
    index=0
)

# Date range selector
col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input("From Date", value=datetime(2024, 1, 1))
with col2:
    end_date = st.date_input("To Date", value=datetime.now())

# Code search
search_code = st.sidebar.text_input("Search Code", "")

# Get and display data based on selection
if start_date <= end_date:
    with st.spinner(f"Loading {selected_table} data..."):
        
        if selected_table == "Inventory Summary":
            df = get_inventory_summary(start_date, end_date, search_code)
            st.header("📦 Inventory Summary")
            
            if not df.empty:
                # Display metrics
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("Total Products", df['Code'].nunique())
                with col2:
                    st.metric("Total Received", f"{df['Total_Received'].sum():,.0f}")
                with col3:
                    st.metric("Total Sales", f"{df['Total_Sales'].sum():,.0f}")
                with col4:
                    st.metric("Previous Stock", f"{df['Previous_Stock'].sum():,.0f}")
                with col5:
                    st.metric("Current Stock", f"{df['Stock'].sum():,.0f}")
                
                st.divider()
                
                # Format and display dataframe
                display_df = df.copy()
                for col in ['Previous_Stock', 'Total_Received', 'Total_Sales', 'Stock']:
                    display_df[col] = display_df[col].apply(lambda x: f"{x:,.0f}")
                
                st.dataframe(display_df, use_container_width=True, height=600)
                
                # Download button
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Summary as CSV",
                    data=csv,
                    file_name=f"inventory_summary_{start_date}_{end_date}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No data found for the selected filters.")
                
        elif selected_table == "Sales":
            df = get_sales_data(start_date, end_date, search_code)
            st.header("💰 Sales Data")
            if not df.empty:
                st.metric("Total Sales Quantity", f"{df['Sales_Qty'].sum():,.0f}")
                st.metric("Unique Products", df['Code'].nunique())
                st.dataframe(df, use_container_width=True, height=600)
                
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Sales Data",
                    data=csv,
                    file_name=f"sales_data_{start_date}_{end_date}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No sales data found for the selected filters.")
                
        elif selected_table == "Cost Center":
            df = get_cost_center_data(start_date, end_date, search_code)
            st.header("🏢 Cost Center Data")
            if not df.empty:
                st.metric("Total Cost Center Quantity", f"{df['CostCenter_Qty'].sum():,.0f}")
                st.metric("Unique Products", df['Code'].nunique())
                st.dataframe(df, use_container_width=True, height=600)
                
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Cost Center Data",
                    data=csv,
                    file_name=f"cost_center_{start_date}_{end_date}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No cost center data found for the selected filters.")
                
        elif selected_table == "Received":
            df = get_received_data(start_date, end_date, search_code)
            st.header("📥 Received Data")
            if not df.empty:
                st.metric("Total Received Quantity", f"{df['Received_Qty'].sum():,.0f}")
                st.metric("Unique Products", df['Code'].nunique())
                st.dataframe(df, use_container_width=True, height=600)
                
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Received Data",
                    data=csv,
                    file_name=f"received_{start_date}_{end_date}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No received data found for the selected filters.")
                
        elif selected_table == "Adjustment":
            df = get_adjustment_data(start_date, end_date, search_code)
            st.header("⚙️ Adjustment Data")
            if not df.empty:
                st.metric("Total Adjustment Quantity", f"{df['Adjustment_Qty'].sum():,.0f}")
                st.metric("Unique Products", df['Code'].nunique())
                st.dataframe(df, use_container_width=True, height=600)
                
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Adjustment Data",
                    data=csv,
                    file_name=f"adjustment_{start_date}_{end_date}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No adjustment data found for the selected filters.")

else:
    st.error("End date must be after start date.")
