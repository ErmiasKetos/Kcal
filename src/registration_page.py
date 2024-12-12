# src/registration_page.py

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import logging
import time
from .inventory_manager import InventoryManager

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
    
    # Initialize inventory manager if not exists
    if 'inventory_manager' not in st.session_state:
        st.session_state.inventory_manager = InventoryManager()
        st.session_state.inventory_manager.initialize_inventory()

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
    serial_number = st.session_state.inventory_manager.get_next_serial_number(probe_type, manufacturing_date)
    
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

                    // Add an event listener for when the iframe content is loaded
                    frame.onload = function() {{
                        setTimeout(() => {{
                            frame.contentWindow.focus();
                            frame.contentWindow.print();
                        }}, 250);
                    }};
                }}
            </script>
        """, unsafe_allow_html=True)

    # Save Button
    if st.button("Register Probe"):
        if not all([manufacturer, manufacturer_part_number, ketos_part_number]):
            st.error("Please fill in all required fields.")
            return

        # Prepare probe data
        probe_data = {
            "Serial Number": serial_number,
            "Type": probe_type,
            "Manufacturer": manufacturer,
            "KETOS P/N": ketos_part_number,
            "Mfg P/N": manufacturer_part_number,
            "Status": "Instock",
            "Entry Date": datetime.now().strftime("%Y-%m-%d"),
            "Last Modified": datetime.now().strftime("%Y-%m-%d"),
            "Change Date": datetime.now().strftime("%Y-%m-%d"),
            "Calibration Data": {}
        }

        success = st.session_state.inventory_manager.add_new_probe(probe_data)
        if success:
            st.success(f"✅ Probe {serial_number} registered successfully!")
            st.session_state['last_save_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            time.sleep(1)  # Delay for user feedback
            st.rerun()
        else:
            st.error("❌ Failed to register probe.")

    # Connection Status
    if 'last_save_time' in st.session_state:
        st.sidebar.markdown(f"""
            <div style='padding: 1rem; background: #f8f9fa; border-radius: 8px; margin-top: 1rem;'>
                <p>📊 Last Sync: {st.session_state['last_save_time']}</p>
            </div>
        """, unsafe_allow_html=True)
