# inventory_review.py

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import time
from .inventory_manager import STATUS_COLORS

# Constants
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
        st.metric("Total Probes", f"{total:,}")
    with col2:
        st.metric("Active Probes", f"{active:,}", 
                 f"{(active/total*100):.1f}% of total" if total > 0 else "0%")
    with col3:
        st.metric("Need Calibration", f"{need_cal:,}", 
                 f"{(need_cal/total*100):.1f}% of total" if total > 0 else "0%")
    with col4:
        st.metric("Shipped Probes", f"{shipped:,}", 
                 f"{(shipped/total*100):.1f}% of total" if total > 0 else "0%")

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
                value=(datetime.now() - timedelta(days=30), datetime.now()),
                help="Filter by Entry Date"
            )

        # Quick filters
        st.markdown("#### Quick Filters")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            show_expired = st.checkbox("Show Expired Calibrations")
        with col2:
            show_recent = st.checkbox("Recent Changes (7 days)")
        with col3:
            show_critical = st.checkbox("Needs Attention")
        with col4:
            show_mine = st.checkbox("My Registrations")

    # Apply filters
    filtered_df = df.copy()
    
    if status_filter:
        filtered_df = filtered_df[filtered_df['Status'].isin(status_filter)]
    if type_filter:
        filtered_df = filtered_df[filtered_df['Type'].isin(type_filter)]
    if len(date_range) == 2:
        filtered_df = filtered_df[
            (pd.to_datetime(filtered_df['Entry Date']).dt.date >= date_range[0]) &
            (pd.to_datetime(filtered_df['Entry Date']).dt.date <= date_range[1])
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
        mask = (filtered_df['Status'] == 'Instock') | (
            pd.to_datetime(filtered_df['Next Calibration']) <= datetime.now() + timedelta(days=7)
        )
        filtered_df = filtered_df[mask]
    if show_mine:
        filtered_df = filtered_df[filtered_df['Registered By'] == st.session_state.get('username', '')]

    return filtered_df

def render_inventory_table(filtered_df):
    """Render the inventory data table."""
    # Column configuration
    column_config = {
        "Serial Number": st.column_config.TextColumn(
            "Serial Number",
            help="Click serial number to manage probe",
            width="medium"
        ),
        "Type": st.column_config.TextColumn(
            "Type",
            help="Type of probe",
            width="medium",
        ),
        "Status": st.column_config.TextColumn(
            "Status",
            help="Current status of probe",
            width="small",
        ),
        "Entry Date": st.column_config.TextColumn(
            "Entry Date",
            help="Date when probe was added",
            width="small",
        ),
        "Last Modified": st.column_config.TextColumn(
            "Last Modified",
            help="Last modification date",
            width="small",
        ),
        "Next Calibration": st.column_config.TextColumn(
            "Next Calibration",
            help="Next calibration due date",
            width="small",
        ),
        "Registered By": st.column_config.TextColumn(
            "Registered By",
            help="User who registered the probe",
            width="medium",
        ),
        "Calibrated By": st.column_config.TextColumn(
            "Calibrated By",
            help="User who last calibrated the probe",
            width="medium",
        )
    }

    # Add styling for status colors
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

    # Initialize state for selected probe if not exists
    if 'selected_probe_sn' not in st.session_state:
        st.session_state.selected_probe_sn = None
        
    # Add interactivity without changing table appearance
    selected_rows = st.data_editor(
        display_df,
        column_config=column_config,
        hide_index=True,
        key="probe_table",
        use_container_width=True,
        disabled=["Type", "Status", "Entry Date", "Last Modified", "Next Calibration", 
                 "Registered By", "Calibrated By"]
    )

    # Handle row selection and actions
    if selected_rows is not None and not selected_rows.equals(display_df):
        # Find the changed row
        changed_mask = (selected_rows != display_df).any(axis=1)
        if changed_mask.any():
            selected_sn = selected_rows[changed_mask].iloc[0]['Serial Number']
            st.session_state.selected_probe_sn = selected_sn
            
            # Show action dialog
            with st.expander(f"Actions for Probe: {selected_sn}", expanded=True):
                action = st.radio(
                    "Choose action:",
                    ["Calibrate", "Change Status"],
                    horizontal=True,
                    key=f"action_{selected_sn}"
                )
                
                if action == "Calibrate":
                    if st.button("Go to Calibration Page", key=f"cal_{selected_sn}", type="primary"):
                        st.session_state.selected_probe = selected_sn
                        st.session_state.page = "Probe Calibration"
                        st.rerun()
                
                elif action == "Change Status":
                    new_status = st.selectbox(
                        "Select new status:",
                        ["Instock", "Calibrated", "Shipped", "Scraped"],
                        key=f"status_{selected_sn}"
                    )
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        if st.button("Confirm", type="primary", key=f"confirm_{selected_sn}"):
                            if st.session_state.inventory_manager.update_probe_status(selected_sn, new_status):
                                st.success(f"Updated status to {new_status}")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Failed to update status")

    return selected_rows

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

if __name__ == "__main__":
    inventory_review_page()
