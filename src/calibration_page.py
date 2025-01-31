# src/calibration_page.py

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import logging
import time
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Helper Functions
def find_probe(serial_number):
    """Find a probe in the inventory by serial number."""
    if 'inventory' not in st.session_state:
        return None
    
    inventory_df = st.session_state.inventory
    probe = inventory_df[inventory_df['Serial Number'] == serial_number]
    return probe.iloc[0] if not probe.empty else None

def get_searchable_probes():
    """Get list of searchable probes with their details."""
    if 'inventory' not in st.session_state:
        return []
    
    inventory_df = st.session_state.inventory
    searchable_probes = []
    
    for _, row in inventory_df.iterrows():
        probe_info = {
            'serial': row['Serial Number'],
            'type': row['Type'],
            'manufacturer': row['Manufacturer'],
            'status': row['Status'],
            'search_text': f"{row['Serial Number']} {row['Type']} {row['Manufacturer']} {row['Status']}"
        }
        searchable_probes.append(probe_info)
    
    return searchable_probes

# Display Functions for Shipped Probes
def display_shipped_probe_info(probe):
    """Display detailed information for shipped probes."""
    st.markdown("""
        <style>
            .shipped-probe-card {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                border-left: 4px solid #4169E1;
                margin: 20px 0;
            }
            .calibration-details {
                background: white;
                padding: 15px;
                border-radius: 8px;
                margin-top: 15px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            .info-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-top: 10px;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="shipped-probe-card">
            <h3 style="color: #4169E1; margin-top: 0;">📦 Shipped Probe Information</h3>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📋 Probe Details")
        st.markdown(f"""
            - **Serial Number:** {probe['Serial Number']}
            - **Type:** {probe['Type']}
            - **Manufacturer:** {probe['Manufacturer']}
            - **Ship Date:** {probe.get('Last Modified', 'N/A')}
        """)

    with col2:
        st.markdown("#### 📅 Calibration Timeline")
        st.markdown(f"""
            - **Last Calibration:** {probe.get('Last Modified', 'N/A')}
            - **Next Calibration Due:** {probe.get('Next Calibration', 'N/A')}
            - **Calibrated By:** {probe.get('Operator', 'N/A')}
        """)

    if 'Calibration Data' in probe and probe['Calibration Data']:
        try:
            cal_data = json.loads(probe['Calibration Data'])
            st.markdown("#### 📊 Final Calibration Results")
            
            if probe['Type'] == "pH Probe":
                display_ph_calibration_data(cal_data)
            elif probe['Type'] == "DO Probe":
                display_do_calibration_data(cal_data)
            elif probe['Type'] == "ORP Probe":
                display_orp_calibration_data(cal_data)
            elif probe['Type'] == "EC Probe":
                display_ec_calibration_data(cal_data)

        except json.JSONDecodeError:
            st.error("Error loading calibration data")
    else:
        st.info("No calibration data available for this probe")

# Calibration Data Display Functions

def display_ph_calibration_data(cal_data):
    """Display pH probe calibration data."""
    buffers = ["pH 4", "pH 7", "pH 10"]
    
    for buffer in buffers:
        if f"{buffer}_initial" in cal_data:
            with st.expander(f"{buffer} Buffer Results", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                        - Initial pH: {cal_data.get(f'{buffer}_initial', 'N/A')}
                        - Initial mV: {cal_data.get(f'{buffer}_initial_mv', 'N/A')}
                        - Solution Control #: {cal_data.get(f'{buffer}_control', 'N/A')}
                    """)
                with col2:
                    st.markdown(f"""
                        - Final pH: {cal_data.get(f'{buffer}_calibrated', 'N/A')}
                        - Final mV: {cal_data.get(f'{buffer}_calibrated_mv', 'N/A')}
                        - Temperature: {cal_data.get('temperature', 'N/A')}°C
                    """)

def display_do_calibration_data(cal_data):
    """Display DO probe calibration data."""
    # Environmental conditions
    st.markdown("##### 🌡️ Environmental Conditions")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
            - Temperature: {cal_data.get('temperature', 'N/A')}°C
        """)
    with col2:
        st.markdown(f"""
            - Pressure: {cal_data.get('pressure', 'N/A')} mmHg
        """)

    # Zero point data
    with st.expander("Zero Point (0% DO) Results", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
                - Initial Reading: {cal_data.get('zero_initial', 'N/A')}%
                - Solution Control #: {cal_data.get('zero_control', 'N/A')}
            """)
        with col2:
            st.markdown(f"""
                - Final Reading: {cal_data.get('zero_final', 'N/A')}%
                - Solution Expiry: {cal_data.get('zero_exp', 'N/A')}
            """)

    # Saturation point data
    with st.expander("Saturation Point (100% DO) Results", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
                - Initial Reading: {cal_data.get('sat_initial', 'N/A')}%
                - Final Reading: {cal_data.get('sat_final', 'N/A')}%
            """)
        with col2:
            st.markdown(f"""
                - mg/L Reading: {cal_data.get('sat_mg_l', 'N/A')} mg/L
                - Temperature: {cal_data.get('sat_temp', 'N/A')}°C
            """)

def display_orp_calibration_data(cal_data):
    """Display ORP probe calibration data."""
    with st.expander("ORP Calibration Results", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
                - Initial mV: {cal_data.get('initial_mv', 'N/A')} mV
                - Solution Control #: {cal_data.get('control_number', 'N/A')}
                - Temperature: {cal_data.get('temperature', 'N/A')}°C
            """)
        with col2:
            st.markdown(f"""
                - Final mV: {cal_data.get('calibrated_mv', 'N/A')} mV
                - Solution Expiry: {cal_data.get('expiration', 'N/A')}
                - Solution Standard: {cal_data.get('standard_value', '225')} mV
            """)

def display_ec_calibration_data(cal_data):
    """Display EC probe calibration data."""
    standards = [
        ("84 µS/cm", "84"),
        ("1413 µS/cm", "1413"),
        ("12.88 mS/cm", "12880")
    ]

    st.markdown("##### 🌡️ Calibration Temperature")
    st.markdown(f"- Temperature: {cal_data.get('temperature', 'N/A')}°C")

    for std_name, std_key in standards:
        if f"{std_key}_initial" in cal_data:
            with st.expander(f"{std_name} Standard Results", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                        - Initial Reading: {cal_data.get(f'{std_key}_initial', 'N/A')}
                        - Solution Control #: {cal_data.get(f'{std_key}_control', 'N/A')}
                    """)
                with col2:
                    st.markdown(f"""
                        - Final Reading: {cal_data.get(f'{std_key}_final', 'N/A')}
                        - Solution Expiry: {cal_data.get(f'{std_key}_exp', 'N/A')}
                    """)


def update_probe_calibration(serial_number, calibration_data):
    try:
        if serial_number not in st.session_state.inventory['Serial Number'].values:
            st.error(f"Serial number {serial_number} not found in inventory")
            return False
            
        probe_idx = st.session_state.inventory[
            st.session_state.inventory['Serial Number'] == serial_number
        ].index[0]

        # Convert date objects to strings
        for key, value in calibration_data.items():
            if isinstance(value, date):
                calibration_data[key] = value.strftime('%Y-%m-%d')
            elif isinstance(value, float) and pd.isna(value):
                calibration_data[key] = ''

        # Add metadata
        calibration_data['calibration_date'] = datetime.now().strftime("%Y-%m-%d")
        calibration_data['operator'] = st.session_state.get('username', 'Unknown')
        
        # Update the DataFrame
        st.session_state.inventory.at[probe_idx, 'Calibration Data'] = json.dumps(calibration_data)
        st.session_state.inventory.at[probe_idx, 'Last Modified'] = datetime.now().strftime("%Y-%m-%d")
        st.session_state.inventory.at[probe_idx, 'Next Calibration'] = (
            datetime.now() + timedelta(days=365)
        ).strftime("%Y-%m-%d")
        st.session_state.inventory.at[probe_idx, 'Status'] = "Calibrated"
        
        return st.session_state.inventory_manager.save_inventory(st.session_state.inventory)
            
    except Exception as e:
        logger.error(f"Error updating calibration data: {str(e)}")
        return False

# Common Styles
CALIBRATION_STYLES = """
<style>
    .calibration-header {
        background: linear-gradient(90deg, #0071ba, #00a6fb);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .info-grid {
        display: flex;
        gap: 15px;
        margin: 10px 0;
        flex-wrap: wrap;
    }
    .info-item {
        background: #f8f9fa;
        padding: 10px 15px;
        border-radius: 8px;
        flex: 1;
        min-width: 200px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .tips-container {
        background: #e3f2fd;
        padding: 15px;
        border-radius: 8px;
        margin-top: 15px;
    }
    .calibration-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        border-left: 4px solid;
    }
</style>
"""


def calculate_mv_from_ph(ph_value, temperature=25.0):
    """Calculate mV from pH using Nernst equation."""
    try:
        ph_value = float(ph_value)
        temperature = float(temperature)
        nernst_factor = 0.198968 * (temperature + 273.15)  # RT/F
        mv = -nernst_factor * (ph_value - 7)
        return round(mv, 1)
    except (ValueError, TypeError):
        return None

def render_ph_calibration():
    """Render pH probe calibration form."""
    st.markdown("""
        <div style='background: linear-gradient(90deg, #0071ba, #00a6fb); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
            <h2 style='margin:0;'>🧪 pH Probe Calibration</h2>
            <p style='margin:5px 0 0 0;'>Three-point calibration sequence for accurate pH measurement</p>
        </div>
    """, unsafe_allow_html=True)

    ph_data = {}

    # Temperature measurement
    st.markdown("### 🌡️ Temperature Control")
    temp_col1, temp_col2 = st.columns([2, 1])
    with temp_col1:
        ph_data['temperature'] = st.number_input(
            "Solution Temperature (°C)",
            min_value=10.0,
            max_value=40.0,
            value=25.0,
            step=0.1,
            help="Maintain temperature between 10-40°C"
        )
    with temp_col2:
        st.info("Optimal range: 20-25°C")

    # Buffer configurations
    buffers = [
        {
            "name": "pH 7",
            "color": "#FFD700",
            "icon": "⚖️",
            "desc": "Neutral Buffer",
            "range": "6.98 - 7.02",
            "expected_mv": "0 ±30 mV",
            "tips": [
                "Always start with pH 7 buffer",
                "Rinse probe with DI water before immersion",
                "Wait for stable reading (±0.01 pH)",
                "Record offset reading after calibration"
            ]
        },
        {
            "name": "pH 4",
            "color": "#FF6B6B",
            "icon": "🔴",
            "desc": "Acidic Buffer",
            "range": "3.98 - 4.02",
            "expected_mv": "+165 to +180 mV",
            "tips": [
                "Use after pH 7 calibration",
                "Ensure thorough rinsing between buffers",
                "Check for rapid response",
                "Calculate slope after calibration"
            ]
        },
        {
            "name": "pH 10",
            "color": "#4ECDC4",
            "icon": "🔵",
            "desc": "Basic Buffer",
            "range": "9.98 - 10.02",
            "expected_mv": "-165 to -180 mV",
            "tips": [
                "Final calibration point",
                "Most sensitive to temperature",
                "Verify slope calculation",
                "Record all final readings"
            ]
        }
    ]

    for buffer in buffers:
        st.markdown(f"### {buffer['icon']} {buffer['name']} Buffer Solution")
        
        # Info grid
        st.info(f"""
            📊 Expected Range: {buffer['range']}  |  
            ⚡ Expected mV: {buffer['expected_mv']}
        """)

        # Tips
        with st.expander("💡 Important Tips", expanded=True):
            for tip in buffer['tips']:
                st.markdown(f"• {tip}")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 📋 Buffer Information")
            ph_data[f"{buffer['name']}_control"] = st.text_input(
                "Control Number",
                key=f"{buffer['name']}_control",
                help="Enter the buffer solution control number"
            )
            ph_data[f"{buffer['name']}_exp"] = st.date_input(
                "Expiration Date",
                key=f"{buffer['name']}_exp"
            )
            ph_data[f"{buffer['name']}_opened"] = st.date_input(
                "Date Opened",
                key=f"{buffer['name']}_opened"
            )

        with col2:
            st.markdown("#### 📊 Measurements")
            
            measurement_cols = st.columns(2)
            with measurement_cols[0]:
                # Initial pH and mV
                initial_ph = st.number_input(
                    "Initial Reading (pH)",
                    min_value=0.0,
                    max_value=14.0,
                    step=0.01,
                    key=f"{buffer['name']}_initial_ph",
                    help=f"Target: {buffer['range']}"
                )
                ph_data[f"{buffer['name']}_initial"] = initial_ph
                
                # Calculate and display initial mV
                calculated_mv = calculate_mv_from_ph(initial_ph, ph_data['temperature'])
                st.text(f"Calculated mV: {calculated_mv if calculated_mv is not None else 'N/A'}")
                
                # Allow manual override of initial mV
                ph_data[f"{buffer['name']}_initial_mv"] = st.number_input(
                    "Initial mV (Override calculated value)",
                    min_value=-2000.0,
                    max_value=2000.0,
                    value=calculated_mv if calculated_mv is not None else 0.0,
                    step=0.1,
                    key=f"{buffer['name']}_initial_mv",
                    help=f"Expected: {buffer['expected_mv']}"
                )

            with measurement_cols[1]:
                # Final pH and mV
                final_ph = st.number_input(
                    "Final Reading (pH)",
                    min_value=0.0,
                    max_value=14.0,
                    step=0.01,
                    key=f"{buffer['name']}_final_ph"
                )
                ph_data[f"{buffer['name']}_calibrated"] = final_ph
                
                # Calculate and display final mV
                calculated_mv_final = calculate_mv_from_ph(final_ph, ph_data['temperature'])
                st.text(f"Calculated mV: {calculated_mv_final if calculated_mv_final is not None else 'N/A'}")
                
                # Allow manual override of final mV
                ph_data[f"{buffer['name']}_calibrated_mv"] = st.number_input(
                    "Final mV (Override calculated value)",
                    min_value=-2000.0,
                    max_value=2000.0,
                    value=calculated_mv_final if calculated_mv_final is not None else 0.0,
                    step=0.1,
                    key=f"{buffer['name']}_final_mv",
                    help=f"Expected: {buffer['expected_mv']}"
                )

            # Add slope and offset fields in the measurements column for pH 7
            if buffer['name'] == "pH 7":
                ph_data['offset_mv'] = st.number_input(
                    "pH 7 Offset (mV)",
                    min_value=-60.0,
                    max_value=60.0,
                    value=0.0,
                    step=0.1,
                    help="Ideal value is 0 mV. Acceptable range: ±60 mV"
                )
                if abs(ph_data['offset_mv']) > 30:
                    st.warning("⚠️ Offset is outside optimal range (±30 mV)")

            # Add slope field for pH 10
            if buffer['name'] == "pH 10":
                ph_data['slope_mv_10'] = st.number_input(
                    "Slope (%)",
                    min_value=85,
                    max_value=115,
                   
                    key="slope_10"
                )
                if ph_data['slope_mv_10'] > 85 or ph_data['slope_mv_10'] < 115:
                    st.warning("⚠️ pH 10 Slope is outside optimal range (85 to 115 %)")

            # Add slope field after pH 4 measurements
            if buffer['name'] == "pH 4":
                ph_data['slope_mv'] = st.number_input(
                    "Slope (%)",
                    min_value=85,
                    max_value=115,
                    
                )
                if ph_data['slope_mv'] > 85 or ph_data['slope_mv'] < 115:
                    st.warning("⚠️ Slope is outside optimal range (85 to 115)")

        st.markdown("---")

    return ph_data
def render_do_tips(tips, border_color):
    """Helper function to render tips properly"""
    tips_html = f"""
        <div style='
            background: #e3f2fd;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
            border-left: 4px solid {border_color};
        '>
            <strong style='color: #0071ba;'>💡 Important Tips:</strong>
            <ul style='margin-top: 10px; margin-bottom: 5px;'>
                {' '.join(f'<li style="margin-bottom: 5px;">{tip}</li>' for tip in tips)}
            </ul>
        </div>
    """
    st.markdown(tips_html, unsafe_allow_html=True)

def render_do_calibration():
    """Render DO probe calibration form."""
    st.markdown("""
        <div style='background: linear-gradient(90deg, #0071ba, #00a6fb); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
            <h2 style='margin:0;'>💧 DO Probe Calibration</h2>
            <p style='margin:5px 0 0 0;'>Two-point calibration for Dissolved Oxygen measurement (mg/L)</p>
        </div>
    """, unsafe_allow_html=True)

    do_data = {}

    # General Guidelines
    with st.expander("📌 General Calibration Guidelines", expanded=True):
        st.markdown("""
        * Ensure probe membrane is clean and undamaged
        * Allow 15-20 minutes warm-up time
        * Calibrate in order: 0 mg/L then saturation point
        * Keep temperature stable during calibration
        * Avoid air bubbles on membrane surface
        * Replace electrolyte if readings are unstable
        """)

    # Environmental Conditions
    st.markdown("### 🌡️ Environmental Conditions")
    col1, col2 = st.columns(2)
    with col1:
        do_data['temperature'] = st.number_input(
            "Solution Temperature (°C)",
            min_value=0.0,
            max_value=50.0,
            value=25.0,
            step=0.1,
            help="Maintain consistent temperature throughout calibration"
        )
    with col2:
        do_data['pressure'] = st.number_input(
            "Atmospheric Pressure (mmHg)",
            min_value=500.0,
            max_value=800.0,
            value=760.0,
            step=0.1,
            help="Local atmospheric pressure affects DO saturation"
        )

    # Calibration points configuration
    cal_points = [
        {
            "name": "Zero Point",
            "unit": "mg/L",
            "color": "#FF6B6B",
            "icon": "⭕",
            "desc": "0 mg/L Calibration",
            "range": "0.0 - 0.2 mg/L",
            "expected": "0.0 mg/L",
            "tips": [
                "Use fresh sodium sulfite solution",
                "Ensure probe tip is fully submerged",
                "Stir gently to remove trapped bubbles",
                "Wait for stable reading (2-3 minutes)",
                "Verify zero point stability"
            ]
        },
        {
            "name": "Saturation Point",
            "unit": "mg/L",
            "color": "#4ECDC4",
            "icon": "💫",
            "desc": "Saturation Calibration",
            "range": "8.2 - 8.7 mg/L at 25°C",
            "expected": "8.4 mg/L at 25°C",
            "tips": [
                "Use water-saturated air method",
                "Keep probe in sealed, moist environment",
                "Maintain stable temperature",
                "Allow 3-5 minutes for stabilization",
                "Avoid direct sunlight during calibration"
            ]
        }
    ]

    # Calibration sections for each point
    for point in cal_points:
        st.markdown(f"### {point['icon']} {point['name']} Calibration ({point['unit']})")
        
        # Info box
        st.info(f"""
            📊 Expected Range: {point['range']}  |  
            🎯 Target Value: {point['expected']}  |  
            ⏱️ Stability Time: 2-3 minutes
        """)

        # Tips section
        with st.expander("💡 Important Tips", expanded=True):
            for tip in point['tips']:
                st.markdown(f"• {tip}")

        # Input fields
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📋 Solution Information")
            if point['name'] == "Zero Point":
                do_data['zero_control'] = st.text_input(
                    "Control Number",
                    help="Enter the zero solution control number"
                )
                do_data['zero_exp'] = st.date_input(
                    "Solution Expiration Date",
                    help="Zero solution expiration date"
                )

        with col2:
            st.markdown("#### 📊 Measurements")
            prefix = 'zero' if point['name'] == "Zero Point" else 'sat'
            
            measurement_cols = st.columns(2)
            with measurement_cols[0]:
                do_data[f'{prefix}_initial'] = st.number_input(
                    "Initial Reading (mg/L)",
                    min_value=0.0,
                    max_value=20.0,
                    step=0.01,
                    key=f"{prefix}_initial",
                    help=f"Initial DO reading for {point['name']}"
                )
            
            with measurement_cols[1]:
                do_data[f'{prefix}_final'] = st.number_input(
                    "Final Reading (mg/L)",
                    min_value=0.0,
                    max_value=20.0,
                    step=0.01,
                    key=f"{prefix}_final",
                    help=f"Final stabilized reading for {point['name']}"
                )

            # Validation warnings
            if point['name'] == "Zero Point":
                if do_data[f'{prefix}_final'] > 0.2:
                    st.warning("⚠️ Zero point reading is higher than recommended (>0.2 mg/L)")
            else:
                temp = do_data['temperature']
                if 20 <= temp <= 30:
                    if not (9.2 <= do_data[f'{prefix}_final'] <= 9.7):
                        st.warning("⚠️ Saturation reading is outside expected range (9.2-9.7 mg/L)")

        st.markdown("---")

    return do_data

def render_orp_calibration():
    """Render ORP probe calibration form."""
    st.markdown(CALIBRATION_STYLES, unsafe_allow_html=True)
    
    st.markdown("""
        <div class='calibration-header'>
            <h2 style='margin:0;'>⚡ ORP Probe Calibration</h2>
            <p style='margin:5px 0 0 0;'>Single-point calibration for ORP measurement</p>
        </div>
    """, unsafe_allow_html=True)

    orp_data = {}

    # General Guidelines
    with st.expander("📌 General Calibration Guidelines", expanded=True):
        st.markdown("""
        * Clean probe tip thoroughly before calibration
        * Use fresh 225mV ORP standard solution
        * Allow readings to stabilize (2-3 minutes)
        * Keep probe tip fully submerged
        * Avoid touching probe tip with fingers
        """)

    # Temperature measurement
    st.markdown("### 🌡️ Environmental Conditions")
    orp_data['temperature'] = st.number_input(
        "Solution Temperature (°C)",
        min_value=10.0,
        max_value=40.0,
        value=25.0,
        step=0.1,
        help="Maintain temperature between 10-40°C"
    )

    # ORP Calibration
    st.markdown("### ORP Standard Solution Calibration")
    st.markdown("""
        <div class='calibration-card' style='border-left-color: #9333ea;'>
            <div class='info-grid'>
                <div class='info-item'>
                    <strong>📊 Expected Range</strong><br/>
                    225 ±10 mV at 25°C
                </div>
                <div class='info-item'>
                    <strong>⏱️ Stability Time</strong><br/>
                    2-3 minutes
                </div>
                <div class='info-item'>
                    <strong>🎯 Target Value</strong><br/>
                    225 mV
                </div>
            </div>

            <div class='tips-container'>
                <strong>💡 Important Tips:</strong>
                <ul>
                    <li>Ensure probe is clean and dry before calibration</li>
                    <li>Use fresh standard solution</li>
                    <li>Keep probe tip fully submerged</li>
                    <li>Wait for reading to stabilize</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        orp_data['control_number'] = st.text_input(
            "Control Number",
            help="Enter the standard solution control number"
        )
        orp_data['expiration'] = st.date_input(
            "Solution Expiration Date"
        )
        orp_data['standard_value'] = st.number_input(
            "Standard Solution Value (mV)",
            value=225.0,
            step=0.1,
            help="Usually 225mV for standard solution"
        )

    with col2:
        orp_data['initial_mv'] = st.number_input(
            "Initial Reading (mV)",
            min_value=-2000.0,
            max_value=2000.0,
            step=0.1,
            help="Initial ORP reading before calibration"
        )
        orp_data['calibrated_mv'] = st.number_input(
            "Final Reading (mV)",
            min_value=-2000.0,
            max_value=2000.0,
            step=0.1,
            help="Should be close to standard value (±10 mV)"
        )

        # Validation warning
        if abs(orp_data['calibrated_mv'] - orp_data['standard_value']) > 10:
            st.warning("⚠️ Final reading deviates more than ±10 mV from standard value")

    return orp_data

def render_ec_calibration():
    """Render EC probe calibration form."""
    st.markdown(CALIBRATION_STYLES, unsafe_allow_html=True)
    
    st.markdown("""
        <div class='calibration-header'>
            <h2 style='margin:0;'>🔌 EC Probe Calibration</h2>
            <p style='margin:5px 0 0 0;'>Three-point calibration for Electrical Conductivity measurement</p>
        </div>
    """, unsafe_allow_html=True)

    ec_data = {}

    # General Guidelines
    with st.expander("📌 General Calibration Guidelines", expanded=True):
        st.markdown("""
        * Start with the lowest conductivity standard (84 µS/cm)
        * Rinse probe thoroughly with DI water between standards
        * Ensure probe is completely dry before each standard
        * Wait for temperature and readings to stabilize
        * Keep probe tip fully submerged during calibration
        * Avoid air bubbles in the measuring cell
        """)

    # Temperature measurement
    st.markdown("### 🌡️ Environmental Conditions")
    ec_data['temperature'] = st.number_input(
        "Solution Temperature (°C)",
        min_value=10.0,
        max_value=40.0,
        value=25.0,
        step=0.1,
        help="Maintain consistent temperature throughout calibration"
    )

    # EC Standards Configuration
    standards = [
        {
            "name": "84 µS/cm",
            "key": "84",
            "color": "#4ECDC4",
            "range": "80-88 µS/cm",
            "unit": "µS/cm",
            "tips": [
                "Start with this lowest standard",
                "Essential for low-range accuracy",
                "Most sensitive to temperature",
                "Wait for complete stability"
            ]
        },
        {
            "name": "1413 µS/cm",
            "key": "1413",
            "color": "#FFD700",
            "range": "1390-1436 µS/cm",
            "unit": "µS/cm",
            "tips": [
                "Middle-range standard",
                "Common measurement range",
                "Check for consistent response",
                "Verify temperature compensation"
            ]
        },
        {
            "name": "12.88 mS/cm",
            "key": "12880",
            "color": "#FF6B6B",
            "range": "12.75-13.01 mS/cm",
            "unit": "mS/cm",
            "tips": [
                "Highest standard solution",
                "Critical for high-range accuracy",
                "Ensure complete rinsing from previous standards",
                "Verify cell constant calculation"
            ]
        }
    ]

    # Calibration sections for each standard
    for standard in standards:
        st.markdown(f"### {standard['name']} Standard")
        st.markdown(f"""
            <div class='calibration-card' style='border-left-color: {standard["color"]};'>
                <div class='info-grid'>
                    <div class='info-item'>
                        <strong>📊 Expected Range</strong><br/>
                        {standard['range']}
                    </div>
                    <div class='info-item'>
                        <strong>⏱️ Stability Time</strong><br/>
                        1-2 minutes
                    </div>
                    <div class='info-item'>
                        <strong>🎯 Target Value</strong><br/>
                        {standard['name']}
                    </div>
                </div>

                <div class='tips-container'>
                    <strong>💡 Important Tips:</strong>
                    <ul>
                        {''.join(f'<li>{tip}</li>' for tip in standard['tips'])}
                    </ul>
                </div>
            """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            ec_data[f"{standard['key']}_control"] = st.text_input(
                "Control Number",
                key=f"ec_{standard['key']}_control",
                help=f"Enter the {standard['name']} solution control number"
            )
            ec_data[f"{standard['key']}_exp"] = st.date_input(
                "Solution Expiration Date",
                key=f"ec_{standard['key']}_exp"
            )

        with col2:
            ec_data[f"{standard['key']}_initial"] = st.number_input(
                f"Initial Reading ({standard['unit']})",
                min_value=0.0,
                step=0.1,
                key=f"ec_{standard['key']}_initial",
                help=f"Initial reading for {standard['name']} standard"
            )
            ec_data[f"{standard['key']}_final"] = st.number_input(
                f"Final Reading ({standard['unit']})",
                min_value=0.0,
                step=0.1,
                key=f"ec_{standard['key']}_final",
                help=f"Should be within {standard['range']}"
            )

            # Validation warnings
            if standard['key'] == '84':
                if not (80 <= ec_data[f"{standard['key']}_final"] <= 88):
                    st.warning("⚠️ Reading outside acceptable range (80-88 µS/cm)")
            elif standard['key'] == '1413':
                if not (1390 <= ec_data[f"{standard['key']}_final"] <= 1436):
                    st.warning("⚠️ Reading outside acceptable range (1390-1436 µS/cm)")
            elif standard['key'] == '12880':
                final_ms = ec_data[f"{standard['key']}_final"]
                if not (12.75 <= final_ms <= 13.01):
                    st.warning("⚠️ Reading outside acceptable range (12.75-13.01 mS/cm)")

        st.markdown("</div>", unsafe_allow_html=True)

    return ec_data

def calibration_page():
    """Main page for probe calibration."""
    st.markdown('<h1 style="color: #0071ba;">🔍 Probe Calibration</h1>', unsafe_allow_html=True)

    # Initialize inventory manager if needed
    if 'inventory_manager' not in st.session_state:
        st.error("Inventory manager not initialized")
        return

    # Show search only if no probe is selected or if user wants to search again
    if not hasattr(st.session_state, 'selected_probe') or st.session_state.get('show_search', False):
        st.markdown("### Select Probe")
        search_query = st.text_input(
            "🔍 Search by Serial Number or Type",
            placeholder="Enter Serial Number or Probe Type...",
            help="Search for a probe to calibrate"
        ).strip().lower()

        # Get and filter probes
        probes = get_searchable_probes()
        if search_query and probes:
            filtered_probes = [
                probe for probe in probes
                if search_query in probe['search_text'].lower()
            ]
            
            if filtered_probes:
                st.markdown("#### Matching Probes")
                cols = st.columns([3, 2, 2, 1])
                cols[0].markdown("**Serial Number**")
                cols[1].markdown("**Type**")
                cols[2].markdown("**Status**")
                st.markdown("---")

                for probe in filtered_probes:
                    cols = st.columns([3, 2, 2, 1])
                    with cols[0]:
                        st.write(probe['serial'])
                    with cols[1]:
                        st.write(probe['type'])
                    with cols[2]:
                        status_color = {
                            'Instock': '#FFD700',
                            'Calibrated': '#90EE90',
                            'Shipped': '#87CEEB',
                            'Scraped': '#FFB6C6'
                        }.get(probe['status'], '#FFFFFF')
                        st.markdown(f"""
                            <span style='
                                background-color: {status_color}40;
                                padding: 3px 8px;
                                border-radius: 12px;
                                font-size: 0.9em;
                            '>
                                {probe['status']}
                            </span>
                        """, unsafe_allow_html=True)
                    with cols[3]:
                        if st.button("Select", key=f"select_{probe['serial']}"):
                            st.session_state.selected_probe = probe['serial']
                            st.session_state.show_search = False
                            st.rerun()
            else:
                st.info("No matching probes found.")

    # Show calibration form if probe is selected
    if hasattr(st.session_state, 'selected_probe'):
        selected_serial = st.session_state.selected_probe
        probe = find_probe(selected_serial)
        
        # Add a button to search for a different probe
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🔍 Search Different Probe"):
                st.session_state.show_search = True
                del st.session_state.selected_probe
                st.rerun()
        
        if probe is None:
            st.error("❌ Probe not found in inventory.")
            return

        # Display probe information
        st.markdown(f"""
            <div style='
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
                border-left: 4px solid #0071ba;
            '>
                <h3 style='margin: 0; color: #0071ba;'>Selected Probe Details</h3>
                <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 10px;'>
                    <div>
                        <strong>Serial Number:</strong> {probe['Serial Number']}<br>
                        <strong>Type:</strong> {probe['Type']}
                    </div>
                    <div>
                        <strong>Manufacturer:</strong> {probe['Manufacturer']}<br>
                        <strong>Entry Date:</strong> {probe['Entry Date']}
                    </div>
                    <div>
                        <strong>Status:</strong> {probe['Status']}<br>
                        <strong>Last Modified:</strong> {probe.get('Last Modified', 'N/A')}
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Check probe status
        if probe['Status'] == 'Shipped':
            display_shipped_probe_info(probe)
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
        
        try:
            if probe['Type'] == "pH Probe":
                calibration_data = render_ph_calibration()
            elif probe['Type'] == "DO Probe":
                calibration_data = render_do_calibration()
            elif probe['Type'] == "ORP Probe":
                calibration_data = render_orp_calibration()
            elif probe['Type'] == "EC Probe":
                calibration_data = render_ec_calibration()
            else:
                st.error(f"Unsupported probe type: {probe['Type']}")
                return

            # Save button
            if calibration_data:
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    if st.button("Save Calibration Data", type="primary"):
                        with st.spinner("Saving calibration data..."):
                            success = update_probe_calibration(selected_serial, calibration_data)
                            if success:
                                st.success("✅ Calibration data saved successfully!")
                                time.sleep(1)
                                st.rerun()
                with col2:
                    if st.button("Clear Form"):
                        del st.session_state.selected_probe
                        st.rerun()

        except Exception as e:
            st.error(f"Error during calibration: {str(e)}")
            logger.error(f"Calibration error: {str(e)}")

if __name__ == "__main__":
    calibration_page()


