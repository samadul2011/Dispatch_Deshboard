import streamlit as st
import duckdb
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import requests

# Page configuration
st.set_page_config(page_title="Sales Oscilloscope", layout="wide")

# Title
st.title("📊 Sales Oscilloscope Dashboard - Animated Chart")

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

# Get date range from database
@st.cache_data
def get_date_range():
    query = """
    SELECT 
        MIN(CAST(Sales_Date AS DATE)) AS min_date,
        MAX(CAST(Sales_Date AS DATE)) AS max_date
    FROM Sales
    """
    result = con.execute(query).df()
    return result['min_date'].iloc[0], result['max_date'].iloc[0]

try:
    min_date, max_date = get_date_range()
    
    # Sidebar for date selection
    st.sidebar.header("📅 Select Date Range")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input(
            "From Date",
            value=max_date - timedelta(days=90) if max_date else datetime.now() - timedelta(days=90),
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
    
    # Animation settings
    st.sidebar.header("🎬 Animation Settings")
    animation_duration = st.sidebar.slider("Animation Duration (ms)", 500, 5000, 2000, 100)
    show_frames = st.sidebar.checkbox("Show Animation Frames", value=False)
    
    # Validate date range
    if start_date > end_date:
        st.error("⚠️ Start date must be before end date!")
        st.stop()
    
    # Query data based on selected date range
    @st.cache_data
    def load_data(start, end):
        query = """
        SELECT 
            CAST(Sales_Date AS DATE) AS Sales_Date,
            SUM(CAST(Qty AS INTEGER)) AS Qty
        FROM Sales
        WHERE CAST(Sales_Date AS DATE) BETWEEN CAST(? AS DATE) AND CAST(? AS DATE)
        GROUP BY CAST(Sales_Date AS DATE)
        ORDER BY CAST(Sales_Date AS DATE) ASC
        """
        return con.execute(query, [start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')]).df()
    
    # Query monthly data
    @st.cache_data
    def load_monthly_data(start, end):
        query = """
        SELECT 
            DATE_TRUNC('month', CAST(Sales_Date AS DATE)) AS Month,
            SUM(CAST(Qty AS INTEGER)) AS Qty
        FROM Sales
        WHERE CAST(Sales_Date AS DATE) BETWEEN CAST(? AS DATE) AND CAST(? AS DATE)
        GROUP BY DATE_TRUNC('month', CAST(Sales_Date AS DATE))
        ORDER BY Month ASC
        """
        df = con.execute(query, [start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')]).df()
        df['Month_Label'] = pd.to_datetime(df['Month']).dt.strftime('%b %Y')
        return df
    
    df = load_data(start_date, end_date)
    monthly_df = load_monthly_data(start_date, end_date)
    
    if df.empty:
        st.warning("⚠️ No data available for the selected date range.")
        st.stop()
    
    # Calculate running total
    df['Running_Total'] = df['Qty'].cumsum()
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Quantity", f"{df['Qty'].sum():,.0f}")
    
    with col2:
        st.metric("Average Daily Qty", f"{df['Qty'].mean():,.0f}")
    
    with col3:
        st.metric("Max Daily Qty", f"{df['Qty'].max():,.0f}")
    
    with col4:
        st.metric("Days in Range", len(df))
    
    # Create tabs for different visualizations
    tab1, tab2 = st.tabs(["📈 Daily Oscilloscope (Animated)", "📊 Monthly Column Chart"])
    
    with tab1:
        # Create animated oscilloscope chart with frames
        fig = go.Figure()
        
        # Create frames for animation
        frames = []
        for i in range(1, len(df) + 1):
            df_slice = df.iloc[:i]
            
            frame_data = [
                # Line trace
                go.Scatter(
                    x=df_slice['Sales_Date'],
                    y=df_slice['Qty'],
                    mode='lines',
                    name='Quantity',
                    line=dict(color='#00ff00', width=3),
                    fill='tozeroy',
                    fillcolor='rgba(0, 255, 0, 0.2)',
                    hovertemplate='<b>Date:</b> %{x|%Y-%m-%d}<br><b>Qty:</b> %{y:,.0f}<extra></extra>'
                ),
                # Current pointer
                go.Scatter(
                    x=[df_slice['Sales_Date'].iloc[-1]],
                    y=[df_slice['Qty'].iloc[-1]],
                    mode='markers+text',
                    name='Current Point',
                    marker=dict(
                        color='#ff0000',
                        size=20,
                        symbol='circle',
                        line=dict(color='#ffffff', width=3)
                    ),
                    text=[f"Total: {df_slice['Running_Total'].iloc[-1]:,.0f}"],
                    textposition="top center",
                    textfont=dict(color='#f1f3f6', size=14, family='Courier New'),
                    hovertemplate='<b>CURRENT</b><br><b>Date:</b> %{x|%Y-%m-%d}<br><b>Qty:</b> %{y:,.0f}<extra></extra>'
                )
            ]
            
            frames.append(go.Frame(data=frame_data, name=str(i)))
        
        # Add initial data (first point)
        fig.add_trace(go.Scatter(
            x=df['Sales_Date'][:1],
            y=df['Qty'][:1],
            mode='lines',
            name='Quantity',
            line=dict(color='#00ff00', width=3),
            fill='tozeroy',
            fillcolor='rgba(0, 255, 0, 0.2)',
            hovertemplate='<b>Date:</b> %{x|%Y-%m-%d}<br><b>Qty:</b> %{y:,.0f}<extra></extra>'
        ))
        
        fig.add_trace(go.Scatter(
            x=[df['Sales_Date'].iloc[0]],
            y=[df['Qty'].iloc[0]],
            mode='markers+text',
            name='Current Point',
            marker=dict(
                color='#ff0000',
                size=20,
                symbol='circle',
                line=dict(color='#ffffff', width=3)
            ),
            text=[f"Total: {df['Running_Total'].iloc[0]:,.0f}"],
            textposition="top center",
            textfont=dict(color='#00ff00', size=14, family='Courier New'),
            hovertemplate='<b>CURRENT</b><br><b>Date:</b> %{x|%Y-%m-%d}<br><b>Qty:</b> %{y:,.0f}<extra></extra>'
        ))
        
        # Add frames to figure
        fig.frames = frames
        
        # Add average line
        avg_qty = df['Qty'].mean()
        fig.add_hline(
            y=avg_qty,
            line_dash="dash",
            line_color="yellow",
            annotation_text=f"Average: {avg_qty:,.0f}",
            annotation_position="right"
        )
        
        # Oscilloscope-style layout with animation controls
        fig.update_layout(
            title="Sales Quantity Over Time - Animated Oscilloscope",
            xaxis_title="Date",
            yaxis_title="Quantity",
            hovermode='closest',
            plot_bgcolor='#0a0a0a',
            paper_bgcolor='#1a1a1a',
            font=dict(color='#00ff00', family='Courier New, monospace'),
            xaxis=dict(
                showgrid=True,
                gridcolor='#1a4d1a',
                gridwidth=1,
                color='#00ff00',
                range=[df['Sales_Date'].min() - timedelta(days=1), 
                       df['Sales_Date'].max() + timedelta(days=1)]
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='#1a4d1a',
                gridwidth=1,
                color='#00ff00',
                range=[0, df['Qty'].max() * 1.15]
            ),
            height=600,
            showlegend=True,
            legend=dict(
                bgcolor='rgba(0, 0, 0, 0.5)',
                bordercolor='#00ff00',
                borderwidth=1
            ),
            updatemenus=[
                dict(
                    type="buttons",
                    showactive=True,
                    buttons=[
                        dict(
                            label="▶ Play",
                            method="animate",
                            args=[None, {
                                "frame": {"duration": animation_duration / len(df), "redraw": True},
                                "fromcurrent": True,
                                "mode": "immediate",
                                "transition": {"duration": 0}
                            }]
                        ),
                        dict(
                            label="⏸ Pause",
                            method="animate",
                            args=[[None], {
                                "frame": {"duration": 0, "redraw": False},
                                "mode": "immediate",
                                "transition": {"duration": 0}
                            }]
                        ),
                        dict(
                            label="⏮ Reset",
                            method="animate",
                            args=[[0], {
                                "frame": {"duration": 0, "redraw": True},
                                "mode": "immediate",
                                "transition": {"duration": 0}
                            }]
                        )
                    ],
                    direction="left",
                    pad={"r": 10, "t": 87},
                    x=0.1,
                    xanchor="left",
                    y=0,
                    yanchor="top",
                    bgcolor='rgba(0, 255, 0, 0.2)',
                    bordercolor='#00ff00',
                    borderwidth=2,
                    font=dict(color='#00ff00', size=12)
                )
            ],
            sliders=[{
                "active": 0,
                "yanchor": "top",
                "y": -0.15,
                "xanchor": "left",
                "currentvalue": {
                    "prefix": "Progress: ",
                    "visible": True,
                    "xanchor": "right",
                    "font": {"color": "#00ff00", "size": 14}
                },
                "pad": {"b": 10, "t": 50},
                "len": 0.9,
                "x": 0.1,
                "steps": [
                    {
                        "args": [[f.name], {
                            "frame": {"duration": 0, "redraw": True},
                            "mode": "immediate",
                            "transition": {"duration": 0}
                        }],
                        "method": "animate",
                        "label": str(i)
                    } for i, f in enumerate(fig.frames)
                ],
                "bgcolor": 'rgba(0, 255, 0, 0.2)',
                "bordercolor": '#00ff00',
                "borderwidth": 2,
                "tickcolor": '#00ff00',
                "font": {"color": "#00ff00"}
            }] if show_frames else []
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.info("📌 Click the **▶ Play** button above the chart to start the animation!")
    
    with tab2:
        # Create monthly column chart
        fig_monthly = go.Figure()
        
        # Add column chart
        fig_monthly.add_trace(go.Bar(
            x=monthly_df['Month_Label'],
            y=monthly_df['Qty'],
            name='Monthly Quantity',
            marker=dict(
                color='#00ff00',
                line=dict(color='#00ff00', width=2),
                opacity=0.8
            ),
            text=monthly_df['Qty'].apply(lambda x: f'{x:,.0f}'),
            textposition='outside',
            textfont=dict(color='#00ff00', size=12, family='Courier New'),
            hovertemplate='<b>Month:</b> %{x}<br><b>Qty:</b> %{y:,.0f}<extra></extra>'
        ))
        
        # Add average line
        monthly_avg = monthly_df['Qty'].mean()
        fig_monthly.add_hline(
            y=monthly_avg,
            line_dash="dash",
            line_color="yellow",
            line_width=2,
            annotation_text=f"Average: {monthly_avg:,.0f}",
            annotation_position="right"
        )
        
        # Update layout with oscilloscope style
        fig_monthly.update_layout(
            title="Monthly Sales Quantity - Column Chart",
            xaxis_title="Month",
            yaxis_title="Quantity",
            plot_bgcolor='#0a0a0a',
            paper_bgcolor='#1a1a1a',
            font=dict(color='#00ff00', family='Courier New, monospace'),
            xaxis=dict(
                showgrid=True,
                gridcolor='#1a4d1a',
                gridwidth=1,
                color='#00ff00',
                tickangle=-45
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='#1a4d1a',
                gridwidth=1,
                color='#00ff00',
                range=[0, monthly_df['Qty'].max() * 1.15]
            ),
            height=600,
            showlegend=False,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_monthly, use_container_width=True)
        
        # Display monthly metrics
        st.subheader("📊 Monthly Statistics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Months", len(monthly_df))
        
        with col2:
            st.metric("Average Monthly Qty", f"{monthly_avg:,.0f}")
        
        with col3:
            best_month = monthly_df.loc[monthly_df['Qty'].idxmax()]
            st.metric("Best Month", best_month['Month_Label'], f"{best_month['Qty']:,.0f}")
        
        with col4:
            worst_month = monthly_df.loc[monthly_df['Qty'].idxmin()]
            st.metric("Lowest Month", worst_month['Month_Label'], f"{worst_month['Qty']:,.0f}")
        
        # Display monthly data table
        st.subheader("📋 Monthly Data Table")
        display_monthly_df = monthly_df.copy()
        display_monthly_df['Qty'] = display_monthly_df['Qty'].apply(lambda x: f"{x:,.0f}")
        display_monthly_df = display_monthly_df[['Month_Label', 'Qty']]
        display_monthly_df.columns = ['Month', 'Quantity']
        
        st.dataframe(
            display_monthly_df,
            use_container_width=True,
            hide_index=True,
            height=300
        )
    
    # Display daily data table
    st.subheader("📋 Daily Sales Data Table")
    
    # Format the dataframe for display
    display_df = df.copy()
    display_df['Sales_Date'] = pd.to_datetime(display_df['Sales_Date']).dt.strftime('%Y-%m-%d')
    display_df['Qty'] = display_df['Qty'].apply(lambda x: f"{x:,.0f}")
    display_df['Running_Total'] = display_df['Running_Total'].apply(lambda x: f"{x:,.0f}")
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=300
    )
    
    # Download buttons
    col1, col2 = st.columns(2)
    with col1:
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Daily Data as CSV",
            data=csv,
            file_name=f"sales_daily_data_{start_date}_{end_date}.csv",
            mime="text/csv"
        )
    
    with col2:
        monthly_csv = monthly_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Monthly Data as CSV",
            data=monthly_csv,
            file_name=f"sales_monthly_data_{start_date}_{end_date}.csv",
            mime="text/csv"
        )

except Exception as e:
    st.error(f"❌ Error: {str(e)}")
    st.info("Please ensure the database file exists and contains the required tables.")

finally:
    # Connection is cached, no need to close manually
    pass
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

