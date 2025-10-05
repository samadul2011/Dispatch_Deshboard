import streamlit as st
import duckdb
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# Page configuration
st.set_page_config(page_title="Sales Oscilloscope", layout="wide")

# Title
st.title("📊 Sales Oscilloscope Dashboard - Animated Chart")

# Connect to DuckDB
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
        query = f"""
        SELECT 
            CAST(Sales_Date AS DATE) AS Sales_Date,
            SUM(CAST(Qty AS INTEGER)) AS Qty
        FROM Sales
        WHERE CAST(Sales_Date AS DATE) BETWEEN '{start}' AND '{end}'
        GROUP BY Sales_Date
        ORDER BY Sales_Date ASC
        """
        return con.execute(query).df()
    
    df = load_data(start_date, end_date)
    
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
                textfont=dict(color="#f1f3f6", size=14, family='Courier New'),
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
    
    # Display data table
    st.subheader("📋 Sales Data Table")
    
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
    
    # Download button
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download Data as CSV",
        data=csv,
        file_name=f"sales_data_{start_date}_{end_date}.csv",
        mime="text/csv"
    )

except Exception as e:
    st.error(f"❌ Error: {str(e)}")
    st.info("Please ensure the database file exists at the specified path and contains the Sales table.")

finally:

    pass

