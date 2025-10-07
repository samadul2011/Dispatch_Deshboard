import streamlit as st

# Page configuration MUST be the first Streamlit command
st.set_page_config(
    page_title="Dispatch Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling with proper colors
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        text-align: center;
        color: #2e8b57;
        margin-bottom: 2rem;
    }
    .welcome-card {
        background-color: #f0f2f6;
        padding: 2rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        margin-bottom: 2rem;
    }
    .welcome-card h3 {
        color: #1f77b4;
        margin-top: 0;
    }
    .welcome-card p {
        color: #262730;
        font-size: 1.1rem;
        line-height: 1.6;
    }
    .feature-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border: 1px solid #e0e0e0;
        height: 100%;
    }
    .feature-card h4 {
        color: #1f77b4;
        margin-top: 0;
    }
    .feature-card p, .feature-card li {
        color: #262730;
    }
    .developer-info {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
    }
    .developer-info h3, .developer-info p {
        color: white !important;
    }
    .metric-card {
        background-color: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        text-align: center;
        border-top: 4px solid #1f77b4;
    }
    .metric-card h3 {
        color: #1f77b4;
        font-size: 2.5rem;
        margin: 0.5rem 0;
    }
    .metric-card p {
        color: #262730;
        margin: 0;
    }
    .footer-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
    }
    .footer-section p {
        color: #262730;
        margin: 0.5rem 0;
    }
    .nav-button {
        width: 100%;
        text-align: left;
        margin: 5px 0;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #e0e0e0;
        background-color: white;
    }
    .nav-button:hover {
        background-color: #f0f2f6;
    }
</style>
""", unsafe_allow_html=True)

# Header Section
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.image("https://raw.githubusercontent.com/samadul2011/Dispatch_Deshboard/main/AtyabLogo.png", width=150)

with col2:
    st.markdown('<div class="main-header">🚀 Dispatch Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Smart Analytics for Better Decisions</div>', unsafe_allow_html=True)

with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**Version:** 2.0", unsafe_allow_html=True)

# Welcome Section
st.markdown("""
<div class="welcome-card">
    <h3>🎯 Welcome to Your Dispatch Command Center</h3>
    <p>This comprehensive dashboard provides real-time insights into your sales and orders data. 
    Monitor performance, analyze trends, and make data-driven decisions with our interactive tools.</p>
</div>
""", unsafe_allow_html=True)

# Key Features Section
st.subheader("📈 Dashboard Features")

feature_col1, feature_col2, feature_col3 = st.columns(3)

with feature_col1:
    st.markdown("""
    <div class="feature-card">
        <h4>📊 Orders vs Sales Analysis</h4>
        <p>Compare orders and sales quantities with detailed difference analysis and filtering capabilities.</p>
        <ul>
            <li>Date range filtering</li>
            <li>Product code search</li>
            <li>Difference calculations</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with feature_col2:
    st.markdown("""
    <div class="feature-card">
        <h4>🔍 Interactive Filters</h4>
        <p>Dynamic filtering options to drill down into specific data segments.</p>
        <ul>
            <li>Multiple date ranges</li>
            <li>Product code selection</li>
            <li>Real-time updates</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with feature_col3:
    st.markdown("""
    <div class="feature-card">
        <h4>📥 Export & Share</h4>
        <p>Export your analysis results for reporting and sharing.</p>
        <ul>
            <li>CSV download</li>
            <li>Filtered data export</li>
            <li>Printable reports</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# Quick Stats Section
st.subheader("🚀 Getting Started")

guide_col1, guide_col2, guide_col3 = st.columns(3)

with guide_col1:
    st.markdown("""
    <div class="metric-card">
        <h3>1</h3>
        <p><b>Select a Page</b><br>Choose from the sidebar menu to access different analyses</p>
    </div>
    """, unsafe_allow_html=True)

with guide_col2:
    st.markdown("""
    <div class="metric-card">
        <h3>2</h3>
        <p><b>Apply Filters</b><br>Use date ranges and product filters to focus on specific data</p>
    </div>
    """, unsafe_allow_html=True)

with guide_col3:
    st.markdown("""
    <div class="metric-card">
        <h3>3</h3>
        <p><b>Analyze & Export</b><br>Review insights and download your analysis</p>
    </div>
    """, unsafe_allow_html=True)

# Developer Info Section
st.markdown("""
<div class="developer-info">
    <h3>👨‍💻 Developed by Dispatch Team</h3>
    <p><strong>Samadul Hoque</strong> | Dispatch Supervisor</p>
    <p>📧 Contact: Your professional analytics partner for dispatch operations</p>
</div>
""", unsafe_allow_html=True)

# Footer
st.markdown("---")
footer_col1, footer_col2, footer_col3 = st.columns(3)

with footer_col1:
    st.markdown("""
    <div class="footer-section">
        <p><strong>🔒 Data Security</strong></p>
        <p>Your data is processed securely and never stored on external servers.</p>
    </div>
    """, unsafe_allow_html=True)

with footer_col2:
    st.markdown("""
    <div class="footer-section">
        <p><strong>🔄 Live Updates</strong></p>
        <p>Data refreshes automatically with the latest information.</p>
    </div>
    """, unsafe_allow_html=True)

with footer_col3:
    st.markdown("""
    <div class="footer-section">
        <p><strong>🆘 Need Help?</strong></p>
        <p>Contact the dispatch team for support and feature requests.</p>
    </div>
    """, unsafe_allow_html=True)

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
    index=list(page_configs.keys()).index(st.session_state.current_page),
    key="page_navigation"
)

# Show page description
if selected_page in page_descriptions:
    st.sidebar.info(f"**{selected_page}**\n\n{page_descriptions[selected_page]}")

# Actually navigate to the selected page if it's different from current
if selected_page != st.session_state.current_page:
    st.session_state.current_page = selected_page
    # Only switch page if it's not the Home page
    if selected_page != "🏠 Home":
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

# Display current page information (only shows when on Home page now)
st.markdown(f"### 📍 Currently Viewing: {st.session_state.current_page}")
st.success("✅ You are currently on the Home page. This is the main dashboard overview.")

# Additional helpful information
st.markdown("---")
st.markdown("### 📁 Your Available Pages")
st.markdown("The following pages are configured in your dashboard:")

# Display all available pages in a nice format
cols = st.columns(3)
for i, (page_name, description) in enumerate(page_descriptions.items()):
    with cols[i % 3]:
        st.markdown(f"""
        <div style='border: 1px solid #e0e0e0; border-radius: 10px; padding: 15px; margin: 5px 0; background-color: #f8f9fa;'>
            <h4 style='margin: 0 0 10px 0; color: #1f77b4;'>{page_name}</h4>
            <p style='margin: 0; font-size: 0.9em; color: #666;'>{description}</p>
        </div>
        """, unsafe_allow_html=True)
