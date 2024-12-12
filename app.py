
import streamlit as st

# Must be the first Streamlit command
st.set_page_config(
    page_title="KETOS CalMS",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

# Custom CSS
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
    .stCard {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: transform 0.2s ease;
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
    
    /* Metrics */
    .stMetric {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    /* Data tables */
    .dataframe {
        border: none !important;
        border-collapse: collapse !important;
    }
    
    .dataframe th {
        background-color: #f8f9fa !important;
        padding: 12px !important;
        border-bottom: 2px solid #dee2e6 !important;
    }
    
    .dataframe td {
        padding: 12px !important;
        border-bottom: 1px solid #e9ecef !important;
    }

    /* Status colors */
    .status-instock { background-color: #FFD70040 !important; }
    .status-calibrated { background-color: #32CD3240 !important; }
    .status-shipped { background-color: #4169E140 !important; }
    .status-scraped { background-color: #DC143C40 !important; }

    /* Login container */
    .login-container {
        max-width: 400px;
        margin: 2rem auto;
        padding: 2rem;
        background: white;
        border-radius: 10px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)


# Add default credentials to secrets if not present
if 'credentials' not in st.secrets:
    st.secrets['credentials'] = {
        'username': 'admin@ketos.co',
        'password': 'default_password'  # Replace with your actual default password
    }

def initialize_session_state():
    """Initialize session state variables."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'inventory_manager' not in st.session_state:
        st.session_state.inventory_manager = None
    if 'page' not in st.session_state:
        st.session_state.page = 'Dashboard'
    if 'selected_probe' not in st.session_state:
        st.session_state.selected_probe = None
    if 'selected_row' not in st.session_state:
        st.session_state.selected_row = None

def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["username_input"].endswith("@ketos.co"):
            if (
                st.session_state["username_input"] in st.secrets["credentials"]
                and st.session_state["password_input"] == st.secrets["credentials"][st.session_state["username_input"]]
            ):
                st.session_state.authenticated = True
                st.session_state.username = st.session_state["username_input"]
                del st.session_state["password_input"]  # Don't store password
                return True
            else:
                st.session_state.authenticated = False
                st.error("😕 User not authorized or incorrect password")
                return False
        else:
            st.error("😕 Please use your @ketos.co email address")
            return False

    if not st.session_state.get("authenticated", False):
        st.markdown("""
            <div class='login-container'>
                <h1 style='text-align: center; color: #0071ba;'>🔬 KETOS CalMS</h1>
                <p style='text-align: center;'>Probe Management System</p>
            </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.text_input("Username (@ketos.co)", key="username_input")
            st.text_input("Password", type="password", key="password_input")
            st.button("Log In", on_click=password_entered)
        return False
    
    return True

def main():
    initialize_session_state()

    if not check_password():
        return

    # Initialize inventory manager if needed
    if not st.session_state.inventory_manager:
        st.session_state.inventory_manager = InventoryManager()
        st.session_state.inventory_manager.initialize_inventory()

    # Verify Google Sheets connection
    if not st.session_state.inventory_manager.verify_connection():
        st.error("❌ Unable to connect to Google Sheets. Please check your connection and try again.")
        return

    # Sidebar navigation
    st.sidebar.title("Navigation")
    
    # Show user info
    st.sidebar.markdown(f"""
        <div style='padding: 1rem; background: #f8f9fa; border-radius: 8px; margin-bottom: 1rem;'>
            <p>👤 Logged in as: {st.session_state.username}</p>
            <p>📊 Sheets Status: ✅ Connected</p>
        </div>
    """, unsafe_allow_html=True)

    # Navigation options
    if st.session_state.get('page') == "Probe Calibration":
        page = "Probe Calibration"
    else:
        page = st.sidebar.radio(
            "Select Page",
            ["Dashboard", "Probe Registration", "Probe Calibration", "Inventory Review"]
        )

    # Logout button
    if st.sidebar.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    # Page routing
    try:
        if page == "Dashboard":
            render_dashboard()
        elif page == "Probe Registration":
            registration_page()
        elif page == "Probe Calibration":
            calibration_page()
        elif page == "Inventory Review":
            inventory_review_page()
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        logger.error(f"Page routing error: {str(e)}")

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
        <div style='text-align: center; color: #666;'>
            <small>Version 1.0.0 | Last Updated: 2024-12</small>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
