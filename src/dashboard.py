

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
from .inventory_manager import STATUS_COLORS

def render_dashboard():
    """Render the main dashboard with inventory statistics."""
    st.title("🎯 Probe Management Dashboard")
    
    # Initialize inventory manager if needed
    if 'inventory_manager' not in st.session_state:
        from .inventory_manager import InventoryManager
        st.session_state.inventory_manager = InventoryManager()
        st.session_state.inventory_manager.initialize_inventory()

    # Get inventory data
    inventory_df = st.session_state.inventory

    if inventory_df is None or inventory_df.empty:
        st.warning("No inventory data available.")
        return

    # Ensure required columns exist
    required_columns = ['Serial Number', 'Type', 'Status', 'Entry Date']
    missing_columns = [col for col in required_columns if col not in inventory_df.columns]
    if missing_columns:
        st.error(f"Missing required columns: {', '.join(missing_columns)}")
        return

    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_probes = len(inventory_df)
        st.metric("Total Probes", total_probes)
        
    with col2:
        active_probes = len(
            inventory_df[inventory_df['Status'].isin(['Instock', 'Calibrated'])]
            if 'Status' in inventory_df.columns else pd.DataFrame()
        )
        st.metric(
            "Active Probes",
            active_probes,
            f"{(active_probes/total_probes*100):.1f}% of total" if total_probes > 0 else "0%"
        )
        
    with col3:
        need_cal = len(
            inventory_df[inventory_df['Status'] == 'Instock']
            if 'Status' in inventory_df.columns else pd.DataFrame()
        )
        st.metric(
            "Need Calibration",
            need_cal,
            delta_color="inverse",
            help="Probes that need calibration"
        )
        
    with col4:
        shipped = len(
            inventory_df[inventory_df['Status'] == 'Shipped']
            if 'Status' in inventory_df.columns else pd.DataFrame()
        )
        st.metric(
            "Shipped Probes",
            shipped,
            f"{(shipped/total_probes*100):.1f}% of total" if total_probes > 0 else "0%"
        )

    # Status Distribution Chart
    try:
        if 'Status' in inventory_df.columns:
            status_counts = inventory_df['Status'].value_counts()
            
            fig = go.Figure(data=[
                go.Pie(
                    labels=status_counts.index,
                    values=status_counts.values,
                    hole=.4,
                    marker=dict(colors=[STATUS_COLORS.get(status, '#CCCCCC') for status in status_counts.index])
                )
            ])
            
            fig.update_layout(
                title="Probe Status Distribution",
                showlegend=True,
                width=400,
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error creating status distribution chart: {str(e)}")

    # Recent Activity
    st.subheader("Recent Activity")
    try:
        recent_df = inventory_df.sort_values('Last Modified', ascending=False).head(5)
        
        for _, row in recent_df.iterrows():
            status_color = STATUS_COLORS.get(row['Status'], '#CCCCCC')
            st.markdown(f"""
                <div style="padding: 10px; border-left: 4px solid {status_color}; 
                           margin: 5px 0; background-color: #f8f9fa;">
                    <strong>{row['Serial Number']}</strong> - {row['Type']}<br>
                    Status: <span style="color: {status_color}">{row['Status']}</span><br>
                    Last Modified: {row.get('Last Modified', 'N/A')}
                </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error displaying recent activity: {str(e)}")

    # Upcoming Calibrations
    st.subheader("Upcoming Calibrations")
    try:
        if 'Next Calibration' in inventory_df.columns and 'Status' in inventory_df.columns:
            upcoming_df = inventory_df[
                (inventory_df['Status'] == 'Calibrated') & 
                (pd.to_datetime(inventory_df['Next Calibration']) <= datetime.now() + timedelta(days=30))
            ].sort_values('Next Calibration')
            
            if not upcoming_df.empty:
                for _, row in upcoming_df.head(5).iterrows():
                    days_until = (pd.to_datetime(row['Next Calibration']) - datetime.now()).days
                    st.markdown(f"""
                        <div style="padding: 10px; border-left: 4px solid #ffc107; 
                                   margin: 5px 0; background-color: #fff3cd;">
                            <strong>{row['Serial Number']}</strong> - {row['Type']}<br>
                            Next Calibration: {row['Next Calibration']} ({days_until} days remaining)
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No upcoming calibrations in the next 30 days")
    except Exception as e:
        st.error(f"Error displaying upcoming calibrations: {str(e)}")

if __name__ == "__main__":
    render_dashboard()
