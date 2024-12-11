import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from src.dashboard import render_dashboard
import logging
import os
from datetime import datetime
from src.drive_manager import DriveManager
from src.inventory_review import inventory_review_page
from src.inventory_manager import initialize_inventory
from src.registration_page import registration_page  
from src.calibration_page import calibration_page   # Updated import

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default Google Drive folder ID
DRIVE_FOLDER_ID = "19lHngxB_RXEpr30jpY9_fCaSpl6Z1m1i"

# OAuth 2.0 configuration
SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]

# Verify environment variables
if not os.environ.get("GOOGLE_CLIENT_ID") or not os.environ.get("GOOGLE_CLIENT_SECRET"):
    raise EnvironmentError("Missing required environment variables: GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET")

# Client configuration
CLIENT_CONFIG = {
    "web": {
        "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
        "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["https://caldash-eoewkytd6u7jyxfm2haaxn.streamlit.app/"],
        "javascript_origins": ["https://caldash-eoewkytd6u7jyxfm2haaxn.streamlit.app"]
    }
}

def init_google_auth():
    """Initialize Google authentication."""
    try:
        # Use updated query_params instead of experimental_get_query_params
        params = st.query_params
        if 'code' not in params:
            return False

        flow = Flow.from_client_config(
            client_config=CLIENT_CONFIG,
            scopes=SCOPES,
            redirect_uri="https://caldash-eoewkytd6u7jyxfm2haaxn.streamlit.app/"
        )

        flow.fetch_token(code=params['code'])
        st.session_state['credentials'] = flow.credentials

        # Initialize Drive manager
        if 'drive_manager' not in st.session_state:
            st.session_state.drive_manager = DriveManager()
        st.session_state.drive_manager.authenticate(flow.credentials)
        
        # Initialize inventory
        if 'inventory' not in st.session_state:
            initialize_inventory()

        # Set authenticated state
        st.session_state['authenticated'] = True
        st.session_state['drive_folder_id'] = DRIVE_FOLDER_ID

        # Clear query parameters
        st.query_params.clear()
        
        logger.info("Authentication successful")
        return True

    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        if 'credentials' in st.session_state:
            del st.session_state['credentials']
        return False

def check_user_auth():
    """Check and handle user authentication"""
    if 'credentials' not in st.session_state:
        try:
            flow = Flow.from_client_config(
                client_config=CLIENT_CONFIG,
                scopes=SCOPES,
                redirect_uri="https://caldash-eoewkytd6u7jyxfm2haaxn.streamlit.app/"
            )
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            st.session_state['oauth_state'] = state
            st.markdown(f"[Login with Google]({authorization_url})")
            return False
        except Exception as e:
            logger.error(f"Auth setup error: {str(e)}")
            st.error(f"Auth setup error: {str(e)}")
            return False
    return True

def main():
    try:
        st.sidebar.title("CalMS")

        # Handle OAuth flow
        params = st.query_params
        if 'code' in params and 'authenticated' not in st.session_state:
            if init_google_auth():
                st.rerun()
            return

        # Check authentication
        if not check_user_auth():
            st.write("Please log in to access the application.")
            return

        # Validate user email domain
        try:
            user_info_service = build('oauth2', 'v2', credentials=st.session_state['credentials'])
            user_info = user_info_service.userinfo().get().execute()

            if user_info['email'].endswith('@ketos.co'):
                st.sidebar.text(f"Logged in as: {user_info['name']}")
            else:
                st.error("Access denied. Please use your @ketos.co email.")
                if st.button("Logout"):
                    st.session_state.clear()
                    st.rerun()
                return
        except Exception as e:
            logger.error(f"Error fetching user info: {str(e)}")
            st.error("Authentication error. Please try logging in again.")
            st.session_state.clear()
            st.rerun()
            return

        # Debug information
        with st.sidebar.expander("Debug Info", expanded=False):
            st.write({
                "Authentication Status": 'credentials' in st.session_state,
                "Drive Connected": 'drive_manager' in st.session_state,
                "Inventory Loaded": 'inventory' in st.session_state,
                "Email": user_info.get('email', 'Not available')
            })

        # Updated sidebar navigation with separate registration and calibration pages
        page = st.sidebar.radio(
            "Navigate to",
            ["Dashboard", "Probe Registration", "Probe Calibration", "Inventory Review"]
        )

        # Page routing
        if page == "Probe Registration":
            registration_page()
        elif page == "Dashboard":
            render_dashboard()
        elif page == "Probe Registration":
            registration_page()
        elif page == "Probe Calibration":
            calibration_page()
        elif page == "Inventory Review":
            inventory_review_page()

    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    st.set_page_config(
        page_title="Probe Management System",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    main()
