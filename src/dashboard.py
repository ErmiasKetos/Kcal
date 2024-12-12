# src/dashboard.py
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
from .inventory_manager import STATUS_COLORS

def render_kpi_metrics(inventory_df):
    """Render the Key Performance Indicators section."""
    total_probes = len(inventory_df)
    
    # Create metrics with consistent styling
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
            <div class="stCard">
                <h4>Total Inventory</h4>
                <h2>{:,}</h2>
            </div>
        """.format(total_probes), unsafe_allow_html=True)
        
    with col2:
        active_probes = len(inventory_df[inventory_df['Status'].isin(['Instock', 'Calibrated'])])
        percentage = (active_probes/total_probes*100) if total_probes > 0 else 0
        st.markdown(f"""
            <div class="stCard">
                <h4>Active Probes</h4>
                <h2>{active_probes:,}</h2>
                <small>{percentage:.1f}% utilization</small>
            </div>
        """, unsafe_allow_html=True)
        
    with col3:
        need_cal = len(inventory_df[inventory_df['Status'] == 'Instock'])
        percentage = (need_cal/total_probes*100) if total_probes > 0 else 0
        st.markdown(f"""
            <div class="stCard">
                <h4>Pending Calibration</h4>
                <h2>{need_cal:,}</h2>
                <small class="warning-text">{percentage:.1f}% of total</small>
            </div>
        """, unsafe_allow_html=True)
        
    with col4:
        shipped = len(inventory_df[inventory_df['Status'] == 'Shipped'])
        percentage = (shipped/total_probes*100) if total_probes > 0 else 0
        st.markdown(f"""
            <div class="stCard">
                <h4>Deployed Probes</h4>
                <h2>{shipped:,}</h2>
                <small>{percentage:.1f}% deployment rate</small>
            </div>
        """, unsafe_allow_html=True)

def render_analysis_charts(inventory_df):
    """Render the inventory analysis charts."""
    st.markdown("### 📈 Inventory Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container():
            st.markdown('<div class="stCard">', unsafe_allow_html=True)
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
                height=400,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(t=30, b=0, l=0, r=0)
            )
            st.plotly_chart(fig_status, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        with st.container():
            st.markdown('<div class="stCard">', unsafe_allow_html=True)
            type_counts = inventory_df['Type'].value_counts()
            fig_type = px.bar(
                x=type_counts.index,
                y=type_counts.values,
                title="Probe Type Distribution",
                labels={'x': 'Probe Type', 'y': 'Count'}
            )
            fig_type.update_layout(
                height=400,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(t=30, b=0, l=0, r=0)
            )
            st.plotly_chart(fig_type, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

def render_calibration_section(inventory_df):
    """Render the calibration management section."""
    st.markdown("### 📅 Calibration Management")
    
    days_filter = st.slider(
        "Show calibrations due within (days):",
        min_value=7,
        max_value=90,
        value=30,
        step=7
    )
    
    upcoming_cals = inventory_df[
        (inventory_df['Status'] == 'Calibrated') & 
        (pd.to_datetime(inventory_df['Next Calibration']) <= datetime.now() + timedelta(days=days_filter))
    ].sort_values('Next Calibration')
    
    if not upcoming_cals.empty:
        st.markdown(f"#### Upcoming Calibrations (Next {days_filter} days)")
        
        for _, row in upcoming_cals.iterrows():
            days_until = (pd.to_datetime(row['Next Calibration']) - datetime.now()).days
            urgency_color = 'var(--error-color)' if days_until <= 7 else 'var(--warning-color)' if days_until <= 14 else 'var(--success-color)'
            
            st.markdown(f"""
                <div class="stCard" style="border-left: 4px solid {urgency_color};">
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

def render_recent_activity(inventory_df):
    """Render the recent activity section."""
    st.markdown("### 📝 Recent Activity")
    recent_df = inventory_df.sort_values('Last Modified', ascending=False).head(5)
    
    if not recent_df.empty:
        for _, row in recent_df.iterrows():
            status_color = STATUS_COLORS.get(row['Status'], '#CCCCCC')
            st.markdown(f"""
                <div class="stCard" style="border-left: 4px solid {status_color};">
                    <div style="display: flex; justify-content: space-between;">
                        <div>
                            <strong>{row['Serial Number']}</strong> - {row['Type']}<br>
                            <span class="status-badge" style="background-color: {status_color}20; 
                                                            color: {status_color}">
                                {row['Status']}
                            </span>
                        </div>
                        <div style="text-align: right;">
                            <small>Modified: {row.get('Last Modified', 'N/A')}</small>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

def render_dashboard():
    """Main function to render the dashboard."""
    st.markdown("# 🎯 Probe Management Dashboard")
    st.markdown("Real-time monitoring and analytics for probe inventory and calibration")
    
    # Get inventory data from session state
    inventory_df = st.session_state.get('inventory')

    if inventory_df is None or inventory_df.empty:
        st.warning("⚠️ No inventory data available. Please check the data source connection.")
        return

    # Data Validation
    required_columns = ['Serial Number', 'Type', 'Status', 'Entry Date', 'Last Modified', 'Next Calibration']
    missing_columns = [col for col in required_columns if col not in inventory_df.columns]
    if missing_columns:
        st.error(f"❌ Critical: Missing required columns: {', '.join(missing_columns)}")
        return

    # Render each section
    render_kpi_metrics(inventory_df)
    render_analysis_charts(inventory_df)
    
    # Create two columns for calibration and activity
    col1, col2 = st.columns([2, 1])
    
    with col1:
        render_calibration_section(inventory_df)
    
    with col2:
        render_recent_activity(inventory_df)

    # Add export functionality
    st.markdown("### 📤 Export Data")
    if st.button("Download Full Report", use_container_width=True):
        csv = inventory_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"probe_inventory_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
