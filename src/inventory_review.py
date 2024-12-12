# src/inventory_review.py

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
        need_cal = len(df[
            (df['Status'] == 'Instock') |
            (pd.to_datetime(df['Next Calibration']) <= datetime.now())
        ])
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

def render_inventory_charts(df):
    """Render inventory analysis charts."""
    col1, col2 = st.columns(2)
    
    with col1:
        # Status Distribution
        status_counts = df['Status'].value_counts()
        fig = go.Figure(data=[
            go.Pie(
                labels=status_counts.index,
                values=status_counts.values,
                hole=.4,
                marker=dict(colors=[STATUS_COLORS[status] for status in status_counts.index])
            )
        ])
        fig.update_layout(title="Status Distribution")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Probe Types
        type_counts = df['Type'].value_counts()
        fig = px.bar(
            x=type_counts.index,
            y=type_counts.values,
            labels={'x': 'Probe Type', 'y': 'Count'},
            title="Probe Types Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)

def render_advanced_filters():
    """Render advanced filtering options."""
    with st.expander("🔍 Advanced Filters", expanded=True):
        col1, col2, col3 = st.columns(3)
        
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
            
        with col3:
            date_range = st.date_input(
                "Entry Date Range",
                value=(
                    datetime.now() - timedelta(days=30),
                    datetime.now()
                )
            )
    
    return status_filter, type_filter, date_range

def render_probe_details(probe):
    """Render detailed probe information."""
    st.markdown("### Probe Details")
    
    # Basic Information
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
            **Serial Number:** {probe['Serial Number']}\n
            **Type:** {probe['Type']}\n
            **Manufacturer:** {probe['Manufacturer']}\n
            **KETOS P/N:** {probe['KETOS P/N']}
        """)
    with col2:
        st.markdown(f"""
            **Status:** {probe['Status']}\n
            **Entry Date:** {probe['Entry Date']}\n
            **Last Modified:** {probe.get('Last Modified', 'N/A')}\n
            **Next Calibration:** {probe.get('Next Calibration', 'N/A')}
        """)
    
    # Calibration History
    if 'Calibration Data' in probe and probe['Calibration Data']:
        st.markdown("#### Calibration History")
        try:
            cal_data = json.loads(probe['Calibration Data'])
            st.json(cal_data)
        except:
            st.error("Error loading calibration data")

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
    
    # Analysis Charts
    render_inventory_charts(df)
    
    # Advanced Filters
    status_filter, type_filter, date_range = render_advanced_filters()
    
    # Apply filters
    filtered_df = df.copy()
    if status_filter:
        filtered_df = filtered_df[filtered_df['Status'].isin(status_filter)]
    if type_filter:
        filtered_df = filtered_df[filtered_df['Type'].isin(type_filter)]
    if len(date_range) == 2:
        filtered_df = filtered_df[
            (pd.to_datetime(filtered_df['Entry Date']) >= pd.to_datetime(date_range[0])) &
            (pd.to_datetime(filtered_df['Entry Date']) <= pd.to_datetime(date_range[1]))
        ]

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
        "Status": st.column_config.SelectboxColumn(
            "Status",
            help="Current status of the probe",
            width="small",
            options=["Instock", "Calibrated", "Shipped", "Scraped"]
        ),
        "Entry Date": st.column_config.DateColumn(
            "Entry Date",
            help="Date when the probe was added to inventory",
            format="MM/DD/YYYY",
            width="small"
        ),
        "Next Calibration": st.column_config.DateColumn(
            "Next Calibration",
            help="Date when next calibration is due",
            format="MM/DD/YYYY",
            width="small"
        )
    }

    edited_df = st.data_editor(
        filtered_df,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed"
    )

    # Check for changes and save
    if not edited_df.equals(filtered_df):
        if st.button("Save Changes"):
            st.session_state.inventory.update(edited_df)
            if st.session_state.inventory_manager.save_inventory(st.session_state.inventory):
                st.success("✅ Changes saved successfully!")
                st.rerun()
            else:
                st.error("Failed to save changes")

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
