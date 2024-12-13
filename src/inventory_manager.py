

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import logging
import gspread
from google.oauth2 import service_account
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
SHEET_ID = "1J9VE94Ja863EyPNZGOEes1EuILg0FsGC58bLwKiQlbc"
WORKSHEET_NAME = "Sheet1"

# Status color mapping
STATUS_COLORS = {
    'Instock': '#FFD700',      # Gold Yellow
    'Calibrated': '#32CD32',   # Lime Green
    'Shipped': '#4169E1',      # Royal Blue
    'Scraped': '#DC143C'       # Crimson
}

class InventoryManager:
    def __init__(self):
        """Initialize InventoryManager with Google Sheets connection."""
        self.sheet_id = SHEET_ID
        self.worksheet_name = WORKSHEET_NAME
        self.client = None
        self.worksheet = None
        self._initialize_sheets()

    def _initialize_sheets(self):
        """Initialize Google Sheets connection."""
        try:
            credentials = service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=[
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive.file",
                ]
            )
            self.client = gspread.authorize(credentials)
            self.worksheet = self.client.open_by_key(self.sheet_id).worksheet(self.worksheet_name)
            logger.info("Successfully initialized Google Sheets connection")
        except Exception as e:
            logger.error(f"Failed to initialize sheets connection: {str(e)}")
            raise

    def initialize_inventory(self):
        """Initialize or load existing inventory"""
        try:
            if 'inventory' not in st.session_state or st.session_state.inventory.empty:
                data = self.worksheet.get_all_records()
                df = pd.DataFrame(data)
                
                # Convert date columns
                date_columns = ['Entry Date', 'Last Modified', 'Next Calibration', 'Change Date']
                for col in date_columns:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col]).dt.strftime('%Y-%m-%d')
                
                st.session_state.inventory = df
                logger.info(f"Loaded inventory from Google Sheets: {len(df)} records")
        except Exception as e:
            logger.error(f"Error initializing inventory: {str(e)}")
            # Create empty inventory with required columns
            st.session_state.inventory = pd.DataFrame(columns=[
                "Serial Number", "Type", "Manufacturer", "KETOS P/N",
                "Mfg P/N", "Next Calibration", "Status", "Entry Date",
                "Last Modified", "Change Date", "Calibration Data"
            ])

    def save_inventory(self, inventory_df):
        """Save inventory to Google Sheets with safety measures."""
        try:
            if self.worksheet is None:
                st.error("❌ Cannot save: No connection to Google Sheets")
                return False
    
            # First get existing data as backup
            try:
                backup_data = self.worksheet.get_all_records()
            except Exception as e:
                logger.error(f"Failed to create backup: {str(e)}")
                backup_data = None
    
            # Prepare new data
            headers = inventory_df.columns.tolist()
            data = inventory_df.values.tolist()
    
            if not data:
                logger.error("No data to save")
                return False
    
            try:
                # Update in chunks without clearing first
                self.worksheet.update('A1', [headers])
                if data:
                    # Update in batches of 1000 rows
                    batch_size = 1000
                    for i in range(0, len(data), batch_size):
                        batch = data[i:i + batch_size]
                        self.worksheet.update(f'A{i+2}', batch)
    
                # Format header row
                self.worksheet.format('A1:Z1', {
                    "backgroundColor": {"red": 0.0, "green": 0.443, "blue": 0.729},
                    "textFormat": {"foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "bold": True}
                })
    
                # Clean up any extra rows if new data is shorter than original
                if backup_data and len(data) < len(backup_data):
                    self.worksheet.delete_rows(len(data) + 2, len(backup_data) + 1)
    
                st.session_state['last_save_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.info("Successfully saved inventory to Google Sheets")
                return True
    
            except Exception as e:
                logger.error(f"Error during save: {str(e)}")
                # Attempt to restore from backup if save failed
                if backup_data:
                    try:
                        backup_headers = list(backup_data[0].keys())
                        backup_values = [list(d.values()) for d in backup_data]
                        self.worksheet.clear()
                        self.worksheet.update('A1', [backup_headers])
                        self.worksheet.update('A2', backup_values)
                        st.error("Save failed, restored previous data")
                    except Exception as restore_error:
                        logger.error(f"Restore failed: {str(restore_error)}")
                        st.error("⚠️ Critical: Save failed and restore failed. Please contact support.")
                return False
    
        except Exception as e:
            logger.error(f"Error saving inventory: {str(e)}")
            st.error(f"Failed to save inventory: {str(e)}")
            return False

    def create_backup(self):
    """Create a backup worksheet."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"Backup_{timestamp}"
        
        # Create new worksheet for backup
        spreadsheet = self.client.open_by_key(self.sheet_id)
        backup_worksheet = spreadsheet.add_worksheet(backup_name, 1000, 100)
        
        # Copy data to backup
        data = self.worksheet.get_all_records()
        if data:
            headers = list(data[0].keys())
            values = [list(d.values()) for d in data]
            backup_worksheet.update('A1', [headers])
            backup_worksheet.update('A2', values)
        
        # Keep only last 5 backups
        all_worksheets = spreadsheet.worksheets()
        backup_sheets = [ws for ws in all_worksheets if ws.title.startswith("Backup_")]
        if len(backup_sheets) > 5:
            oldest_backup = min(backup_sheets, key=lambda x: x.title)
            spreadsheet.del_worksheet(oldest_backup)
            
        return True
    except Exception as e:
        logger.error(f"Backup failed: {str(e)}")
        return False
        
    def get_filtered_inventory(self, status_filter="All"):
        """Get filtered inventory based on status."""
        try:
            if status_filter == "All":
                return st.session_state.inventory
            return st.session_state.inventory[st.session_state.inventory['Status'] == status_filter]
        except Exception as e:
            logger.error(f"Error filtering inventory: {str(e)}")
            return pd.DataFrame()

    def update_probe_status(self, serial_number, new_status):
        """Update probe status and metadata."""
        try:
            if serial_number in st.session_state.inventory['Serial Number'].values:
                mask = st.session_state.inventory['Serial Number'] == serial_number
                st.session_state.inventory.loc[mask, 'Status'] = new_status
                st.session_state.inventory.loc[mask, 'Change Date'] = datetime.now().strftime('%Y-%m-%d')
                st.session_state.inventory.loc[mask, 'Last Modified'] = datetime.now().strftime('%Y-%m-%d')
                
                return self.save_inventory(st.session_state.inventory)
            return False
        except Exception as e:
            logger.error(f"Error updating probe status: {str(e)}")
            return False

    def get_next_serial_number(self, probe_type, manufacturing_date):
        """Generate sequential serial number."""
        try:
            existing_serials = st.session_state.inventory[
                st.session_state.inventory['Type'] == probe_type
            ]['Serial Number'].tolist()
            
            if existing_serials:
                sequence_numbers = [
                    int(serial.split('_')[-1])
                    for serial in existing_serials
                ]
                next_sequence = max(sequence_numbers) + 1
            else:
                next_sequence = 1
            
            expire_date = manufacturing_date + timedelta(days=365 * 2)  # 2-year default
            expire_yymm = expire_date.strftime("%y%m")
            return f"{probe_type.split()[0]}_{expire_yymm}_{next_sequence:05d}"
        except Exception as e:
            logger.error(f"Error generating serial number: {str(e)}")
            return None

    def add_new_probe(self, probe_data):
        """Add a new probe to the inventory."""
        try:
            probe_data['Entry Date'] = datetime.now().strftime('%Y-%m-%d')
            probe_data['Last Modified'] = datetime.now().strftime('%Y-%m-%d')
            probe_data['Change Date'] = datetime.now().strftime('%Y-%m-%d')
            probe_data['Status'] = 'Instock'
            
            new_row_df = pd.DataFrame([probe_data])
            st.session_state.inventory = pd.concat(
                [st.session_state.inventory, new_row_df],
                ignore_index=True
            )
            
            return self.save_inventory(st.session_state.inventory)
        except Exception as e:
            logger.error(f"Error adding new probe: {str(e)}")
            return False

    def verify_connection(self):
        """Verify connection to Google Sheets."""
        try:
            self.worksheet.get_all_values()
            return True
        except Exception as e:
            logger.error(f"Connection verification failed: {str(e)}")
            return False
