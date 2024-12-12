# src/inventory_review.py

import streamlit as st
import pandas as pd
from datetime import datetime
import time
import json
from .inventory_manager import InventoryManager, STATUS_COLORS

def render_inventory_table(filtered_df):
    """Render interactive inventory table."""
    # Column configuration with clickable serial numbers
    column_config = {
        "Serial Number": st.column_config.TextColumn(
            "Serial Number",
            help="Click for actions",
            width="medium"
        ),
        "Type": st.column_config.TextColumn(
            "Type",
            width="medium"
        ),
        "Status": st.column_config.Column(
            "Status",
            width="small",
        ),
        "Manufacturer": st.column_config.TextColumn(
            "Manufacturer",
            width="medium"
        ),
        "KETOS P/N": st.column_config.TextColumn(
            "KETOS P/N",
            width="medium"
        ),
        "Entry Date": st.column_config.TextColumn(
            "Entry Date",
            width="small"
        ),
        "Next Calibration": st.column_config.TextColumn(
            "Next Calibration",
            width="small"
        )
    }

    # Initialize session state for selected probe
    if 'selected_row' not in st.session_state:
        st.session_state.selected_row = None

    # Display the dataframe with the configured columns
    edited_df = st.data_editor(
        filtered_df,
        column_config=column_config,
        disabled=["Type", "Manufacturer", "KETOS P/N", "Entry Date", "Next Calibration"],
        hide_index=True,
        use_container_width=True,
        num_rows="dynamic",
        key="inventory_editor"
    )

    # Handle row selection
    if edited_df is not None:
        for index, row in edited_df.iterrows():
            sn = row['Serial Number']
            # Create a unique key for each row's action buttons
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button(f"Select Action for {sn}", key=f"select_{sn}"):
                    st.session_state.selected_row = row

    # Handle selected row actions
    if st.session_state.selected_row is not None:
        row = st.session_state.selected_row
        serial = row['Serial Number']

        st.markdown(f"### Actions for {serial}")
        action = st.radio(
            "Choose action:",
            ["Calibrate", "Change Status"],
            key=f"action_{serial}"
        )

        if action == "Calibrate":
            if st.button("Proceed to Calibration"):
                st.session_state.selected_probe = serial
                st.session_state.page = "Probe Calibration"
                st.rerun()

        elif action == "Change Status":
            new_status = st.selectbox(
                "Select new status:",
                ["Instock", "Calibrated", "Shipped", "Scraped"],
                key=f"status_{serial}"
            )
            
            if st.button("Update Status"):
                if 'inventory_manager' in st.session_state:
                    success = st.session_state.inventory_manager.update_probe_status(serial, new_status)
                    if success:
                        st.success(f"✅ Status updated to {new_status}")
                        st.session_state.selected_row = None
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Failed to update status")

        if st.button("Cancel"):
            st.session_state.selected_row = None
            st.rerun()

def inventory_review_page():
    """Display and manage inventory."""
    st.markdown("<h2 style='color: #0071ba;'>Inventory Review</h2>", unsafe_allow_html=True)
    
    # Initialize inventory if needed
    if 'inventory_manager' not in st.session_state:
        st.session_state.inventory_manager = InventoryManager()
        st.session_state.inventory_manager.initialize_inventory()
    
    # Status filter
    status_filter = st.selectbox(
        "Filter by Status",
        ["All", "Instock", "Calibrated", "Shipped", "Scraped"]
    )
    
    # Get filtered inventory
    filtered_df = get_filtered_inventory(status_filter)
    
    # Apply status colors to the Status column
    if not filtered_df.empty:
        # Create a style function for the Status column
        def style_status(val):
            return f'background-color: {STATUS_COLORS.get(val, "white")}'
        
        styled_df = filtered_df.style.applymap(
            style_status, 
            subset=['Status']
        )
        
        # Display the inventory table
        render_inventory_table(styled_df)
        
        # Display summary statistics
        st.markdown("### Inventory Summary")
        status_counts = filtered_df['Status'].value_counts()
        summary_cols = st.columns(len(STATUS_COLORS))
        for i, status in enumerate(STATUS_COLORS.keys()):
            count = status_counts.get(status, 0)
            summary_cols[i].metric(
                label=status,
                value=count,
                delta=f"{count/len(filtered_df)*100:.1f}%" if len(filtered_df) > 0 else "0%"
            )
    else:
        st.info("No records found for the selected filter.")

    # Export options
    st.markdown("### Export Options")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Export Filtered Data"):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                "Download CSV",
                csv,
                f"inventory_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv"
            )
    
    with col2:
        if st.button("Export Full Inventory"):
            csv = st.session_state.inventory.to_csv(index=False)
            st.download_button(
                "Download CSV",
                csv,
                f"full_inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv"
            )

if __name__ == "__main__":
    inventory_review_page()
