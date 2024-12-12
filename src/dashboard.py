import streamlit as st
st.set_page_config(
    page_title="Probe Management Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
from .inventory_manager import STATUS_COLORS

def render_dashboard():
    """Render the enhanced probe management dashboard with detailed insights."""
    st.set_page_config(page_title="Probe Management Dashboard", layout="wide")
    
    # Custom CSS to improve appearance
    st.markdown("""
        <style>
        .main .block-container {padding-top: 2rem;}
        div[data-testid="stMetricValue"] {font-size: 28px;}
        div[data-testid="stMetricDelta"] {font-size: 14px;}
        </style>
    """, unsafe_allow_html=True)
    
    # Dashboard Header with Logo and Title
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image("logo.png", width=100)  # Make sure to add your logo file
    with col2:
        st.title("🎯 Probe Management Dashboard")
        st.markdown("Real-time monitoring and analytics for probe inventory and calibration")
    
    # Initialize inventory manager
    if 'inventory_manager' not in st.session_state:
        from .inventory_manager import InventoryManager
        st.session_state.inventory_manager = InventoryManager()
        st.session_state.inventory_manager.initialize_inventory()

    inventory_df = st.session_state.inventory

    if inventory_df is None or inventory_df.empty:
        st.warning("⚠️ No inventory data available. Please check the data source connection.")
        return

    # Data Validation
    required_columns = ['Serial Number', 'Type', 'Status', 'Entry Date', 'Last Modified', 'Next Calibration']
    missing_columns = [col for col in required_columns if col not in inventory_df.columns]
    if missing_columns:
        st.error(f"❌ Critical: Missing required columns: {', '.join(missing_columns)}")
        return

    # Key Metrics Section
    st.markdown("### 📊 Key Performance Indicators")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_probes = len(inventory_df)
        st.metric(
            "Total Inventory",
            f"{total_probes:,}",
            help="Total number of probes in the system"
        )
        
    with col2:
        active_probes = len(inventory_df[inventory_df['Status'].isin(['Instock', 'Calibrated'])])
        st.metric(
            "Active Probes",
            f"{active_probes:,}",
            f"{(active_probes/total_probes*100):.1f}% utilization",
            help="Probes available for immediate use"
        )
        
    with col3:
        need_cal = len(inventory_df[inventory_df['Status'] == 'Instock'])
        st.metric(
            "Pending Calibration",
            f"{need_cal:,}",
            f"{(need_cal/total_probes*100):.1f}% of total",
            delta_color="inverse",
            help="Probes requiring immediate calibration"
        )
        
    with col4:
        critical_cal = len(inventory_df[
            (inventory_df['Status'] == 'Calibrated') & 
            (pd.to_datetime(inventory_df['Next Calibration']) <= datetime.now() + timedelta(days=7))
        ])
        st.metric(
            "Critical Calibrations",
            f"{critical_cal:,}",
            "Due within 7 days",
            delta_color="inverse",
            help="Probes requiring calibration within the next week"
        )
        
    with col5:
        shipped = len(inventory_df[inventory_df['Status'] == 'Shipped'])
        st.metric(
            "Deployed Probes",
            f"{shipped:,}",
            f"{(shipped/total_probes*100):.1f}% deployment rate",
            help="Probes currently in the field"
        )

    # Interactive Analysis Section
    st.markdown("### 📈 Inventory Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
        # Status Distribution Chart
        status_counts = inventory_df['Status'].value_counts()
        fig_status = go.Figure(data=[
            go.Pie(
                labels=status_counts.index,
                values=status_counts.values,
                hole=.4,
                marker=dict(colors=[STATUS_COLORS.get(status, '#CCCCCC') for status in status_counts.index])
            )
        ])
        fig_status.update_layout(
            title="Status Distribution",
            showlegend=True,
            height=400
        )
        st.plotly_chart(fig_status, use_container_width=True)
        
    with col2:
        # Probe Type Distribution
        type_counts = inventory_df['Type'].value_counts()
        fig_type = px.bar(
            x=type_counts.index,
            y=type_counts.values,
            title="Probe Type Distribution",
            labels={'x': 'Probe Type', 'y': 'Count'}
        )
        fig_type.update_layout(height=400)
        st.plotly_chart(fig_type, use_container_width=True)

    # Calibration Timeline
    st.markdown("### 📅 Calibration Management")
    
    # Filter options
    col1, col2 = st.columns([2, 3])
    with col1:
        days_filter = st.slider(
            "Show calibrations due within (days):",
            min_value=7,
            max_value=90,
            value=30,
            step=7
        )
    
    # Upcoming Calibrations Table
    upcoming_cals = inventory_df[
        (inventory_df['Status'] == 'Calibrated') & 
        (pd.to_datetime(inventory_df['Next Calibration']) <= datetime.now() + timedelta(days=days_filter))
    ].sort_values('Next Calibration')
    
    if not upcoming_cals.empty:
        st.markdown(f"#### Upcoming Calibrations (Next {days_filter} days)")
        
        for _, row in upcoming_cals.iterrows():
            days_until = (pd.to_datetime(row['Next Calibration']) - datetime.now()).days
            urgency_color = '#ff0000' if days_until <= 7 else '#ffc107' if days_until <= 14 else '#28a745'
            
            st.markdown(f"""
                <div style="padding: 15px; border-left: 4px solid {urgency_color}; 
                           margin: 5px 0; background-color: rgba(248,249,250,0.95); border-radius: 4px;">
                    <div style="display: flex; justify-content: space-between;">
                        <div>
                            <strong>{row['Serial Number']}</strong> - {row['Type']}<br>
                            <small>Last Calibrated: {row.get('Last Modified', 'N/A')}</small>
                        </div>
                        <div style="text-align: right;">
                            <span style="color: {urgency_color}; font-weight: bold;">
                                {days_until} days remaining
                            </span><br>
                            <small>Due: {row['Next Calibration']}</small>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("✓ No calibrations due within the selected timeframe")

    # Recent Activity Log
    st.markdown("### 📝 Recent Activity")
    recent_df = inventory_df.sort_values('Last Modified', ascending=False).head(10)
    
    if not recent_df.empty:
        for _, row in recent_df.iterrows():
            status_color = STATUS_COLORS.get(row['Status'], '#CCCCCC')
            st.markdown(f"""
                <div style="padding: 12px; border-left: 4px solid {status_color}; 
                           margin: 5px 0; background-color: rgba(248,249,250,0.95); border-radius: 4px;">
                    <div style="display: flex; justify-content: space-between;">
                        <div>
                            <strong>{row['Serial Number']}</strong> - {row['Type']}<br>
                            Status: <span style="color: {status_color}">{row['Status']}</span>
                        </div>
                        <div style="text-align: right;">
                            <small>Modified: {row.get('Last Modified', 'N/A')}</small>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    # Add export functionality
    st.markdown("### 📤 Export Data")
    if st.button("Download Full Report"):
        csv = inventory_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"probe_inventory_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    render_dashboard()
