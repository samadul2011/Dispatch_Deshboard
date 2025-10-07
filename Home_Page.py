from ast import With
import streamlit as st

col1, col2, col3 = st.columns([1, 2, 1])
color = "green"  # or "#008000"
with col2:
    st.title("Welcome to the Dispatch Page")

with col1:
    st.image("https://raw.githubusercontent.com/samadul2011/Dispatch_Deshboard/main/AtyabLogo.png", width=200)

st.set_page_config(page_title="📊 Sales Pivot Dashboard", layout="wide")

color= "red"
st.markdown(f"<h2 style='color: {color};'>Sales Data Analysis with Interactive Filters</h2>", unsafe_allow_html=True)

with col2:
    st.markdown(":green[Sales Dashboard developed] :red[by]")
    st.markdown(":blue[Dispatch Supervisor]")
    st.markdown(":green[Samadul Hoque].")


st.markdown("This dashboard allows you to filter sales data by supervisor and date range, providing insights into sales performance.")
st.markdown("Use the sidebar to navigate through different sections of the dashboard.")

st.markdown(":green[Note: This dashboard is a work in progress and will be updated with more features soon.]")
#color = "blue"
#st.markdown(f"<h3 style='color: {color};'>Sales Dashboard developed by Dispatch Supervisor Samadul Hoque.</h3>", unsafe_allow_html=True)
#st.subheader("Sales Dashboard developed by Dispatch Supervisor Samadul Hoque")
st.sidebar.success("Select a page above.")
