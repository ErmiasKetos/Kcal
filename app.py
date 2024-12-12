# app.py
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

# Modern UI Styling
st.markdown("""
<style>
    /* Modern color scheme */
    :root {
        --primary-color: #0071ba;
        --secondary-color: #00487c;
        --accent-color: #00a6fb;
        --background-color: #f8f9fa;
        --card-color: #ffffff;
        --text-color: #2c3e50;
        --success-color: #28a745;
        --warning-color: #ffc107;
        --error-color: #dc3545;
    }

    /* Main app container */
    .stApp {
        background: linear-gradient(135deg, var(--background-color), #e9ecef);
    }

    /* Sidebar styling */
    .css-1d391kg {
        background-color: var(--card-color);
        border-right: 1px solid rgba(0,0,0,0.1);
    }

    /* Sidebar nav items */
    .sidebar-nav-item {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
        transition: all 0.3s ease;
        cursor: pointer;
    }

    .sidebar-nav-item:hover {
        background-color: rgba(0,113,186,0.1);
        transform: translateX(5px);
    }

    .sidebar-nav-item.active {
        background-color: var(--primary-color);
        color: white;
    }

    /* Cards styling */
    .stCard {
        background: var(--card-color);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        border: 1px solid rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }

    .stCard:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(45deg, var(--primary-color), var(--accent-color));
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,113,186,0.3);
    }

    /* Input fields */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }

    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 2px rgba(0,113,186,0.2);
    }

    /* Headers */
    h1, h2, h3 {
        color: var(--text-color);
        font-weight: 600;
        margin-bottom: 1.5rem;
    }

    /* Status badges */
    .status-badge {
        padding: 0.25rem 1rem;
        border-radius: 15px;
        font-weight: 500;
        text-align: center;
        display: inline-block;
    }

    /* Metrics */
    .css-1r6slb0 {
        background: var(--card-color);
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: var(--background-color);
    }

    ::-webkit-scrollbar-thumb {
        background: var(--primary-color);
        border-radius: 4px;
    }

    /* Loader animation */
    .stSpinner > div {
        border-color: var(--primary-color);
    }

    /* Toast notifications */
    .element-container .alert {
        border-radius: 10px;
        border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'Dashboard'

def create_sidebar():
    """Create modern sidebar with navigation."""
    with st.sidebar:
        # Logo and app title
        st.markdown("""
            <div style='text-align: center; padding: 1rem;'>
                <h1 style='color: #0071ba; font-size: 24px; margin-bottom: 0;'>🔬 KETOS CalMS</h1>
                <p style='color: #666; font-size: 14px;'>Probe Management System</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")

        # User info if logged in
        if 'username' in st.session_state and st.session_state.username:
            st.markdown(f"""
                <div style='padding: 1rem; background: #f8f9fa; border-radius: 10px; margin-bottom: 2rem;'>
                    <div style='display: flex; align-items: center; margin-bottom: 0.5rem;'>
                        <div style='width: 40px; height: 40px; background: #0071ba; border-radius: 20px; 
                             color: white; display: flex; align-items: center; justify-content: center; 
                             margin-right: 10px;'>
                            {st.session_state.username[0].upper()}
                        </div>
                        <div>
                            <p style='margin: 0; font-weight: 500;'>{st.session_state.username}</p>
                            <small style='color: #666;'>Logged in</small>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # Navigation menu
        pages = {
            "Dashboard": "📊",
            "Probe Registration": "📝",
            "Probe Calibration": "🔍",
            "Inventory Review": "📦"
        }

        for page_name, icon in pages.items():
            button_class = "active" if st.session_state.page == page_name else ""
            if st.sidebar.button(
                f"{icon} {page_name}",
                key=f"nav_{page_name}",
                use_container_width=True,
                help=f"Navigate to {page_name}"
            ):
                st.session_state.page = page_name
                st.rerun()

        st.markdown("---")

        # System status
        if 'inventory_manager' in st.session_state:
            connection_status = st.session_state.inventory_manager.verify_connection()
            status_color = "#28a745" if connection_status else "#dc3545"
            st.markdown(f"""
                <div style='padding: 1rem; background: #f8f9fa; border-radius: 10px; margin-bottom: 1rem;'>
                    <h4 style='margin: 0; font-size: 14px; color: #666;'>System Status</h4>
                    <div style='display: flex; align-items: center; margin-top: 0.5rem;'>
                        <div style='width: 8px; height: 8px; border-radius: 4px; 
                                  background: {status_color}; margin-right: 8px;'></div>
                        <span style='font-size: 14px;'>
                            {"Connected" if connection_status else "Disconnected"}
                        </span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # Logout button
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()

        # Footer
        st.markdown("""
            <div style='position: fixed; bottom: 0; left: 0; width: 100%; 
                      padding: 1rem; text-align: center; font-size: 12px; color: #666;'>
                <p style='margin: 0;'>Version 1.0.0</p>
                <p style='margin: 0;'>Last Updated: 2024-12</p>
            </div>
        """, unsafe_allow_html=True)

def main():
    # Initialize session state
    if 'inventory_manager' not in st.session_state:
        st.session_state.inventory_manager = InventoryManager()
        st.session_state.inventory_manager.initialize_inventory()

    # Create sidebar
    create_sidebar()

    # Main content
    if not st.session_state.get('password_correct', False):
        # Login page
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
                <div style='background: white; padding: 2rem; border-radius: 15px; 
                          box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center;'>
                    <h1 style='color: #0071ba; margin-bottom: 2rem;'>🔬 Welcome to KETOS CalMS</h1>
                    <p style='color: #666; margin-bottom: 2rem;'>
                        Please log in with your KETOS credentials to continue.
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            with st.form("login_form"):
                username = st.text_input("Email (@ketos.co)")
                password = st.text_input("Password", type="password")
                
                if st.form_submit_button("Login", use_container_width=True):
                    if username.endswith("@ketos.co"):
                        if (
                            username in st.secrets["credentials"]
                            and password == st.secrets["credentials"][username]
                        ):
                            st.session_state.password_correct = True
                            st.session_state.username = username
                            st.rerun()
                        else:
                            st.error("Invalid credentials")
                    else:
                        st.error("Please use your @ketos.co email")
    else:
        # Render appropriate page based on navigation
        if st.session_state.page == "Dashboard":
            render_dashboard()
        elif st.session_state.page == "Probe Registration":
            registration_page()
        elif st.session_state.page == "Probe Calibration":
            calibration_page()
        elif st.session_state.page == "Inventory Review":
            inventory_review_page()

if __name__ == "__main__":
    main()
