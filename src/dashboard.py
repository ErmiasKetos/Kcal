import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from .drive_manager import DriveManager
from .inventory_manager import initialize_inventory, save_inventory

# Initialize inventory in session state
initialize_inventory()

def load_data():
    """Fetch and preprocess inventory data."""
    if 'inventory' in st.session_state:
        return st.session_state.inventory
    else:
        st.warning("⚠️ No inventory data found.")
        return pd.DataFrame(columns=[
            "Serial Number", "Type", "Manufacturer", "KETOS P/N",
            "Mfg P/N", "Next Calibration", "Status", "Entry Date",
            "Last Modified", "Change Date"
        ])

def render_dashboard():
    """Render the dynamic dashboard."""
    st.title("📊 Inventory Dashboard")
    inventory = load_data()

    if inventory.empty:
        st.info("No data available. Add probes to the inventory to populate the dashboard.")
        return

    # Summary Section
    st.markdown("### Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Probes", len(inventory))
    with col2:
        calibration_due = len(inventory[inventory['Next Calibration'] <= datetime.now().strftime('%Y-%m-%d')])
        st.metric("Calibration Due", calibration_due)
    with col3:
        st.metric("Instock Probes", len(inventory[inventory['Status'] == 'Instock']))

    # Filters
    st.markdown("### Filters")
    col1, col2, col3 = st.columns(3)
    with col1:
        probe_type = st.multiselect("Probe Type", inventory['Type'].unique(), default=inventory['Type'].unique())
    with col2:
        status_filter = st.multiselect("Status", inventory['Status'].unique(), default=inventory['Status'].unique())
    with col3:
        date_filter = st.date_input("Calibration Before", datetime.now() + timedelta(days=30))

    filtered_inventory = inventory[
        (inventory['Type'].isin(probe_type)) &
        (inventory['Status'].isin(status_filter)) &
        (pd.to_datetime(inventory['Next Calibration']) <= pd.to_datetime(date_filter))
    ]

    # Charts Section
    st.markdown("### Visualizations")
    col1, col2 = st.columns(2)

    with col1:
        probe_count_chart = px.bar(
            filtered_inventory.groupby('Type')['Serial Number'].count().reset_index(),
            x='Type',
            y='Serial Number',
            title="Probes by Type",
            labels={"Serial Number": "Count", "Type": "Probe Type"}
        )
        st.plotly_chart(probe_count_chart, use_container_width=True)

    with col2:
        status_chart = px.pie(
            filtered_inventory,
            names='Status',
            title="Probes by Status",
            hole=0.4
        )
        st.plotly_chart(status_chart, use_container_width=True)

    # Table Section
    st.markdown("### Inventory Table")
    st.dataframe(filtered_inventory, use_container_width=True)

    # Action Section
    st.markdown("### Actions")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Sync with Google Drive"):
            drive_manager = st.session_state.get("drive_manager")
            folder_id = st.session_state.get("drive_folder_id")
            if drive_manager and folder_id:
                if drive_manager.save_to_drive(inventory, folder_id):
                    st.success("✅ Inventory synced successfully with Google Drive!")
                else:
                    st.error("⚠️ Failed to sync inventory with Google Drive.")
            else:
                st.warning("⚠️ Google Drive not configured.")

    with col2:
        csv = filtered_inventory.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Filtered Inventory",
            data=csv,
            file_name=f"filtered_inventory_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

# Run the dashboard
render_dashboard()
