# app.py - Ensure this is at the very top
import streamlit as st

# Must be the first Streamlit command
st.set_page_config(
    page_title="KETOS CalMS",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Other imports
import pandas as pd
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom CSS
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(to bottom right, #f8f9fa, #e9ecef);
    }
    .sidebar .sidebar-content {
        background-color: #ffffff;
        border-right: 1px solid #dee2e6;
    }
    .main .block-container {
        padding: 2rem;
        background: linear-gradient(to bottom, #ffffff, #f8f9fa);
        border-radius: 10px;
        box-shadow: 0 2px 15px rgba(0,0,0,0.05);
    }
    .stButton > button {
        background-color: #0071ba;
        color: white;
        border-radius: 4px;
        padding: 0.5rem 1rem;
    }
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

# Initialize session state
if 'username' not in st.session_state:
    st.session_state.username = None
if 'password_correct' not in st.session_state:
    st.session_state.password_correct = False
if 'inventory_manager' not in st.session_state:
    st.session_state.inventory_manager = None

def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        if st.session_state["username_input"].endswith("@ketos.co"):
            if (
                st.session_state["username_input"] in st.secrets["credentials"]
                and st.session_state["password_input"] == st.secrets["credentials"][st.session_state["username_input"]]
            ):
                st.session_state.password_correct = True
                st.session_state.username = st.session_state["username_input"]
                del st.session_state["password_input"]
                return True
            else:
                st.session_state.password_correct = False
                st.error("😕 User not authorized or incorrect password")
                return False
        else:
            st.error("😕 Please use your @ketos.co email address")
            return False

    if not st.session_state.get("password_correct", False):
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
    if not check_password():
        return

    # Import other modules only after authentication
    from src.dashboard import render_dashboard
    from src.inventory_review import inventory_review_page
    from src.inventory_manager import InventoryManager
    from src.registration_page import registration_page
    from src.calibration_page import calibration_page

    # Initialize inventory manager
    if not st.session_state.inventory_manager:
        st.session_state.inventory_manager = InventoryManager()
        st.session_state.inventory_manager.initialize_inventory()

    # Verify Google Sheets connection
    if not st.session_state.inventory_manager.verify_connection():
        st.error("❌ Unable to connect to Google Sheets. Please check your connection and try again.")
        return

    # Sidebar navigation
    st.sidebar.title("Navigation")
    
    if st.session_state.username:
        st.sidebar.markdown(f"""
            <div style='padding: 1rem; background: #f8f9fa; border-radius: 8px; margin-bottom: 1rem;'>
                <p>👤 Logged in as: {st.session_state.username}</p>
                <p>📊 Sheets Status: ✅ Connected</p>
            </div>
        """, unsafe_allow_html=True)

    # Navigation
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
