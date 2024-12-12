
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import time
from .inventory_manager import STATUS_COLORS

# Constants for inventory review
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

def handle_click():
    """Handle table interaction."""
    if st.session_state.inventory_editor.get('edited_rows'):
        for idx in st.session_state.inventory_editor['edited_rows']:
            row = st.session_state.inventory[idx]
            serial = row['Serial Number']
            with st.popover(f"Actions for {serial}", use_container_width=True):
                action = st.radio(
                    "Choose action:",
                    ["Calibrate", "Change Status"],
                    key=f"action_{serial}",
                    horizontal=True
                )
                
                if action == "Calibrate":
                    if st.button("Proceed to Calibration", type="primary", key=f"cal_{serial}"):
                        st.session_state.selected_probe = serial
                        st.session_state.page = "Probe Calibration"
                        st.rerun()
                else:
                    new_status = st.selectbox(
                        "Select new status:",
                        ["Instock", "Calibrated", "Shipped", "Scraped"],
                        key=f"status_{serial}"
                    )
                    if st.button("Update Status", type="primary", key=f"update_{serial}"):
                        if st.session_state.inventory_manager.update_probe_status(serial, new_status):
                            st.success(f"Updated status to {new_status}")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to update status")


def render_inventory_table(filtered_df):
    """Render the inventory data table."""
    # First, add a column for actions if clicked
    if 'selected_sn' not in st.session_state:
        st.session_state.selected_sn = None
        
    # Column configuration
    column_config = {
        "Serial Number": st.column_config.TextColumn(
            "Serial Number",
            help="Select to manage probe",
            width="medium"
        ),
        "Actions": st.column_config.SelectboxColumn(  # Add new actions column
            "Actions",
            help="Choose action for probe",
            width="medium",
            options=["", "Calibrate", "Change Status"]
        ),
        "Type": st.column_config.TextColumn(
            "Type",
            help="Type of probe",
            width="medium"
        ),
        "Status": st.column_config.TextColumn(
            "Status",
            help="Current status of the probe",
            width="small"
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

    # Prepare display dataframe with actions column
    display_df = filtered_df.copy()
    display_df.insert(1, 'Actions', "")  # Add empty actions column
    
    # Apply colored status
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

    # Render table
    edited_df = st.data_editor(
        display_df,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        disabled=["Serial Number", "Status", "Entry Date", "Last Modified", 
                 "Next Calibration", "Registered By", "Calibrated By"]
    )

    # Handle actions from the table
    if edited_df is not None:
        for idx, row in edited_df.iterrows():
            if row['Actions'] == "Calibrate":
                st.session_state.page = "Probe Calibration"
                st.session_state.selected_probe = row['Serial Number']
                st.rerun()
            elif row['Actions'] == "Change Status":
                with st.expander(f"Change Status for {row['Serial Number']}", expanded=True):
                    new_status = st.selectbox(
                        "Select new status:",
                        ["Instock", "Calibrated", "Shipped", "Scraped"],
                        key=f"new_status_{row['Serial Number']}"
                    )
                    if st.button("Confirm Status Change", key=f"confirm_{row['Serial Number']}"):
                        if st.session_state.inventory_manager.update_probe_status(
                            row['Serial Number'], new_status
                        ):
                            st.success(f"Updated status to {new_status}")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to update status")

    # Remove the Actions column before returning
    if 'Actions' in edited_df.columns:
        edited_df = edited_df.drop('Actions', axis=1)
    
    return edited_df
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
