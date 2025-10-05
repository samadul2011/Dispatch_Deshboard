import streamlit as st


color = "green"  # or "#008000"
st.markdown(f"<h1 style='color: {color};'>Welcome to the Dispatch Page</h1>", unsafe_allow_html=True)


st.set_page_config(page_title="📊 Sales Pivot Dashboard", layout="wide")
color= "red"
st.markdown(f"<h2 style='color: {color};'>Sales Data Analysis with Interactive Filters</h2>", unsafe_allow_html=True)


st.subheader("This dashboard allows you to filter sales data by supervisor and date range, providing insights into sales performance.")
color = "blue"
st.markdown(f"<h3 style='color: {color};'>Sales Dashboard developed by Dispatch Supervisor Samadul Hoque.</h3>", unsafe_allow_html=True)
#st.subheader("Sales Dashboard developed by Dispatch Supervisor Samadul Hoque")
st.sidebar.success("Select a page above.")