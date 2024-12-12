import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import logging
import time
import json
import numpy as np

logger = logging.basicConfig(level=logging.INFO)

# Constants for validation
PH_RANGES = {
    "pH 4": (3.8, 4.2),
    "pH 7": (6.8, 7.2),
    "pH 10": (9.8, 10.2)
}

DO_RANGES = {
    "0%": (-0.1, 0.5),
    "100%": (95.0, 105.0)
}

ORP_RANGES = {
    "mV": (200, 275)  # For 225mV standard solution
}

EC_RANGES = {
    "84": (80, 88),       # 84 µS/cm
    "1413": (1390, 1436), # 1413 µS/cm
    "12880": (12750, 13010) # 12.88 mS/cm
}

def validate_reading(value, range_min, range_max, reading_type):
    """Validate if a reading is within acceptable range."""
    try:
        float_value = float(value)
        if range_min <= float_value <= range_max:
            return True
        st.warning(f"{reading_type} reading ({float_value}) is outside expected range ({range_min}-{range_max})")
        return False
    except ValueError:
        st.error(f"Invalid {reading_type} reading: {value}")
        return False

def get_searchable_probes():
    """Enhanced probe search functionality."""
    if 'inventory_manager' not in st.session_state:
        return []
    
    inventory_df = st.session_state.inventory
    if inventory_df is None or inventory_df.empty:
        return []
        
    searchable_probes = []
    
    for _, row in inventory_df.iterrows():
        # Enhance probe info with more details
        calibration_status = "Never Calibrated"
        days_since_cal = "N/A"
        
        if 'Calibration Data' in row and row['Calibration Data']:
            try:
                cal_data = json.loads(row['Calibration Data'])
                if 'calibration_date' in cal_data:
                    cal_date = datetime.strptime(cal_data['calibration_date'], "%Y-%m-%d")
                    days_since_cal = (datetime.now() - cal_date).days
                    calibration_status = f"Calibrated {days_since_cal} days ago"
            except:
                calibration_status = "Error loading calibration data"

        probe_info = {
            'serial': row['Serial Number'],
            'type': row['Type'],
            'manufacturer': row['Manufacturer'],
            'status': row['Status'],
            'display': f"{row['Serial Number']} - {row['Type']} ({row['Status']})",
            'search_text': f"{row['Serial Number']} {row['Type']} {row['Manufacturer']} {row['Status']}",
            'ketos_pn': row.get('KETOS P/N', 'N/A'),
            'mfg_pn': row.get('Mfg P/N', 'N/A'),
            'entry_date': row.get('Entry Date', 'N/A'),
            'calibration_status': calibration_status,
            'days_since_cal': days_since_cal
        }
        searchable_probes.append(probe_info)
    
    return searchable_probes

def render_autocomplete_search():
    """Enhanced autocomplete search with advanced filtering."""
    probes = get_searchable_probes()
    
    if not probes:
        st.warning("No probes found in inventory. Please add probes first.")
        return None
    
    # Advanced search options
    col1, col2 = st.columns([2, 1])
    with col1:
        search_query = st.text_input(
            "🔍 Search Probe",
            key="probe_search",
            placeholder="Enter Serial Number, Type, or Manufacturer...",
        ).strip().lower()
    
    with col2:
        status_filter = st.multiselect(
            "Filter by Status",
            options=["Instock", "Calibrated", "Shipped", "Scraped"],
            default=["Instock"]
        )
    
    # Filter probes based on search query and status
    if search_query or status_filter:
        filtered_probes = [
            probe for probe in probes
            if (not search_query or search_query in probe['search_text'].lower()) and
               (not status_filter or probe['status'] in status_filter)
        ]
        
        if filtered_probes:
            st.markdown("#### Matching Probes")
            
            # Create a styled table for probe display
            for probe in filtered_probes:
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                    
                    with col1:
                        st.markdown(f"""
                            <div style='padding: 10px; background: #f8f9fa; border-radius: 5px;'>
                                <strong>{probe['serial']}</strong><br/>
                                {probe['type']}
                            </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        status_color = {
                            'Instock': '#FFD700',
                            'Calibrated': '#90EE90',
                            'Shipped': '#87CEEB',
                            'Scraped': '#FFB6C6'
                        }.get(probe['status'], '#FFFFFF')
                        
                        st.markdown(f"""
                            <div style='padding: 10px; background: {status_color}; border-radius: 5px;'>
                                Status: {probe['status']}<br/>
                                {probe['calibration_status']}
                            </div>
                        """, unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown(f"""
                            <div style='padding: 10px; background: #f8f9fa; border-radius: 5px;'>
                                KETOS P/N: {probe['ketos_pn']}<br/>
                                Entry: {probe['entry_date']}
                            </div>
                        """, unsafe_allow_html=True)
                    
                    with col4:
                        if st.button("Select", key=f"select_{probe['serial']}"):
                            return probe['serial']
                    
                    st.markdown("---")
        else:
            st.info("No matching probes found.")
    
    return None


def render_ph_calibration():
    """Render modern pH probe calibration form."""
    # Custom CSS for pH calibration
    st.markdown("""
        <style>
            .buffer-card {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 20px;
                transition: all 0.3s ease;
            }
            .buffer-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            }
            .buffer-title {
                font-size: 1.2em;
                font-weight: bold;
                margin-bottom: 15px;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .reading-section {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 10px;
            }
            .ph-header {
                background: linear-gradient(90deg, #0071ba, #00a6fb);
                color: white;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 20px;
                text-align: center;
            }
            .buffer-ph7 { border-left: 4px solid #FFD700; }
            .buffer-ph4 { border-left: 4px solid #FF6B6B; }
            .buffer-ph10 { border-left: 4px solid #4ECDC4; }
            .info-text {
                font-size: 0.9em;
                color: #666;
                margin-top: 5px;
            }
        </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
        <div class='ph-header'>
            <h2 style='margin:0;'>🧪 pH Probe Calibration</h2>
            <p style='margin:0; margin-top:5px; font-size:0.9em;'>
                Three-point calibration using pH 4, 7, and 10 buffers
            </p>
        </div>
    """, unsafe_allow_html=True)

    ph_data = {}

    # Temperature Measurement
    st.markdown("### 🌡️ Temperature Settings")
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            ph_data['temperature'] = st.number_input(
                "Solution Temperature (°C)",
                min_value=10.0,
                max_value=40.0,
                value=25.0,
                step=0.1,
                help="Maintain temperature between 10-40°C for accurate calibration"
            )

    # Buffer Solutions
    buffer_configs = [
        {
            "name": "pH 7",
            "class": "buffer-ph7",
            "icon": "⚖️",
            "desc": "Start with pH 7 (Neutral) buffer",
            "color": "#FFD700"
        },
        {
            "name": "pH 4",
            "class": "buffer-ph4",
            "icon": "🔴",
            "desc": "Followed by pH 4 (Acidic) buffer",
            "color": "#FF6B6B"
        },
        {
            "name": "pH 10",
            "class": "buffer-ph10",
            "icon": "🔵",
            "desc": "Finally pH 10 (Basic) buffer",
            "color": "#4ECDC4"
        }
    ]

    for buffer in buffer_configs:
        st.markdown(f"### {buffer['icon']} {buffer['name']} Buffer Solution")
        st.markdown(f"<div class='buffer-card {buffer['class']}'>", unsafe_allow_html=True)
        
        # Buffer Information
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("#### 📋 Buffer Information")
            ph_data[f"{buffer['name']}_control"] = st.text_input(
                "Control Number",
                key=f"{buffer['name']}_control",
                help="Enter the buffer solution control number"
            )
            ph_data[f"{buffer['name']}_exp"] = st.date_input(
                "Expiration Date",
                key=f"{buffer['name']}_exp",
                help="Buffer solution expiration date"
            )
            ph_data[f"{buffer['name']}_opened"] = st.date_input(
                "Date Opened",
                key=f"{buffer['name']}_opened",
                help="Date when the buffer was opened"
            )

        with col2:
            st.markdown("#### 📊 Measurements")
            with st.container():
                st.markdown('<div class="reading-section">', unsafe_allow_html=True)
                
                measurement_cols = st.columns(2)
                with measurement_cols[0]:
                    ph_data[f"{buffer['name']}_initial"] = st.number_input(
                        "Initial Reading (pH)",
                        min_value=0.0,
                        max_value=14.0,
                        step=0.01,
                        key=f"{buffer['name']}_initial_ph",
                        help=f"Initial pH reading for {buffer['name']} buffer"
                    )
                    ph_data[f"{buffer['name']}_initial_mv"] = st.number_input(
                        "Initial mV",
                        min_value=-2000.0,
                        max_value=2000.0,
                        step=0.1,
                        key=f"{buffer['name']}_initial_mv",
                        help="Initial millivolt reading"
                    )
                
                with measurement_cols[1]:
                    ph_data[f"{buffer['name']}_calibrated"] = st.number_input(
                        "Final Reading (pH)",
                        min_value=0.0,
                        max_value=14.0,
                        step=0.01,
                        key=f"{buffer['name']}_final_ph",
                        help=f"Final calibrated pH reading for {buffer['name']} buffer"
                    )
                    ph_data[f"{buffer['name']}_calibrated_mv"] = st.number_input(
                        "Final mV",
                        min_value=-2000.0,
                        max_value=2000.0,
                        step=0.1,
                        key=f"{buffer['name']}_final_mv",
                        help="Final calibrated millivolt reading"
                    )
                st.markdown('</div>', unsafe_allow_html=True)

        # Expected Range Info
        st.markdown(f"""
            <div class='info-text'>
                {buffer['desc']}
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

    return ph_data
def render_do_calibration():
    """Render DO probe calibration form with validation."""
    st.markdown('<h3 style="color: #0071ba;">DO Calibration</h3>', unsafe_allow_html=True)
    do_data = {}

    # Temperature and Atmospheric Pressure
    col1, col2 = st.columns(2)
    with col1:
        do_data['temperature'] = st.number_input(
            "Solution Temperature (°C)",
            min_value=0.0,
            max_value=50.0,
            value=25.0,
            step=0.1
        )
    with col2:
        do_data['pressure'] = st.number_input(
            "Atmospheric Pressure (mmHg)",
            min_value=500.0,
            max_value=800.0,
            value=760.0,
            step=0.1
        )

    # Zero point calibration
    st.markdown("""
        <div style="background-color: #f8f1f1; border: 1px solid #ccc; 
        padding: 15px; border-radius: 8px; margin-bottom: 15px;">
        <h4>Zero Point Calibration (0% DO)</h4>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        do_data['zero_control'] = st.text_input("Zero Solution Control Number")
        do_data['zero_exp'] = st.date_input(
            "Zero Solution Expiration Date",
            min_value=date.today()
        )
    with col2:
        do_data['zero_initial'] = st.number_input(
            "Initial Reading (%)",
            min_value=-0.1,
            max_value=100.0,
            step=0.1
        )
        do_data['zero_final'] = st.number_input(
            "Final Reading (%)",
            min_value=-0.1,
            max_value=100.0,
            step=0.1
        )
    st.markdown('</div>', unsafe_allow_html=True)

    # Saturation point calibration
    st.markdown("""
        <div style="background-color: #e8f8f2; border: 1px solid #ccc;
        padding: 15px; border-radius: 8px; margin-bottom: 15px;">
        <h4>Saturation Point Calibration (100% DO)</h4>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        do_data['sat_initial'] = st.number_input(
            "Initial Reading (%)",
            min_value=0.0,
            max_value=200.0,
            step=0.1,
            key="sat_initial"
        )
        do_data['sat_final'] = st.number_input(
            "Final Reading (%)",
            min_value=0.0,
            max_value=200.0,
            step=0.1,
            key="sat_final"
        )
    with col2:
        do_data['sat_mg_l'] = st.number_input(
            "mg/L Reading",
            min_value=0.0,
            max_value=20.0,
            step=0.1
        )
        do_data['sat_temp'] = st.number_input(
            "Temperature (°C)",
            min_value=0.0,
            max_value=50.0,
            step=0.1,
            key="sat_temp"
        )
    st.markdown('</div>', unsafe_allow_html=True)
    
    return do_data

def render_orp_calibration():
    """Render ORP probe calibration form with validation."""
    st.markdown('<h3 style="color: #0071ba;">ORP Calibration</h3>', unsafe_allow_html=True)
    orp_data = {}

    st.markdown("""
        <div style="background-color: #f8f1f1; border: 1px solid #ccc;
        padding: 15px; border-radius: 8px; margin-bottom: 15px;">
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        orp_data['temperature'] = st.number_input(
            "Solution Temperature (°C)",
            min_value=0.0,
            max_value=50.0,
            value=25.0,
            step=0.1
        )
        orp_data['control_number'] = st.text_input("Control Number")
        orp_data['lot_number'] = st.text_input("Lot Number")
        orp_data['expiration'] = st.date_input(
            "Solution Expiration Date",
            min_value=date.today()
        )
    
    with col2:
        orp_data['standard_value'] = st.number_input(
            "Standard Solution Value (mV)",
            value=225.0,
            step=0.1
        )
        orp_data['initial_mv'] = st.number_input(
            "Initial Reading (mV)",
            min_value=-2000.0,
            max_value=2000.0,
            step=0.1
        )
        orp_data['final_mv'] = st.number_input(
            "Final Reading (mV)",
            min_value=-2000.0,
            max_value=2000.0,
            step=0.1
        )

    st.markdown('</div>', unsafe_allow_html=True)
    return orp_data

def render_ec_calibration():
    """Render EC probe calibration form with validation."""
    st.markdown('<h3 style="color: #0071ba;">EC Calibration</h3>', unsafe_allow_html=True)
    ec_data = {}

    # Temperature measurement
    col1, col2 = st.columns(2)
    with col1:
        ec_data['temperature'] = st.number_input(
            "Solution Temperature (°C)",
            min_value=10.0,
            max_value=40.0,
            value=25.0,
            step=0.1
        )

    # Calibration points
    standards = [
        ("84 µS/cm", "#f8f1f1"),
        ("1413 µS/cm", "#e8f8f2"),
        ("12.88 mS/cm", "#e8f0f8")
    ]

    for std, color in standards:
        st.markdown(
            f'<div style="background-color: {color}; border: 1px solid #ccc; '
            f'padding: 15px; border-radius: 8px; margin-bottom: 15px;">',
            unsafe_allow_html=True
        )
        
        st.markdown(f"#### {std} Standard")
        col1, col2 = st.columns(2)
        
        key_prefix = std.split()[0]
        
        with col1:
            ec_data[f"{key_prefix}_control"] = st.text_input(
                "Control Number",
                key=f"ec_{key_prefix}_control"
            )
            ec_data[f"{key_prefix}_lot"] = st.text_input(
                "Lot Number",
                key=f"ec_{key_prefix}_lot"
            )
            ec_data[f"{key_prefix}_exp"] = st.date_input(
                "Expiration Date",
                min_value=date.today(),
                key=f"ec_{key_prefix}_exp"
            )
        
        with col2:
            ec_data[f"{key_prefix}_initial"] = st.number_input(
                "Initial Reading",
                min_value=0.0,
                step=0.1,
                key=f"ec_{key_prefix}_initial"
            )
            ec_data[f"{key_prefix}_final"] = st.number_input(
                "Final Reading",
                min_value=0.0,
                step=0.1,
                key=f"ec_{key_prefix}_final"
            )
            ec_data[f"{key_prefix}_temp"] = st.number_input(
                "Temperature (°C)",
                min_value=0.0,
                max_value=50.0,
                value=25.0,
                step=0.1,
                key=f"ec_{key_prefix}_temp"
            )

        st.markdown('</div>', unsafe_allow_html=True)
    
    return ec_data
# src/calibration_page.py - Part 3: Main Calibration Logic

def validate_calibration_data(probe_type, calibration_data):
    """Validate calibration data based on probe type."""
    errors = []
    
    # Common validations
    if 'temperature' in calibration_data:
        temp = float(calibration_data['temperature'])
        if not (10 <= temp <= 40):
            errors.append(f"Temperature {temp}°C is outside acceptable range (10-40°C)")

    # Type-specific validations
    if probe_type == "pH Probe":
        for buffer_label in ["pH 4", "pH 7", "pH 10"]:
            if f"{buffer_label}_initial_ph" in calibration_data:
                initial_ph = float(calibration_data[f"{buffer_label}_initial_ph"])
                final_ph = float(calibration_data[f"{buffer_label}_final_ph"])
                
                # Check readings are within range
                min_val, max_val = PH_RANGES[buffer_label]
                if not (min_val <= final_ph <= max_val):
                    errors.append(f"{buffer_label} final reading ({final_ph}) outside acceptable range ({min_val}-{max_val})")
                
                # Check for drift
                if abs(initial_ph - final_ph) > 0.5:
                    errors.append(f"{buffer_label} shows excessive drift: {abs(initial_ph - final_ph)} pH units")

    elif probe_type == "DO Probe":
        # Zero point validation
        if 'zero_final' in calibration_data:
            zero_reading = float(calibration_data['zero_final'])
            if not (-0.1 <= zero_reading <= 0.5):
                errors.append(f"Zero point reading ({zero_reading}%) outside acceptable range (-0.1-0.5%)")
        
        # Saturation point validation
        if 'sat_final' in calibration_data:
            sat_reading = float(calibration_data['sat_final'])
            if not (95 <= sat_reading <= 105):
                errors.append(f"Saturation point reading ({sat_reading}%) outside acceptable range (95-105%)")

    elif probe_type == "ORP Probe":
        if 'final_mv' in calibration_data:
            mv_reading = float(calibration_data['final_mv'])
            std_value = float(calibration_data.get('standard_value', 225))
            if abs(mv_reading - std_value) > 15:
                errors.append(f"ORP reading ({mv_reading} mV) deviates too much from standard ({std_value} mV)")

    elif probe_type == "EC Probe":
        standards = {
            "84": (80, 88),
            "1413": (1390, 1436),
            "12880": (12750, 13010)
        }
        for std, (min_val, max_val) in standards.items():
            if f"{std}_final" in calibration_data:
                reading = float(calibration_data[f"{std}_final"])
                if not (min_val <= reading <= max_val):
                    errors.append(f"{std} µS/cm reading ({reading}) outside acceptable range ({min_val}-{max_val})")

    return errors

def calibration_page():
    """Main calibration page logic."""
    st.markdown('<h1 style="color: #0071ba;">🔍 Probe Calibration</h1>', unsafe_allow_html=True)

    # Initialize inventory manager if needed
    if 'inventory_manager' not in st.session_state:
        st.error("Inventory manager not initialized. Please refresh the page.")
        return

    # Enhanced probe search
    selected_serial = render_autocomplete_search()
    
    if selected_serial:
        # Get probe details
        probe_df = st.session_state.inventory[
            st.session_state.inventory['Serial Number'] == selected_serial
        ]
        
        if probe_df.empty:
            st.error("❌ Probe not found in inventory.")
            return
            
        probe = probe_df.iloc[0]
        
        # Display probe information in a card
        st.markdown("""
            <div style='background-color: #f8f9fa; padding: 20px; border-radius: 10px; 
            border-left: 5px solid #0071ba; margin-bottom: 20px;'>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2,2,1])
        with col1:
            st.markdown(f"""
                <h3 style='margin:0;'>{probe['Serial Number']}</h3>
                <p style='margin:0;'>{probe['Type']}</p>
                <p style='margin:0; color: #666;'>{probe['Manufacturer']}</p>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
                <p style='margin:0;'><strong>KETOS P/N:</strong> {probe['KETOS P/N']}</p>
                <p style='margin:0;'><strong>Mfg P/N:</strong> {probe['Mfg P/N']}</p>
                <p style='margin:0;'><strong>Entry Date:</strong> {probe['Entry Date']}</p>
            """, unsafe_allow_html=True)
        with col3:
            status_color = {
                'Instock': '#FFD700',
                'Calibrated': '#90EE90',
                'Shipped': '#87CEEB',
                'Scraped': '#FFB6C6'
            }.get(probe['Status'], '#FFFFFF')
            
            st.markdown(f"""
                <div style='background-color: {status_color}; padding: 10px; 
                border-radius: 5px; text-align: center;'>
                    <strong>{probe['Status']}</strong>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Check probe status
        if probe['Status'] == 'Shipped':
            st.warning("⚠️ This probe has been shipped and cannot be calibrated.")
            return
            
        if probe['Status'] == 'Scraped':
            st.error("❌ This probe has been scraped and cannot be calibrated.")
            return
            
        if probe['Status'] != 'Instock':
            st.error("❌ Only probes with 'Instock' status can be calibrated.")
            return
        
        # Calibration form based on probe type
        st.markdown("### Calibration Data")
        calibration_data = None
        
        if probe['Type'] == "pH Probe":
            calibration_data = render_ph_calibration()
        elif probe['Type'] == "DO Probe":
            calibration_data = render_do_calibration()
        elif probe['Type'] == "ORP Probe":
            calibration_data = render_orp_calibration()
        elif probe['Type'] == "EC Probe":
            calibration_data = render_ec_calibration()
        
        # Save button
        if calibration_data and st.button("Save Calibration", key="save_cal"):
            # Validate calibration data
            errors = validate_calibration_data(probe['Type'], calibration_data)
            
            if errors:
                st.error("Calibration validation failed:")
                for error in errors:
                    st.warning(error)
            else:
                try:
                    # Add metadata
                    calibration_data['calibration_date'] = datetime.now().strftime("%Y-%m-%d")
                    calibration_data['operator'] = st.session_state.get('username', 'Unknown')
                    
                    # Update probe in inventory
                    probe_idx = probe_df.index[0]
                    st.session_state.inventory.at[probe_idx, 'Calibration Data'] = json.dumps(calibration_data)
                    st.session_state.inventory.at[probe_idx, 'Status'] = 'Calibrated'
                    st.session_state.inventory.at[probe_idx, 'Last Modified'] = datetime.now().strftime("%Y-%m-%d")
                    st.session_state.inventory.at[probe_idx, 'Next Calibration'] = (
                        datetime.now() + timedelta(days=365)
                    ).strftime("%Y-%m-%d")
                    
                    # Save to Google Sheets
                    if st.session_state.inventory_manager.save_inventory(st.session_state.inventory):
                        st.success("✅ Calibration data saved successfully!")
                        
                        # Show calibration certificate download option
                        if st.button("Download Calibration Certificate"):
                            generate_calibration_certificate(probe, calibration_data)
                        
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Failed to save calibration data")
                except Exception as e:
                    st.error(f"Error saving calibration: {str(e)}")
                    logger.error(f"Calibration save error: {str(e)}")

if __name__ == "__main__":
    calibration_page()
