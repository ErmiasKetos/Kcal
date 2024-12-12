
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
from .inventory_manager import STATUS_COLORS

def render_inventory_stats(df):
    """Render inventory statistics cards."""
    st.markdown("### 📊 Inventory Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total = len(df)
        st.metric(
            "Total Probes",
            total,
            help="Total number of probes in inventory"
        )
        
    with col2:
        active = len(df[df['Status'].isin(['Instock', 'Calibrated'])])
        st.metric(
            "Active Probes",
            active,
            f"{(active/total*100):.1f}% of total" if total > 0 else "0%",
            help="Probes that are either in stock or calibrated"
        )
        
    with col3:
        need_cal = len(df[df['Status'] == 'Instock'])
        st.metric(
            "Need Calibration",
            need_cal,
            delta_color="inverse",
            help="Probes that need calibration"
        )
        
    with col4:
        shipped = len(df[df['Status'] == 'Shipped'])
        st.metric(
            "Shipped Probes",
            shipped,
            f"{(shipped/total*100):.1f}% of total" if total > 0 else "0%",
            help="Probes that have been shipped"
        )

def render_advanced_filters():
    """Render advanced filtering options."""
    with st.expander("🔍 Advanced Filters", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            status_filter = st.multiselect(
                "Status",
                ["Instock", "Calibrated", "Shipped", "Scraped"],
                default=["Instock", "Calibrated"]
            )
            
        with col2:
            type_filter = st.multiselect(
                "Probe Type",
                ["pH Probe", "DO Probe", "ORP Probe", "EC Probe"]
            )
    
    return status_filter, type_filter

def inventory_review_page():
    """Enhanced inventory review page."""
    st.markdown("# 📦 Inventory Review")
    
    # Initialize inventory
    if 'inventory_manager' not in st.session_state:
        st.error("Inventory manager not initialized")
        return
        
    df = st.session_state.inventory
    if df.empty:
        st.warning("No inventory data available")
        return

    # Inventory Statistics
    render_inventory_stats(df)
    
    # Advanced Filters
    status_filter, type_filter = render_advanced_filters()
    
    # Apply filters
    filtered_df = df.copy()
    if status_filter:
        filtered_df = filtered_df[filtered_df['Status'].isin(status_filter)]
    if type_filter:
        filtered_df = filtered_df[filtered_df['Type'].isin(type_filter)]

    # Search bar
    search_query = st.text_input(
        "🔍 Search by Serial Number, Type, or Manufacturer",
        help="Enter any part of the Serial Number, Type, or Manufacturer"
    )
    if search_query:
        search_mask = filtered_df.apply(
            lambda x: any(
                search_query.lower() in str(val).lower() 
                for val in x
            ),
            axis=1
        )
        filtered_df = filtered_df[search_mask]

    # Display filtered inventory
    st.markdown("### Inventory Data")
    
    # Add column configuration
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
            options=["pH Probe", "DO Probe", "ORP Probe", "EC Probe"]
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
        "Next Calibration": st.column_config.TextColumn(
            "Next Calibration",
            help="Date when next calibration is due",
            width="small"
        ),
        "Last Modified": st.column_config.TextColumn(
            "Last Modified",
            help="Last modification date",
            width="small"
        )
    }

    # Apply custom styling to the dataframe
    edited_df = st.data_editor(
        filtered_df,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        key="inventory_editor"
    )

    # Check for changes and save
    if not edited_df.equals(filtered_df):
        if st.button("Save Changes"):
            try:
                # Update the main inventory with edited values
                for idx, row in edited_df.iterrows():
                    if idx in st.session_state.inventory.index:
                        st.session_state.inventory.loc[idx] = row
                
                if st.session_state.inventory_manager.save_inventory(st.session_state.inventory):
                    st.success("✅ Changes saved successfully!")
                    st.rerun()
                else:
                    st.error("Failed to save changes")
            except Exception as e:
                st.error(f"Error saving changes: {str(e)}")

    # Export options
    st.markdown("### Export Options")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Export Filtered Data (CSV)"):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                "Download CSV",
                csv,
                f"inventory_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv"
            )
    
    with col2:
        if st.button("Export Full Inventory (CSV)"):
            csv = df.to_csv(index=False)
            st.download_button(
                "Download CSV",
                csv,
                f"full_inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv"
            )

    # Status info
    st.markdown("### Status Color Legend")
    status_cols = st.columns(len(STATUS_COLORS))
    for i, (status, color) in enumerate(STATUS_COLORS.items()):
        status_cols[i].markdown(
            f'<div style="background-color: {color}; padding: 10px; '
            f'border-radius: 5px; text-align: center; margin: 5px;">'
            f'{status}</div>',
            unsafe_allow_html=True
        )

    # Debug Information
    with st.expander("🛠️ Debug Info", expanded=False):
        st.write({
            "Total Records": len(df),
            "Filtered Records": len(filtered_df),
            "Last Save": st.session_state.get('last_save_time', 'Never'),
            "Connection Status": '✅ Connected' if st.session_state.inventory_manager.verify_connection() else '❌ Disconnected'
        })

if __name__ == "__main__":
    inventory_review_page()
