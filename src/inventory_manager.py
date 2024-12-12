import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import logging
import gspread
from google.oauth2 import service_account

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
            spreadsheet = self.client.open_by_key(self.sheet_id)
    
            # Try to get the worksheet, create if it doesn't exist
            try:
                self.worksheet = spreadsheet.worksheet(self.worksheet_name)
            except gspread.exceptions.WorksheetNotFound:
                # Create new worksheet
                self.worksheet = spreadsheet.add_worksheet(
                    title=self.worksheet_name,
                    rows=1000,
                    cols=20
                )
                # Initialize headers
                headers = [
                    "Serial Number", "Type", "Manufacturer", "KETOS P/N",
                    "Mfg P/N", "Next Calibration", "Status", "Entry Date",
                    "Last Modified", "Change Date", "Calibration Data"
                ]
                self.worksheet.append_row(headers)
                # Format header row
                self.worksheet.format('A1:K1', {
                    "backgroundColor": {"red": 0.0, "green": 0.443, "blue": 0.729},
                    "textFormat": {"foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "bold": True}
                })
    
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
            st.session_state.inventory = pd.DataFrame(columns=[
                "Serial Number", "Type", "Manufacturer", "KETOS P/N",
                "Mfg P/N", "Next Calibration", "Status", "Entry Date",
                "Last Modified", "Change Date", "Calibration Data"
            ])

    def get_filtered_inventory(self, status_filter="All"):
        """Get filtered inventory based on status"""
        try:
            if status_filter == "All":
                return st.session_state.inventory
            return st.session_state.inventory[st.session_state.inventory['Status'] == status_filter]
        except Exception as e:
            logger.error(f"Error filtering inventory: {str(e)}")
            return pd.DataFrame()

    def style_inventory_dataframe(self, df):
        """Apply color styling to inventory dataframe based on status"""
        try:
            def color_status(val):
                return f'background-color: {STATUS_COLORS.get(val, "white")}'
            return df.style.applymap(color_status, subset=['Status'])
        except Exception as e:
            logger.error(f"Error styling dataframe: {str(e)}")
            return df

    def save_inventory(self, inventory_df):
        """Save inventory to Google Sheets with backup"""
        try:
            # Update main worksheet
            headers = inventory_df.columns.tolist()
            data = inventory_df.values.tolist()
            
            self.worksheet.clear()
            self.worksheet.update('A1', [headers])
            if data:
                self.worksheet.update('A2', data)

            # Format header row
            self.worksheet.format('A1:Z1', {
                "backgroundColor": {"red": 0.0, "green": 0.443, "blue": 0.729},
                "textFormat": {"foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "bold": True}
            })

            # Create backup if it's backup day
            if datetime.now().day % 5 == 0:
                try:
                    backup_sheet_name = f"Backup_{datetime.now().strftime('%Y%m%d')}"
                    sheet = self.client.open_by_key(self.sheet_id)
                    backup_worksheet = sheet.add_worksheet(backup_sheet_name, 1000, 100)
                    backup_worksheet.update('A1', [headers])
                    backup_worksheet.update('A2', data)
                    logger.info(f"Created backup worksheet: {backup_sheet_name}")
                except Exception as e:
                    logger.error(f"Backup creation failed: {str(e)}")

            st.session_state['last_save_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return True
        except Exception as e:
            logger.error(f"Error saving inventory: {str(e)}")
            return False

    def update_probe_status(self, serial_number, new_status):
        """Update probe status and metadata"""
        try:
            if serial_number in st.session_state.inventory['Serial Number'].values:
                mask = st.session_state.inventory['Serial Number'] == serial_number
                st.session_state.inventory.loc[mask, 'Status'] = new_status
                st.session_state.inventory.loc[mask, 'Change Date'] = datetime.now().strftime('%Y-%m-%d')
                st.session_state.inventory.loc[mask, 'Last Modified'] = datetime.now().strftime('%Y-%m-%d')
                
                return self.save_inventory(st.session_state.inventory)
            return False
        except Exception as e:
            logger.error(f"Error updating status: {str(e)}")
            return False

    def get_next_serial_number(self, probe_type, manufacturing_date):
        """Generate sequential serial number"""
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
        """Add a new probe to the inventory"""
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
        """Verify connection to Google Sheets"""
        try:
            self.worksheet.get_all_values()
            return True
        except Exception as e:
            logger.error(f"Connection verification failed: {str(e)}")
            return False
