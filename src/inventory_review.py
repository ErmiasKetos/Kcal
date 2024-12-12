
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


def render_advanced_filters(df):
    """Enhanced advanced filtering options."""
    with st.expander("🔍 Advanced Filters", expanded=True):
        # Create three columns for filter organization
        col1, col2, col3 = st.columns(3)

        with col1:
            # Status and Type filters
            status_filter = st.multiselect(
                "Status",
                ["Instock", "Calibrated", "Shipped", "Scraped"],
                default=["Instock", "Calibrated"]
            )
            
            type_filter = st.multiselect(
                "Probe Type",
                sorted(df['Type'].unique().tolist())
            )

        with col2:
            # Manufacturer and KETOS P/N filters
            manufacturer_filter = st.multiselect(
                "Manufacturer",
                sorted(df['Manufacturer'].unique().tolist())
            )
            
            ketos_pn_filter = st.multiselect(
                "KETOS P/N",
                sorted(df['KETOS P/N'].unique().tolist())
            )

        with col3:
            # Date range filters
            start_date = st.date_input(
                "Start Date",
                value=datetime.now() - timedelta(days=30),
                help="Filter from this date"
            )
            
            end_date = st.date_input(
                "End Date",
                value=datetime.now(),
                help="Filter until this date"
            )
            
            # Calibration status filter
            cal_status = st.radio(
                "Calibration Status",
                ["All", "Needs Calibration", "Recently Calibrated", "Never Calibrated"],
                horizontal=True
            )

        # Additional filters in new row
        col1, col2 = st.columns(2)
        
        with col1:
            # Custom field filter
            filter_field = st.selectbox(
                "Additional Filter Field",
                ["None"] + [col for col in df.columns if col not in 
                          ['Status', 'Type', 'Manufacturer', 'KETOS P/N', 'Entry Date']]
            )
            
            if filter_field != "None":
                filter_value = st.text_input(f"Filter by {filter_field}")
            else:
                filter_value = None

        with col2:
            # Sort options
            sort_by = st.selectbox(
                "Sort By",
                ["None"] + list(df.columns)
            )
            
            if sort_by != "None":
                sort_order = st.radio(
                    "Sort Order",
                    ["Ascending", "Descending"],
                    horizontal=True
                )

        # Quick filter buttons
        st.markdown("### Quick Filters")
        quick_filter_cols = st.columns(4)
        with quick_filter_cols[0]:
            show_expired_cal = st.checkbox("Show Expired Calibrations")
        with quick_filter_cols[1]:
            show_recent_changes = st.checkbox("Show Recent Changes (7 days)")
        with quick_filter_cols[2]:
            show_active_only = st.checkbox("Show Active Only")
        with quick_filter_cols[3]:
            show_critical = st.checkbox("Show Critical (Needs Attention)")

    # Apply filters
    filtered_df = df.copy()

    # Basic filters
    if status_filter:
        filtered_df = filtered_df[filtered_df['Status'].isin(status_filter)]
    if type_filter:
        filtered_df = filtered_df[filtered_df['Type'].isin(type_filter)]
    if manufacturer_filter:
        filtered_df = filtered_df[filtered_df['Manufacturer'].isin(manufacturer_filter)]
    if ketos_pn_filter:
        filtered_df = filtered_df[filtered_df['KETOS P/N'].isin(ketos_pn_filter)]

    # Date range filter
    try:
        if start_date and end_date:
            filtered_df = filtered_df[
                (pd.to_datetime(filtered_df['Entry Date']) >= pd.to_datetime(start_date)) &
                (pd.to_datetime(filtered_df['Entry Date']) <= pd.to_datetime(end_date))
            ]
    except Exception as e:
        st.warning(f"Date filtering error: {str(e)}")

    # Calibration status filter
    if cal_status != "All":
        if cal_status == "Needs Calibration":
            filtered_df = filtered_df[
                (filtered_df['Status'] == 'Instock') |
                (pd.to_datetime(filtered_df['Next Calibration']) <= datetime.now())
            ]
        elif cal_status == "Recently Calibrated":
            filtered_df = filtered_df[
                (filtered_df['Status'] == 'Calibrated') &
                (pd.to_datetime(filtered_df['Last Modified']) >= datetime.now() - timedelta(days=30))
            ]
        elif cal_status == "Never Calibrated":
            filtered_df = filtered_df[filtered_df['Calibration Data'].isna()]

    # Custom field filter
    if filter_field != "None" and filter_value:
        filtered_df = filtered_df[
            filtered_df[filter_field].astype(str).str.contains(filter_value, case=False)
        ]

    # Quick filters
    if show_expired_cal:
        try:
            filtered_df = filtered_df[
                pd.to_datetime(filtered_df['Next Calibration']) <= datetime.now()
            ]
        except Exception as e:
            st.warning("Error filtering expired calibrations")
            
    if show_recent_changes:
        try:
            filtered_df = filtered_df[
                pd.to_datetime(filtered_df['Last Modified']) >= datetime.now() - timedelta(days=7)
            ]
        except Exception as e:
            st.warning("Error filtering recent changes")
            
    if show_active_only:
        filtered_df = filtered_df[filtered_df['Status'].isin(['Instock', 'Calibrated'])]
        
    if show_critical:
        try:
            critical_mask = (
                (filtered_df['Status'] == 'Instock') |
                (pd.to_datetime(filtered_df['Next Calibration']) <= datetime.now() + timedelta(days=7))
            )
            filtered_df = filtered_df[critical_mask]
        except Exception as e:
            st.warning("Error filtering critical items")

    # Sorting
    if sort_by != "None":
        filtered_df = filtered_df.sort_values(
            by=sort_by,
            ascending=(sort_order == "Ascending")
        )

    # Display filter summary
    st.markdown("### Active Filters")
    active_filters = []
    if status_filter:
        active_filters.append(f"Status: {', '.join(status_filter)}")
    if type_filter:
        active_filters.append(f"Type: {', '.join(type_filter)}")
    if manufacturer_filter:
        active_filters.append(f"Manufacturer: {', '.join(manufacturer_filter)}")
    if cal_status != "All":
        active_filters.append(f"Calibration Status: {cal_status}")
    if start_date and end_date:
        active_filters.append(f"Date Range: {start_date} to {end_date}")
    if filter_field != "None" and filter_value:
        active_filters.append(f"{filter_field}: {filter_value}")
    
    if active_filters:
        st.info(" | ".join(active_filters))
    else:
        st.info("No active filters")

    return filtered_df


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
    
    # Apply advanced filters
    filtered_df = render_advanced_filters(df)

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
