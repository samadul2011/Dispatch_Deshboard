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

# Sidebar Navigation
st.sidebar.title("🌐 Navigation")
st.sidebar.markdown("### Select a Dashboard Page")

# Updated page_options with all your pages
page_options = {
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

# Display pages in sidebar
for page, description in page_options.items():
    st.sidebar.markdown(f"**{page}**")
    st.sidebar.caption(description)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔧 Quick Actions")
if st.sidebar.button("🔄 Refresh All Data"):
    st.cache_data.clear()
    st.success("Data refreshed successfully!")

st.sidebar.markdown("### 📞 Support")
st.sidebar.info("For technical support or feature requests, please contact the Dispatch Supervisor.")
