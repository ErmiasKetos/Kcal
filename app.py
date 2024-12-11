import streamlit as st
import pandas as pd
from datetime import datetime
import logging
from src.dashboard import render_dashboard
from src.inventory_review import inventory_review_page
from src.inventory_manager import InventoryManager
from src.registration_page import registration_page
from src.calibration_page import calibration_page

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom CSS for professional look
st.markdown("""
<style>
    /* Main app styling */
    .stApp {
        background: linear-gradient(to bottom right, #f8f9fa, #e9ecef);
    }
    
    /* Navigation and sidebar */
    .sidebar .sidebar-content {
        background-color: #ffffff;
        border-right: 1px solid #dee2e6;
    }
    
    /* Main content area */
    .main .block-container {
        padding: 2rem;
        background: linear-gradient(to bottom, #ffffff, #f8f9fa);
        border-radius: 10px;
        box-shadow: 0 2px 15px rgba(0,0,0,0.05);
    }

    /* Headers and text */
    h1, h2, h3 {
        color: #0071ba;
        font-family: 'Arial', sans-serif;
        font-weight: 600;
    }
    
    /* Cards and containers */
    .stMarkdown div {
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        background: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: transform 0.2s ease;
    }
    
    .stMarkdown div:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Status indicators */
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-weight: 500;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #0071ba;
        color: white;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #005a94;
        box-shadow: 0 4px 8px rgba(0,113,186,0.2);
        transform: translateY(-1px);
    }
    
    /* Form inputs */
    .stTextInput > div > div > input {
        border-radius: 4px;
        border: 1px solid #ced4da;
        padding: 0.5rem;
        transition: border-color 0.2s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #0071ba;
        box-shadow: 0 0 0 2px rgba(0,113,186,0.2);
    }
    
    /* Select boxes */
    .stSelectbox > div > div {
        border-radius: 4px;
        border: 1px solid #ced4da;
    }
    
    /* Metrics */
    .stMetric {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Data frames */
    .stDataFrame {
        border: 1px solid #e9ecef;
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 4px;
        padding: 0.5rem 1rem;
        background: white;
    }
    
    /* Login form styling */
    .login-container {
        max-width: 400px;
        margin: 2rem auto;
        padding: 2rem;
        background: white;
        border-radius: 10px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
    }
    
    .login-header {
        text-align: center;
        color: #0071ba;
        margin-bottom: 2rem;
    }
    
    /* Alert boxes */
    .element-container .alert {
        border-radius: 8px;
        border-left: 4px solid;
        margin: 1rem 0;
    }
    
    .element-container .alert.success {
        background-color: #d4edda;
        border-left-color: #28a745;
    }
    
    .element-container .alert.warning {
        background-color: #fff3cd;
        border-left-color: #ffc107;
    }
    
    .element-container .alert.error {
        background-color: #f8d7da;
        border-left-color: #dc3545;
    }
    
    /* Plotly chart containers */
    .plotly-chart-container {
        background: white;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: white;
        border-radius: 8px;
        border: none;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Status colors */
    .status-instock { color: #FFD700; }
    .status-calibrated { color: #32CD32; }
    .status-shipped { color: #4169E1; }
    .status-scraped { color: #DC143C; }

    /* Navigation active state */
    .sidebar .nav-active {
        background-color: #e9ecef;
        border-left: 3px solid #0071ba;
    }
</style>
""", unsafe_allow_html=True)

# Add default credentials to secrets if not present
if 'credentials' not in st.secrets:
    st.secrets['credentials'] = {
        'username': 'admin@ketos.co',
        'password': 'default_password'  # Replace with your actual default password
    }

def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["username"].endswith("@ketos.co"):
            if (
                st.session_state["username"] in st.secrets["credentials"]
                and st.session_state["password"] == st.secrets["credentials"][st.session_state["username"]]
            ):
                st.session_state["password_correct"] = True
                del st.session_state["password"]  # Don't store password
                return True
            else:
                st.session_state["password_correct"] = False
                st.error("😕 User not authorized or incorrect password")
                return False
        else:
            st.error("😕 Please use your @ketos.co email address")
            return False

    if "password_correct" not in st.session_state:
        # First run, show input for password
        st.markdown("""
            <div style='text-align: center; padding: 2rem;'>
                <h1 style='color: #0071ba;'>🔬 KETOS CalMS</h1>
                <p>Probe Management System</p>
            </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.text_input("Username (@ketos.co)", key="username")
            st.text_input("Password", type="password", key="password")
            st.button("Log In", on_click=password_entered)
        return False
    
    return st.session_state["password_correct"]

def main():
    st.set_page_config(
        page_title="KETOS CalMS",
        page_icon="🔬",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    if not check_password():
        return

    # Initialize inventory manager
    if 'inventory_manager' not in st.session_state:
        st.session_state.inventory_manager = InventoryManager()
        st.session_state.inventory_manager.initialize_inventory()

    # Sidebar navigation
    st.sidebar.title("Navigation")
    
    # Show user info
    st.sidebar.markdown(f"""
        <div style='padding: 1rem; background: #f8f9fa; border-radius: 8px; margin-bottom: 1rem;'>
            <p>👤 Logged in as: {st.session_state["username"]}</p>
            <p>📊 Sheets Status: {
                "✅ Connected" if st.session_state.inventory_manager.verify_connection() 
                else "❌ Disconnected"
            }</p>
        </div>
    """, unsafe_allow_html=True)

    # Navigation options
    page = st.sidebar.radio(
        "Select Page",
        ["Dashboard", "Probe Registration", "Probe Calibration", "Inventory Review"]
    )

    # Logout button
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    # Page routing
    if page == "Dashboard":
        render_dashboard()
    elif page == "Probe Registration":
        registration_page()
    elif page == "Probe Calibration":
        calibration_page()
    elif page == "Inventory Review":
        inventory_review_page()

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
        <div style='text-align: center; color: #666;'>
            <small>Version 1.0.0 | Last Updated: 2024-12</small>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
