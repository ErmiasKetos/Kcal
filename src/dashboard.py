# src/dashboard.py

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
from .inventory_manager import InventoryManager, STATUS_COLORS

def create_status_chart(inventory_df):
    """Create a status distribution chart."""
    status_counts = inventory_df['Status'].value_counts()
    
    fig = go.Figure(data=[
        go.Pie(
            labels=status_counts.index,
            values=status_counts.values,
            hole=.4,
            marker=dict(colors=[
                STATUS_COLORS['Instock'],
                STATUS_COLORS['Calibrated'],
                STATUS_COLORS['Shipped'],
                STATUS_COLORS['Scraped']
            ])
        )
    ])
    
    fig.update_layout(
        title="Probe Status Distribution",
        showlegend=True,
        width=400,
        height=400
    )
    
    return fig

def create_probe_type_chart(inventory_df):
    """Create a probe type distribution chart."""
    type_counts = inventory_df['Type'].value_counts()
    
    fig = go.Figure(data=[
        go.Bar(
            x=type_counts.index,
            y=type_counts.values,
            marker_color='#0071ba'
        )
    ])
    
    fig.update_layout(
        title="Probe Type Distribution",
        xaxis_title="Probe Type",
        yaxis_title="Count",
        width=600,
        height=400
    )
    
    return fig

def create_timeline_chart(inventory_df):
    """Create a timeline chart of probe registrations."""
    df = inventory_df.copy()
    df['Entry Date'] = pd.to_datetime(df['Entry Date'])
    daily_counts = df.groupby('Entry Date').size().reset_index(name='count')
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily_counts['Entry Date'],
        y=daily_counts['count'],
        mode='lines+markers',
        line=dict(color='#0071ba'),
        name='Registrations'
    ))
    
    fig.update_layout(
        title="Probe Registration Timeline",
        xaxis_title="Date",
        yaxis_title="Number of Registrations",
        width=800,
        height=400
    )
    
    return fig

def render_dashboard():
    """Render the main dashboard."""
    st.title("🎯 Probe Management Dashboard")
    
    # Initialize inventory manager if needed
    if 'inventory_manager' not in st.session_state:
        st.session_state.inventory_manager = InventoryManager()
        st.session_state.inventory_manager.initialize_inventory()
    
    # Get current inventory
    inventory_df = st.session_state.inventory
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_probes = len(inventory_df)
        st.metric("Total Probes", total_probes)
        
    with col2:
        active_probes = len(inventory_df[inventory_df['Status'].isin(['Instock', 'Calibrated'])])
        st.metric("Active Probes", active_probes)
        
    with col3:
        shipped_probes = len(inventory_df[inventory_df['Status'] == 'Shipped'])
        st.metric("Shipped Probes", shipped_probes)
        
    with col4:
        scraped_probes = len(inventory_df[inventory_df['Status'] == 'Scraped'])
        st.metric("Scraped Probes", scraped_probes)
    
    # Charts
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        status_chart = create_status_chart(inventory_df)
        st.plotly_chart(status_chart, use_container_width=True)
    
    with col2:
        probe_type_chart = create_probe_type_chart(inventory_df)
        st.plotly_chart(probe_type_chart, use_container_width=True)
    
    # Timeline
    timeline_chart = create_timeline_chart(inventory_df)
    st.plotly_chart(timeline_chart, use_container_width=True)
    
    # Recent Activity
    st.subheader("Recent Activity")
    recent_df = inventory_df.sort_values('Last Modified', ascending=False).head(5)
    
    for _, row in recent_df.iterrows():
        with st.container():
            st.markdown(f"""
            <div style="padding: 10px; border-left: 4px solid #0071ba; margin: 5px 0; background-color: #f8f9fa;">
                <strong>{row['Serial Number']}</strong> - {row['Type']}<br>
                Status: <span style="color: {STATUS_COLORS[row['Status']]}">{row['Status']}</span><br>
                Last Modified: {row['Last Modified']}
            </div>
            """, unsafe_allow_html=True)
    
    # Upcoming Calibrations
    st.subheader("Upcoming Calibrations")
    if 'Next Calibration' in inventory_df.columns:
        upcoming_df = inventory_df[
            (inventory_df['Status'] == 'Calibrated') & 
            (pd.to_datetime(inventory_df['Next Calibration']) <= datetime.now() + timedelta(days=30))
        ].sort_values('Next Calibration')
        
        if not upcoming_df.empty:
            for _, row in upcoming_df.head(5).iterrows():
                days_until = (pd.to_datetime(row['Next Calibration']) - datetime.now()).days
                st.markdown(f"""
                <div style="padding: 10px; border-left: 4px solid #ffc107; margin: 5px 0; background-color: #fff3cd;">
                    <strong>{row['Serial Number']}</strong> - {row['Type']}<br>
                    Next Calibration: {row['Next Calibration']} ({days_until} days remaining)
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No upcoming calibrations in the next 30 days")

    # Connection Status
    if st.session_state.inventory_manager.verify_connection():
        st.sidebar.success("✅ Google Sheets Connected")
    else:
        st.sidebar.error("❌ Google Sheets Disconnected")

if __name__ == "__main__":
    render_dashboard()
