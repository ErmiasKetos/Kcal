# src/inventory_review.py

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import time
from .inventory_manager import STATUS_COLORS

# Constants for the inventory review
ESSENTIAL_COLUMNS = [
    "Serial Number", "Type", "Status", "Entry Date", 
    "Next Calibration", "Last Modified", "Registered By", "Calibrated By"
]

STATUS_INFO = {
    'Instock': {
        'color': '#FFD700',
        'desc': 'Probes available for calibration and deployment',
        'icon': '📦'
    },
    'Calibrated': {
        'color': '#32CD32',
        'desc': 'Probes that have been calibrated and are ready for shipping',
        'icon': '✅'
    },
    'Shipped': {
        'color': '#4169E1',
        'desc': 'Probes that have been sent to customers',
        'icon': '🚢'
    },
    'Scraped': {
        'color': '#DC143C',
        'desc': 'Probes that are no longer in service',
        'icon': '❌'
    }
}

def render_status_legend():
    """Render status color legend with descriptions."""
    st.markdown("""
        <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 10px; margin-bottom: 20px;'>
    """, unsafe_allow_html=True)
    
    for status, info in STATUS_INFO.items():
        st.markdown(f"""
            <div style='
                padding: 15px;
                border-radius: 8px;
                background-color: {info['color']}20;
                border-left: 4px solid {info['color']};
            '>
                <div style='font-weight: bold; margin-bottom: 5px;'>
                    {info['icon']} {status}
                </div>
                <div style='font-size: 0.9em; color: #666;'>
                    {info['desc']}
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

def render_inventory_stats(df):
    """Render inventory statistics."""
    st.markdown("### 📊 Inventory Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total = len(df)
    active = len(df[df['Status'].isin(['Instock', 'Calibrated'])])
    need_cal = len(df[df['Status'] == 'Instock'])
    shipped = len(df[df['Status'] == 'Shipped'])
    
    with col1:
        st.metric(
            "Total Probes",
            f"{total:,}",
            help="Total number of probes in inventory"
        )
    
    with col2:
        st.metric(
            "Active Probes",
            f"{active:,}",
            f"{(active/total*100):.1f}% of total" if total > 0 else None,
            help="Probes available for use (Instock + Calibrated)"
        )
    
    with col3:
        st.metric(
            "Need Calibration",
            f"{need_cal:,}",
            f"{(need_cal/total*100):.1f}% of total" if total > 0 else None,
            help="Probes requiring calibration"
        )
    
    with col4:
        st.metric(
            "Shipped Probes",
            f"{shipped:,}",
            f"{(shipped/total*100):.1f}% of total" if total > 0 else None,
            help="Probes currently deployed"
        )

def render_advanced_filters(df):
    """Render advanced filtering options."""
    with st.expander("🔍 Advanced Filters", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            status_filter = st.multiselect(
                "Status",
                options=list(STATUS_INFO.keys()),
                default=["Instock", "Calibrated"]
            )
            
            type_filter = st.multiselect(
                "Probe Type",
                options=sorted(df['Type'].unique())
            )

        with col2:
            date_range = st.date_input(
                "Date Range",
                value=(
                    datetime.now() - timedelta(days=30),
                    datetime.now()
                ),
                help="Filter by Entry Date"
            )

        # Quick filters
        st.markdown("#### Quick Filters")
        quick_filter_cols = st.columns(4)
        
        with quick_filter_cols[0]:
            show_expired = st.checkbox(
                "Show Expired Calibrations",
                help="Show probes with expired calibration dates"
            )
        
        with quick_filter_cols[1]:
            show_recent = st.checkbox(
                "Recent Changes (7 days)",
                help="Show probes modified in the last 7 days"
            )
        
        with quick_filter_cols[2]:
            show_critical = st.checkbox(
                "Needs Attention",
                help="Show probes needing immediate attention"
            )
        
        with quick_filter_cols[3]:
            show_registered_by = st.checkbox(
                "My Registrations",
                help="Show probes registered by current user"
            )

    # Apply filters
    filtered_df = df.copy()

    if status_filter:
        filtered_df = filtered_df[filtered_df['Status'].isin(status_filter)]
    
    if type_filter:
        filtered_df = filtered_df[filtered_df['Type'].isin(type_filter)]
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[
            (pd.to_datetime(filtered_df['Entry Date']).dt.date >= start_date) &
            (pd.to_datetime(filtered_df['Entry Date']).dt.date <= end_date)
        ]
    
    if show_expired:
        filtered_df = filtered_df[
            pd.to_datetime(filtered_df['Next Calibration']) <= datetime.now()
        ]
    
    if show_recent:
        filtered_df = filtered_df[
            pd.to_datetime(filtered_df['Last Modified']) >= datetime.now() - timedelta(days=7)
        ]
    
    if show_critical:
        critical_mask = (
            (filtered_df['Status'] == 'Instock') |
            (pd.to_datetime(filtered_df['Next Calibration']) <= datetime.now() + timedelta(days=7))
        )
        filtered_df = filtered_df[critical_mask]
    
    if show_registered_by:
        filtered_df = filtered_df[
            filtered_df['Registered By'] == st.session_state.get('username', '')
        ]

    return filtered_df


def render_inventory_table(filtered_df):
    """Render the inventory data table."""
    # Configure columns with colored status
    column_config = {
        "Serial Number": st.column_config.Column(
            "Serial Number",
            help="Click to manage probe",
            required=True,
            width="medium"
        ),
        "Type": st.column_config.SelectboxColumn(
            "Type",
            help="Type of probe",
            width="medium",
            options=sorted(filtered_df['Type'].unique().tolist())
        ),
        "Status": st.column_config.Column(
            "Status",
            help="Current status of the probe",
            width="small"
        ),
        "Entry Date": st.column_config.DateColumn(
            "Entry Date",
            help="Date when the probe was added to inventory",
            width="small"
        ),
        "Last Modified": st.column_config.DateColumn(
            "Last Modified",
            help="Last modification date",
            width="small"
        ),
        "Next Calibration": st.column_config.DateColumn(
            "Next Calibration",
            help="Date when next calibration is due",
            width="small"
        ),
        "Registered By": st.column_config.TextColumn(
            "Registered By",
            help="User who registered the probe",
            width="medium"
        ),
        "Calibrated By": st.column_config.TextColumn(
            "Calibrated By",
            help="User who last calibrated the probe",
            width="medium"
        )
    }

    # Apply colored status
    display_df = filtered_df.copy()
    display_df['Status'] = display_df['Status'].apply(
        lambda x: f"""
            <div style='
                background-color: {STATUS_COLORS.get(x, "#CCCCCC")}40;
                color: {STATUS_COLORS.get(x, "#000000")};
                padding: 4px 8px;
                border-radius: 12px;
                text-align: center;
                font-weight: 500;
            '>
                {x}
            </div>
        """
    )

    # Add table styling
    st.markdown("""
        <style>
            .stDataFrame td {
                vertical-align: middle !important;
            }
            .stDataFrame td:nth-child(3) div {
                margin: auto;
                width: fit-content;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # Render table and get edited data
    edited_df = st.data_editor(
        display_df,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        key="inventory_editor",
        on_change=handle_table_click
    )

    return edited_df

def handle_table_click():
    """Handle clicks in the table."""
    if 'edited_rows' in st.session_state.inventory_editor:
        for idx, changes in st.session_state.inventory_editor['edited_rows'].items():
            if 'Serial Number' in changes:
                serial = changes['Serial Number']
                # Create popup for actions
                with st.popover(f"Actions for {serial}"):
                    action = st.radio(
                        "Choose action:",
                        ["Calibrate", "Change Status"],
                        key=f"action_{serial}"
                    )
                    
                    if action == "Calibrate":
                        if st.button("Go to Calibration"):
                            st.session_state.selected_probe = serial
                            st.session_state.page = "Probe Calibration"
                            st.rerun()
                    
                    elif action == "Change Status":
                        new_status = st.selectbox(
                            "New Status:",
                            ["Instock", "Calibrated", "Shipped", "Scraped"],
                            key=f"status_{serial}"
                        )
                        if st.button("Update Status"):
                            if st.session_state.inventory_manager.update_probe_status(serial, new_status):
                                st.success(f"Status updated to {new_status}")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Failed to update status")
def render_tools_section(filtered_df, df):
    """Render tools and system status section."""
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
            st.success("✅ Connected to Database")
            st.info(f"Last Update: {st.session_state.get('last_save_time', 'Never')}")
        else:
            st.error("❌ Database Connection Error")

    with st.expander("🛠️ Debug Information", expanded=False):
        st.json({
            "Total Records": len(df),
            "Filtered Records": len(filtered_df),
            "Last Save": st.session_state.get('last_save_time', 'Never'),
            "Current User": st.session_state.get('username', 'Not logged in'),
            "Connection Status": "Connected" if st.session_state.inventory_manager.verify_connection() else "Disconnected"
        })

def inventory_review_page():
    """Main inventory review page."""
    st.markdown("# 📦 Inventory Review")
    
    if 'inventory_manager' not in st.session_state:
        st.error("Inventory manager not initialized")
        return
    
    df = st.session_state.inventory
    if df.empty:
        st.warning("No inventory data available")
        return

    tab1, tab2, tab3 = st.tabs(["📊 Overview", "📋 Inventory List", "⚙️ Tools"])

    with tab1:
        render_inventory_stats(df)
        render_status_legend()

    with tab2:
        filtered_df = render_advanced_filters(df)
        edited_df = render_inventory_table(filtered_df)
        if not edited_df.equals(filtered_df):
            if st.button("Save Changes", type="primary"):
                if st.session_state.inventory_manager.save_inventory(edited_df):
                    st.success("✅ Changes saved successfully!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Failed to save changes")

    with tab3:
        render_tools_section(filtered_df, df)

if __name__ == "__main__":
    inventory_review_page()
