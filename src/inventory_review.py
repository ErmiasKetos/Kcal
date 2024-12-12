

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import time
from .inventory_manager import STATUS_COLORS

# Constants for the inventory review
ESSENTIAL_COLUMNS = [
    "Serial Number", "Type", "Status", "Entry Date", 
    "Next Calibration", "Last Modified"
]

STATUS_INFO = {
    'Instock': {
        'color': '#FFD700',
        'desc': 'Probes available for calibration and deployment',
        'icon': '📦'
    },
    'Calibrated': {
        'color': '#90EE90',
        'desc': 'Probes that have been calibrated and are ready for shipping',
        'icon': '✅'
    },
    'Shipped': {
        'color': '#87CEEB',
        'desc': 'Probes that have been sent to customers',
        'icon': '🚢'
    },
    'Scraped': {
        'color': '#FFB6C6',
        'desc': 'Probes that are no longer in service',
        'icon': '❌'
    }
}

# Custom CSS for styling
CUSTOM_CSS = """
<style>
    .status-legend {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-bottom: 20px;
    }
    .status-item {
        flex: 1;
        min-width: 200px;
        padding: 10px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: transform 0.2s ease;
    }
    .status-item:hover {
        transform: translateY(-2px);
    }
    .status-title {
        font-weight: bold;
        margin-bottom: 5px;
        display: flex;
        align-items: center;
        gap: 5px;
    }
    .status-desc {
        font-size: 0.9em;
        color: #666;
    }
    .metric-card {
        background: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 10px;
    }
    .filter-section {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
    }
</style>
"""

def render_status_legend():
    """Render an improved status color legend with descriptions."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    st.markdown('<div class="status-legend">', unsafe_allow_html=True)
    for status, info in STATUS_INFO.items():
        st.markdown(f"""
            <div class="status-item" style="background-color: {info['color']}20; 
                                          border-left: 4px solid {info['color']}">
                <div class="status-title">
                    {info['icon']} {status}
                </div>
                <div class="status-desc">{info['desc']}</div>
            </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def render_inventory_stats(df):
    """Render inventory statistics cards."""
    st.markdown("### 📊 Inventory Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total = len(df)
    active = len(df[df['Status'].isin(['Instock', 'Calibrated'])])
    need_cal = len(df[df['Status'] == 'Instock'])
    shipped = len(df[df['Status'] == 'Shipped'])
    
    metrics = [
        (col1, "Total Probes", total, None),
        (col2, "Active Probes", active, f"{(active/total*100):.1f}% of total" if total > 0 else None),
        (col3, "Need Calibration", need_cal, "Awaiting calibration"),
        (col4, "Shipped", shipped, f"{(shipped/total*100):.1f}% of total" if total > 0 else None)
    ]
    
    for col, label, value, delta in metrics:
        with col:
            st.metric(label, value, delta=delta)

def render_advanced_filters(df):
    """Render advanced filtering options."""
    with st.expander("🔍 Advanced Filters", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            # Basic filters
            status_filter = st.multiselect(
                "Status",
                ["Instock", "Calibrated", "Shipped", "Scraped"],
                default=["Instock", "Calibrated"]
            )
            
            type_filter = st.multiselect(
                "Probe Type",
                sorted(df['Type'].unique().tolist())
            )

        with col2:
            # Date filters
            date_col1, date_col2 = st.columns(2)
            with date_col1:
                start_date = st.date_input(
                    "Start Date",
                    value=datetime.now() - timedelta(days=30)
                )
            with date_col2:
                end_date = st.date_input(
                    "End Date",
                    value=datetime.now()
                )

        # Quick filters
        st.markdown("#### Quick Filters")
        quick_cols = st.columns(4)
        with quick_cols[0]:
            show_expired_cal = st.checkbox("Show Expired Calibrations")
        with quick_cols[1]:
            show_recent = st.checkbox("Recent Changes (7 days)")
        with quick_cols[2]:
            show_active = st.checkbox("Active Only")
        with quick_cols[3]:
            show_critical = st.checkbox("Needs Attention")

    # Apply filters
    filtered_df = df.copy()

    # Basic filters
    if status_filter:
        filtered_df = filtered_df[filtered_df['Status'].isin(status_filter)]
    if type_filter:
        filtered_df = filtered_df[filtered_df['Type'].isin(type_filter)]

    # Date range filter
    try:
        if start_date and end_date:
            filtered_df = filtered_df[
                (pd.to_datetime(filtered_df['Entry Date']) >= pd.to_datetime(start_date)) &
                (pd.to_datetime(filtered_df['Entry Date']) <= pd.to_datetime(end_date))
            ]
    except Exception as e:
        st.warning(f"Date filtering error: {str(e)}")

    # Quick filters
    if show_expired_cal:
        try:
            filtered_df = filtered_df[
                pd.to_datetime(filtered_df['Next Calibration']) <= datetime.now()
            ]
        except Exception:
            st.warning("Error filtering expired calibrations")
    
    if show_recent:
        try:
            filtered_df = filtered_df[
                pd.to_datetime(filtered_df['Last Modified']) >= datetime.now() - timedelta(days=7)
            ]
        except Exception:
            st.warning("Error filtering recent changes")
    
    if show_active:
        filtered_df = filtered_df[filtered_df['Status'].isin(['Instock', 'Calibrated'])]
    
    if show_critical:
        try:
            critical_mask = (
                (filtered_df['Status'] == 'Instock') |
                (pd.to_datetime(filtered_df['Next Calibration']) <= datetime.now() + timedelta(days=7))
            )
            filtered_df = filtered_df[critical_mask]
        except Exception:
            st.warning("Error filtering critical items")

    return filtered_df

def render_inventory_table(filtered_df):
    """Render the inventory data table with the original columns."""
    # Original column configuration
    column_config = {
        "Serial Number": st.column_config.TextColumn(
            "Serial Number",
            help="Unique identifier for the probe",
            width="medium"
        ),
        "Type": st.column_config.SelectboxColumn(
            "Type",
            help="Type of probe",
            width="medium",
            options=sorted(filtered_df['Type'].unique().tolist())
        ),
        "Manufacturer": st.column_config.TextColumn(
            "Manufacturer",
            help="Probe manufacturer",
            width="medium"
        ),
        "KETOS P/N": st.column_config.TextColumn(
            "KETOS P/N",
            help="KETOS part number",
            width="medium"
        ),
        "Mfg P/N": st.column_config.TextColumn(
            "Mfg P/N",
            help="Manufacturer part number",
            width="medium"
        ),
        "Status": st.column_config.SelectboxColumn(
            "Status",
            help="Current status of the probe",
            width="small",
            options=["Instock", "Calibrated", "Shipped", "Scraped"]
        ),
        "Entry Date": st.column_config.TextColumn(
            "Entry Date",
            help="Date when the probe was added to inventory",
            width="small"
        ),
        "Last Modified": st.column_config.TextColumn(
            "Last Modified",
            help="Last modification date",
            width="small"
        ),
        "Next Calibration": st.column_config.TextColumn(
            "Next Calibration",
            help="Date when next calibration is due",
            width="small"
        ),
        "Change Date": st.column_config.TextColumn(
            "Change Date",
            help="Date of last status change",
            width="small"
        )
    }

    # Display full dataframe with all original columns
    return st.data_editor(
        filtered_df,  # Use entire dataframe instead of selected columns
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        key="inventory_editor"
    )


def save_inventory_changes(edited_df, original_df):
    """Save changes made to the inventory."""
    if not edited_df.equals(original_df):
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Save Changes", type="primary"):
                try:
                    # Update all columns in the main inventory
                    for idx, row in edited_df.iterrows():
                        if idx in st.session_state.inventory.index:
                            st.session_state.inventory.loc[idx] = row
                            # Update Last Modified date
                            st.session_state.inventory.at[idx, 'Last Modified'] = datetime.now().strftime("%Y-%m-%d")
                    
                    if st.session_state.inventory_manager.save_inventory(st.session_state.inventory):
                        st.success("✅ Changes saved successfully!")
                        time.sleep(1)
                        st.rerun()
                    return True
                except Exception as e:
                    st.error(f"Error saving changes: {str(e)}")
                    return False
    return False

def render_tools_section(filtered_df, df):
    """Render the tools section with exports and debug info."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Export Options")
        if st.button("Export Filtered Data"):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                "📥 Download CSV",
                csv,
                f"inventory_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv"
            )
    
    with col2:
        st.markdown("#### System Status")
        if st.session_state.inventory_manager.verify_connection():
            st.success("✅ Connected to Google Sheets")
            st.info(f"Last Update: {st.session_state.get('last_save_time', 'Never')}")
        else:
            st.error("❌ Connection Error")

    with st.expander("🛠️ Debug Information", expanded=False):
        st.json({
            "Total Records": len(df),
            "Filtered Records": len(filtered_df),
            "Last Save": st.session_state.get('last_save_time', 'Never'),
            "Active Filters": len(filtered_df) != len(df),
            "Connection Status": "Connected" if st.session_state.inventory_manager.verify_connection() else "Disconnected"
        })

def inventory_review_page():
    """Main inventory review page."""
    st.markdown("# 📦 Inventory Review")
    
    # Initialize and check inventory
    if 'inventory_manager' not in st.session_state:
        st.error("Inventory manager not initialized")
        return
        
    df = st.session_state.inventory
    if df.empty:
        st.warning("No inventory data available")
        return

    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["📊 Overview", "📋 Inventory List", "⚙️ Tools"])

    with tab1:
        # Overview tab content
        render_inventory_stats(df)
        render_status_legend()

    with tab2:
        # Inventory list tab content
        filtered_df = render_advanced_filters(df)
        edited_df = render_inventory_table(filtered_df)
        save_inventory_changes(edited_df, filtered_df)

    with tab3:
        # Tools tab content
        render_tools_section(filtered_df, df)
if __name__ == "__main__":
    inventory_review_page()
