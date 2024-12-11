import streamlit as st
import pandas as pd
import time
import json
from datetime import datetime
from .inventory_manager import InventoryManager, STATUS_COLORS

def display_calibration_details(probe_data):
    """Display detailed calibration information in the inventory review."""
    if 'Calibration Data' in probe_data and probe_data['Calibration Data']:
        try:
            calibration_data = json.loads(probe_data['Calibration Data'])
            
            st.markdown("#### Calibration Details")
            
            if 'calibration_date' in calibration_data:
                st.write(f"**Calibration Date:** {calibration_data['calibration_date']}")
            
            # Display pH calibration data if present
            if probe_data['Type'] == "pH Probe":
                for buffer_label in ["pH 4", "pH 7", "pH 10"]:
                    if any(f"{buffer_label}" in key for key in calibration_data.keys()):
                        st.markdown(f"##### {buffer_label} Buffer Data")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"Control Number: {calibration_data.get(f'{buffer_label}_control', 'N/A')}")
                            st.write(f"Expiration Date: {calibration_data.get(f'{buffer_label}_exp', 'N/A')}")
                            st.write(f"Date Opened: {calibration_data.get(f'{buffer_label}_opened', 'N/A')}")
                        
                        with col2:
                            st.write("pH Measurements:")
                            st.write(f"- Initial: {calibration_data.get(f'{buffer_label}_initial', 'N/A')} pH")
                            st.write(f"- Calibrated: {calibration_data.get(f'{buffer_label}_calibrated', 'N/A')} pH")
                            st.write("mV Measurements:")
                            st.write(f"- Initial: {calibration_data.get(f'{buffer_label}_initial_mv', 'N/A')} mV")
        except Exception as e:
            st.error(f"Error displaying calibration data: {str(e)}")

def inventory_review_page():
    """Display and manage inventory"""
    st.markdown("<h2 style='color: #0071ba;'>Inventory Review</h2>", unsafe_allow_html=True)
    
    # Initialize inventory manager if not exists
    if 'inventory_manager' not in st.session_state:
        st.session_state.inventory_manager = InventoryManager()
        st.session_state.inventory_manager.initialize_inventory()

    # Status filter with added 'Calibrated' status
    status_filter = st.selectbox(
        "Filter by Status",
        ["All", "Instock", "Calibrated", "Shipped", "Scraped"]
    )
    
    # Get filtered inventory
    filtered_inventory = st.session_state.inventory_manager.get_filtered_inventory(status_filter)
    
    # Display inventory with styling
    if not filtered_inventory.empty:
        # Add status color preview
        st.markdown("### Status Color Legend")
        legend_cols = st.columns(len(STATUS_COLORS))
        for i, (status, color) in enumerate(STATUS_COLORS.items()):
            legend_cols[i].markdown(
                f'<div style="background-color: {color}; padding: 10px; '
                f'border-radius: 5px; text-align: center; margin: 5px;">'
                f'{status}</div>',
                unsafe_allow_html=True
            )

        st.markdown("### Inventory Data")
        st.dataframe(
            st.session_state.inventory_manager.style_inventory_dataframe(filtered_inventory),
            height=400,
            use_container_width=True
        )

        # Add summary statistics
        st.markdown("### Inventory Summary")
        status_counts = filtered_inventory['Status'].value_counts()
        summary_cols = st.columns(len(STATUS_COLORS))
        for i, status in enumerate(STATUS_COLORS.keys()):
            count = status_counts.get(status, 0)
            summary_cols[i].metric(
                label=status,
                value=count,
                delta=f"{count/len(filtered_inventory)*100:.1f}%" if len(filtered_inventory) > 0 else "0%"
            )
    else:
        st.info("No records found for the selected filter.")
    
    # Status update section
    if not st.session_state.inventory.empty:
        st.markdown("### Update Probe Status")
        
        col1, col2 = st.columns(2)
        
        with col1:
            search_term = st.text_input(
                "Search Probe (Serial Number or Type)",
                key="probe_search_update"
            ).strip().lower()

            filtered_probes = st.session_state.inventory[
                (st.session_state.inventory['Serial Number'].str.lower().str.contains(search_term, na=False)) |
                (st.session_state.inventory['Type'].str.lower().str.contains(search_term, na=False))
            ]

            selected_probe = st.selectbox(
                "Select Probe",
                filtered_probes['Serial Number'].tolist() if not filtered_probes.empty else ["No matches found"]
            )
            
            if selected_probe and selected_probe != "No matches found":
                probe_info = st.session_state.inventory[
                    st.session_state.inventory['Serial Number'] == selected_probe
                ].iloc[0]
                
                st.markdown("#### Probe Details")
                st.write(f"Type: {probe_info['Type']}")
                st.write(f"Current Status: {probe_info['Status']}")
                if 'Next Calibration' in probe_info:
                    st.write(f"Next Calibration: {probe_info['Next Calibration']}")
                    
                if probe_info['Type'] == "pH Probe":
                    with st.expander("View Calibration Details"):
                        display_calibration_details(probe_info)
        
        with col2:
            if selected_probe and selected_probe != "No matches found":
                current_status = probe_info['Status']
                new_status = st.selectbox(
                    "New Status",
                    ["Instock", "Calibrated", "Shipped", "Scraped"],
                    index=["Instock", "Calibrated", "Shipped", "Scraped"].index(current_status)
                )
                
                status_warning = None
                status_change_allowed = True
                
                if current_status == "Scraped" and new_status != "Scraped":
                    status_warning = "⚠️ Scraped probes cannot be restored to other statuses."
                    status_change_allowed = False
                elif current_status == "Calibrated" and new_status == "Instock":
                    status_warning = "⚠️ Calibrated probes cannot be moved back to Instock status."
                    status_change_allowed = False
                
                if status_warning:
                    st.warning(status_warning)
                
                st.markdown(
                    f'<div style="background-color: {STATUS_COLORS[new_status]}; '
                    f'padding: 10px; border-radius: 5px; margin-top: 10px;">'
                    f'Selected status: {new_status}</div>',
                    unsafe_allow_html=True
                )
                
                if st.button("Update Status") and status_change_allowed:
                    if new_status != current_status:
                        success = st.session_state.inventory_manager.update_probe_status(selected_probe, new_status)
                        if success:
                            st.success(f"✅ Updated status of {selected_probe} to {new_status}")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Failed to update status. Please try again.")
                    else:
                        st.info("ℹ️ No status change selected")

    # Download section
    st.markdown("### Download Inventory")
    col1, col2 = st.columns(2)
    
    with col1:
        # Download filtered inventory
        csv = filtered_inventory.to_csv(index=False).encode("utf-8")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        st.download_button(
            label="Download Filtered Inventory",
            data=csv,
            file_name=f"inventory_filtered_{timestamp}.csv",
            mime="text/csv",
        )
    
    with col2:
        # Download full inventory
        full_csv = st.session_state.inventory.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Full Inventory",
            data=full_csv,
            file_name=f"inventory_full_{timestamp}.csv",
            mime="text/csv",
        )

    # Debug information
    with st.expander("Debug Info", expanded=False):
        st.write({
            "Total Records": len(st.session_state.inventory),
            "Filtered Records": len(filtered_inventory),
            "Last Save": st.session_state.get('last_save_time', 'Never'),
            "Sheets Status": '✅ Connected' if st.session_state.inventory_manager.verify_connection() else '❌ Disconnected',
            "Status Distribution": dict(st.session_state.inventory['Status'].value_counts())
        })

if __name__ == "__main__":
    inventory_review_page()
