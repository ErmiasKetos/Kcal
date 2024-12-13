
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
    st.markdown(f"""
        <style>
            .serial-container {{
                background: white;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                margin: 20px 0;
            }}
            .serial-number {{
                color: #0071ba;
                font-size: 24px;
                font-weight: bold;
                font-family: monospace;
                padding: 10px;
                background: #f8f9fa;
                border-radius: 5px;
                margin: 10px 0;
            }}
            .print-button {{
                background: #0071ba;
                color: white;
                padding: 8px 16px;
                border-radius: 5px;
                border: none;
                cursor: pointer;
                display: inline-flex;
                align-items: center;
                gap: 8px;
            }}
            .print-button:hover {{
                background: #005999;
            }}
            @media print {{
                body * {{
                    visibility: hidden;
                }}
                #printable-content, #printable-content * {{
                    visibility: visible;
                }}
                #printable-content {{
                    position: absolute;
                    left: 0;
                    top: 0;
                    width: 2.25in;
                    height: 1.25in;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                .print-serial {{
                    font-family: monospace;
                    font-size: 16pt;
                    font-weight: bold;
                }}
            }}
        </style>
    
        <div class="serial-container">
            <div>Generated Serial Number:</div>
            <div class="serial-number">{serial_number}</div>
            <button onclick="printSerialNumber('{serial_number}')" class="print-button">
                🖨️ Print Label
            </button>
        </div>
    
        <div id="printable-content" style="display: none;">
            <div class="print-serial">{serial_number}</div>
        </div>
    
        <script>
            function printSerialNumber(serialNumber) {{
                var printWindow = window.open('', '', 'width=600,height=600');
                printWindow.document.write(`
                    <html>
                        <head>
                            <style>
                                @page {{
                                    size: 2.25in 1.25in;
                                    margin: 0;
                                }}
                                body {{
                                    margin: 0;
                                    display: flex;
                                    justify-content: center;
                                    align-items: center;
                                    height: 1.25in;
                                }}
                                .serial {{
                                    font-family: monospace;
                                    font-size: 16pt;
                                    font-weight: bold;
                                    text-align: center;
                                }}
                            </style>
                        </head>
                        <body>
                            <div class="serial">${serialNumber}</div>
                        </body>
                    </html>
                `);
                printWindow.document.close();
                printWindow.focus();
                setTimeout(() => {{
                    printWindow.print();
                    printWindow.close();
                }}, 250);
            }}
        </script>
    """, unsafe_allow_html=True)

    
    # Save Button with improved styling
    st.markdown("""
        <style>
            .stButton > button {
                background: #0071ba;
                color: white;
                font-weight: 500;
                padding: 0.5rem 1rem;
                width: 100%;
                transition: all 0.3s ease;
            }
            .stButton > button:hover {
                background: #005999;
                transform: translateY(-2px);
            }
        </style>
    """, unsafe_allow_html=True)

    if st.button("Register Probe", type="primary"):
        if not all([manufacturer, manufacturer_part_number, ketos_part_number]):
            st.error("❌ Please fill in all required fields.")
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
            "Calibration Data": {},
            "Registered By": st.session_state.get('username', 'Unknown')  # Added registered by field
        }

        success = st.session_state.inventory_manager.add_new_probe(probe_data)
        if success:
            st.success(f"✅ Probe {serial_number} registered successfully!")
            st.session_state['last_save_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            time.sleep(1)
            st.rerun()
        else:
            st.error("❌ Failed to register probe.")

    # Connection Status
    if 'last_save_time' in st.session_state:
        st.sidebar.markdown(f"""
            <div style='padding: 1rem; background: #f8f9fa; border-radius: 8px; margin-top: 1rem;'>
                <h4 style='margin: 0; color: #0071ba; font-size: 14px;'>System Status</h4>
                <div style='display: flex; align-items: center; margin-top: 0.5rem;'>
                    <div style='width: 8px; height: 8px; border-radius: 50%; 
                              background: #28a745; margin-right: 8px;'></div>
                    <span style='font-size: 14px;'>Last Sync: {st.session_state['last_save_time']}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    registration_page()
