import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import logging
import time
from .drive_manager import DriveManager
from .inventory_manager import (
    add_new_probe,
    get_next_serial_number,
    save_inventory
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Autofill options for KETOS Part Number
KETOS_PART_NUMBERS = {
    "pH Probe": ["400-00260", "400-00292"],
    "DO Probe": ["300-00056"],
    "ORP Probe": ["400-00261"],
    "EC Probe": ["400-00259", "400-00279"],
}

# Expected Service Life for probes (in years)
SERVICE_LIFE = {
    "pH Probe": 2,
    "ORP Probe": 2,
    "DO Probe": 4,
    "EC Probe": 10,
}

def registration_page():
    """Main page for probe registration"""
    # Initialize inventory if not exists
    if 'inventory' not in st.session_state:
        st.session_state.inventory = pd.DataFrame(columns=[
            "Serial Number", "Type", "Manufacturer", "KETOS P/N",
            "Mfg P/N", "Next Calibration", "Status", "Entry Date",
            "Last Modified", "Status Color", "Change Date", "Calibration Data"
        ])

    # Sidebar for Drive settings
    with st.sidebar:
        st.markdown("### Google Drive Settings")
        if 'drive_folder_id' in st.session_state:
            st.success(f"✅ Using folder ID: {st.session_state['drive_folder_id']}")
            if st.button("Test Folder Access"):
                drive_manager = st.session_state.get('drive_manager')
                if drive_manager and drive_manager.verify_folder_access(st.session_state['drive_folder_id']):
                    st.success("✅ Folder access verified!")
                else:
                    st.error("❌ Could not access folder. Check permissions.")

            if st.button("Upload or Update Inventory"):
                if load_inventory_from_drive():
                    st.success("✅ Inventory updated successfully from Google Drive!")
                else:
                    st.error("❌ Failed to update inventory. Please check your settings.")
        else:
            st.warning("⚠️ Google Drive is not configured.")

    # Title
    st.markdown('<h1 style="font-family: Arial; color: #0071ba;">📋 Probe Registration</h1>', unsafe_allow_html=True)

    # Input Fields
    col1, col2 = st.columns(2)
    with col1:
        manufacturer = st.text_input("Manufacturer")
        manufacturing_date = st.date_input("Manufacturing Date", datetime.today())
        manufacturer_part_number = st.text_input("Manufacturer Part Number")
    with col2:
        probe_type = st.selectbox("Probe Type", ["pH Probe", "DO Probe", "ORP Probe", "EC Probe"])
        ketos_part_number = st.selectbox("KETOS Part Number", KETOS_PART_NUMBERS.get(probe_type, []))

    # Generate Serial Number
    service_years = SERVICE_LIFE.get(probe_type, 2)
    expire_date = manufacturing_date + timedelta(days=service_years * 365)
    serial_number = get_next_serial_number(probe_type, manufacturing_date)
    
    # Display Serial Number with Print Button
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"""
            <div style="font-family: Arial; font-size: 16px; padding-top: 10px;">
                Generated Serial Number: 
                <span style="font-weight: bold; color: #0071ba;">{serial_number}</span>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div style="padding-top: 10px;">
                <button onclick="printLabel()" style="padding: 5px 15px; cursor: pointer;">
                    🖨️ Print Label
                </button>
            </div>
            <iframe id="printFrame" style="display: none;"></iframe>
            <script>
                function printLabel() {{
                    const content = `
                        <html>
                            <head>
                                <style>
                                    @page {{
                                        size: 2.25in 1.25in;
                                        margin: 0;
                                    }}
                                    body {{
                                        width: 2.25in;
                                        height: 1.25in;
                                        margin: 0;
                                        display: flex;
                                        justify-content: center;
                                        align-items: center;
                                        font-family: Arial, sans-serif;
                                    }}
                                    .label {{
                                        text-align: center;
                                        font-size: 16pt;
                                        font-weight: bold;
                                    }}
                                </style>
                            </head>
                            <body>
                                <div class="label">{serial_number}</div>
                            </body>
                        </html>
                    `;
                    
                    const frame = document.getElementById('printFrame');
                    frame.contentWindow.document.open();
                    frame.contentWindow.document.write(content);
                    frame.contentWindow.document.close();
                    
                    setTimeout(() => {{
                        frame.contentWindow.focus();
                        frame.contentWindow.print();
                    }}, 250);
                }}
            </script>
        """, unsafe_allow_html=True)

    # Save Button
    if st.button("Register Probe"):
        if not all([manufacturer, manufacturer_part_number, ketos_part_number]):
            st.error("Please fill in all required fields.")
            return

        # Prepare and save probe data
        probe_data = {
            "Serial Number": serial_number,
            "Type": probe_type,
            "Manufacturer": manufacturer,
            "KETOS P/N": ketos_part_number,
            "Mfg P/N": manufacturer_part_number,
            "Status": "Pending Calibration",
            "Entry Date": datetime.now().strftime("%Y-%m-%d"),
            "Last Modified": datetime.now().strftime("%Y-%m-%d"),
            "Change Date": datetime.now().strftime("%Y-%m-%d"),
            "Calibration Data": {}  # Empty calibration data
        }

        success = add_new_probe(probe_data)
        if success:
            st.success(f"✅ Probe {serial_number} registered successfully!")
            if 'drive_manager' in st.session_state and 'drive_folder_id' in st.session_state:
                if st.session_state.drive_manager.save_to_drive(st.session_state.inventory, st.session_state.drive_folder_id):
                    st.success("✅ Inventory saved to Google Drive.")
                    st.session_state['last_save_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                else:
                    st.warning("⚠️ Failed to save to Google Drive. Data saved locally.")
            else:
                st.warning("⚠️ Google Drive not configured. Data saved locally.")
            time.sleep(1)  # Delay for user feedback
            st.rerun()
        else:
            st.error("❌ Failed to register probe.")

def load_inventory_from_drive():
    """Load the inventory CSV from Google Drive into the app's session state."""
    try:
        drive_manager = st.session_state.get("drive_manager")
        folder_id = st.session_state.get("drive_folder_id")

        if not drive_manager:
            st.error("❌ Drive Manager is not initialized. Please check your Google Drive setup.")
            return False

        if not folder_id:
            st.error("❌ Google Drive folder ID is not set. Please configure your settings.")
            return False

        # Download the file from Google Drive
        st.info("📂 Attempting to load the inventory CSV from Google Drive...")
        file_content = drive_manager.download_inventory_csv(folder_id, "wbpms_inventory_2024.csv")

        # Parse the CSV content
        existing_inventory = pd.read_csv(file_content)

        # Merge with session state inventory, avoiding duplicates
        if 'inventory' in st.session_state and not st.session_state.inventory.empty:
            st.session_state.inventory = pd.concat(
                [st.session_state.inventory, existing_inventory]
            ).drop_duplicates(subset="Serial Number", keep="last")
        else:
            st.session_state.inventory = existing_inventory

        return True
    except FileNotFoundError:
        st.warning("⚠️ Inventory file not found. A new file will be created.")
        st.session_state.inventory = pd.DataFrame(columns=[
            "Serial Number", "Type", "Manufacturer", "KETOS P/N",
            "Mfg P/N", "Next Calibration", "Status", "Entry Date",
            "Last Modified", "Change Date", "Calibration Data"
        ])
        return True
    except pd.errors.EmptyDataError:
        st.warning("⚠️ Inventory file is empty. Starting with a new inventory.")
        st.session_state.inventory = pd.DataFrame(columns=[
            "Serial Number", "Type", "Manufacturer", "KETOS P/N",
            "Mfg P/N", "Next Calibration", "Status", "Entry Date",
            "Last Modified", "Change Date", "Calibration Data"
        ])
        return True
    except Exception as e:
        st.error(f"❌ Failed to load inventory. Error: {e}")
        return False
