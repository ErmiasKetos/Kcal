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

def check_backup_needed():
    """Check if daily backup is needed."""
    if 'last_backup_date' not in st.session_state:
        st.session_state.last_backup_date = None

    if (st.session_state.last_backup_date is None or 
        datetime.now().date() > st.session_state.last_backup_date):
        if st.session_state.inventory_manager.create_backup():
            st.session_state.last_backup_date = datetime.now().date()
            return True
    return False

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
    # Add an action column to the table
    display_df = filtered_df.copy()
    display_df.insert(1, 'Action', ['Select' for _ in range(len(display_df))])
    
    # Column configuration
    column_config = {
        "Serial Number": st.column_config.TextColumn(
            "Serial Number",
            help="Probe serial number",
            width="medium"
        ),
        "Action": st.column_config.SelectboxColumn(
            "Action",
            width="medium",
            options=["Select", "Calibrate", "Change Status"],
            help="Choose action for probe"
        ),
        "Type": st.column_config.TextColumn(
            "Type",
            help="Type of probe",
            width="medium",
        ),
        "Status": st.column_config.SelectboxColumn(  # Changed to SelectboxColumn
            "Status",
            help="Current status of probe",
            width="small",
            options=list(STATUS_COLORS.keys())
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

    # Custom styling for the data editor
    st.markdown("""
        <style>
            /* Status cell styling */
            .stDataFrame td:nth-child(4) {  /* Adjust column number as needed */
                padding: 0 !important;
            }
            
            .status-cell {
                padding: 4px 8px;
                border-radius: 12px;
                text-align: center;
                font-weight: 500;
                margin: 2px;
                display: inline-block;
                min-width: 100px;
            }
            
            /* Status-specific colors */
            .status-Instock {
                background-color: rgba(255, 215, 0, 0.2);
                color: #FFD700;
            }
            .status-Calibrated {
                background-color: rgba(50, 205, 50, 0.2);
                color: #32CD32;
            }
            .status-Shipped {
                background-color: rgba(65, 105, 225, 0.2);
                color: #4169E1;
            }
            .status-Scraped {
                background-color: rgba(220, 20, 60, 0.2);
                color: #DC143C;
            }
        </style>
    """, unsafe_allow_html=True)

    # Render table
    edited_df = st.data_editor(
        display_df,
        column_config=column_config,
        hide_index=True,
        use_container_width=True,
        disabled=["Serial Number", "Type", "Status", "Entry Date", "Last Modified", 
                 "Next Calibration", "Registered By", "Calibrated By"]
    )

    # Handle actions
    for idx, row in edited_df.iterrows():
        if row['Action'] == 'Calibrate':
            st.session_state.selected_probe = row['Serial Number']
            st.session_state.page = "Probe Calibration"
            st.rerun()
        elif row['Action'] == 'Change Status':
            with st.expander(f"Change Status for {row['Serial Number']}", expanded=True):
                new_status = st.selectbox(
                    "Select new status:",
                    ["Instock", "Calibrated", "Shipped", "Scraped"],
                    key=f"status_{row['Serial Number']}"
                )
                if st.button("Update Status", type="primary", key=f"update_{row['Serial Number']}"):
                    if st.session_state.inventory_manager.update_probe_status(
                        row['Serial Number'], new_status
                    ):
                        st.success(f"Updated status to {new_status}")
                        # Reset action to Select
                        edited_df.at[idx, 'Action'] = 'Select'
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Failed to update status")

    # Remove the Action column before returning
    if 'Action' in edited_df.columns:
        edited_df = edited_df.drop('Action', axis=1)

    return edited_df
    
def render_tools_section(filtered_df, df):
    """Render tools and system status section."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Export & Backup Options")
        col_exp, col_bak = st.columns(2)
        
        with col_exp:
            if st.button("Export Data"):
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    "📥 Download CSV",
                    csv,
                    f"inventory_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "text/csv"
                )
        
        with col_bak:
            if st.button("Create Manual Backup"):
                if st.session_state.inventory_manager.create_backup():
                    st.success("✅ Backup created successfully!")
                    st.session_state.last_backup_date = datetime.now().date()
                else:
                    st.error("❌ Failed to create backup")
    
    with col2:
        st.markdown("#### System Status")
        if st.session_state.inventory_manager.verify_connection():
            st.success("✅ Connected to Database")
            
            # Show backup status
            if st.session_state.last_backup_date:
                st.info(f"Last Backup: {st.session_state.last_backup_date}")
            else:
                st.warning("No recent backup found")
            
            st.info(f"Last Update: {st.session_state.get('last_save_time', 'Never')}")
        else:
            st.error("❌ Database Connection Error")

    # Debug Information
    with st.expander("🛠️ Debug Information", expanded=False):
        st.json({
            "Total Records": len(df),
            "Filtered Records": len(filtered_df),
            "Last Save": st.session_state.get('last_save_time', 'Never'),
            "Last Backup": str(st.session_state.get('last_backup_date', 'Never')),
            "Connection Status": "Connected" if st.session_state.inventory_manager.verify_connection() else "Disconnected"
        })

def inventory_review_page():
    """Main inventory review page."""
    st.markdown("# 📦 Inventory Review")
    
    if 'inventory_manager' not in st.session_state:
        st.error("Inventory manager not initialized")
        return
    
    # Check for daily backup
    check_backup_needed()
    
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
