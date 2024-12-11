import streamlit as st
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from googleapiclient.errors import HttpError
import pandas as pd
import io
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INVENTORY_FILENAME = "wbpms_inventory_2024.csv"
BACKUP_FOLDER_ID = "19lHngxB_RXEpr30jpY9_fCaSpl6Z1m1i"

class DriveManager:
    def __init__(self):
        self.service = None
        self.credentials = None

    def authenticate(self, credentials):
        """Set up Google Drive service with provided credentials"""
        try:
            self.credentials = credentials
            self.service = build('drive', 'v3', credentials=credentials)
            logger.info("Drive service authenticated successfully")
            return True
        except Exception as e:
            logger.error(f"Drive authentication failed: {str(e)}")
            st.error(f"Drive authentication failed: {str(e)}")
            return False

    def verify_folder_access(self, folder_id):
        """Verify if the folder exists and is accessible"""
        try:
            if not self.service:
                logger.error("Drive service not initialized")
                return False

            folder = self.service.files().get(
                fileId=folder_id,
                fields="id, name, permissions"
            ).execute()

            logger.info(f"Successfully verified access to folder: {folder.get('name', 'Unknown')}")
            return True

        except Exception as e:
            logger.error(f"Failed to verify folder access: {str(e)}")
            return False

    def get_file_id(self, folder_id, filename):
        """Get file ID if it exists in the folder"""
        try:
            query = f"name='{filename}' and '{folder_id}' in parents and trashed=false"
            results = self.service.files().list(
                q=query,
                fields="files(id, name)"
            ).execute()
            
            files = results.get('files', [])
            return files[0]['id'] if files else None
        except Exception as e:
            logger.error(f"Error getting file ID: {str(e)}")
            return None

    def load_inventory_from_drive(self, folder_id):
        """Load inventory file from Drive"""
        try:
            if not self.service:
                logger.error("Drive service not initialized")
                return None

            file_id = self.get_file_id(folder_id, INVENTORY_FILENAME)
            if not file_id:
                logger.info("No inventory file found in Drive")
                return None

            request = self.service.files().get_media(fileId=file_id)
            content = request.execute()
            
            # Read CSV content
            df = pd.read_csv(io.StringIO(content.decode('utf-8')))
            logger.info(f"Successfully loaded inventory from Drive: {len(df)} records")
            return df

        except Exception as e:
            logger.error(f"Failed to load inventory from Drive: {str(e)}")
            return None

    def save_to_drive(self, inventory_df, folder_id):
        """Save or update inventory to Google Drive, appending new records."""
        try:
            if not self.service:
                logger.error("Drive service not initialized")
                return False

            # Load existing data
            existing_inventory = self.load_inventory_from_drive(folder_id)

            # Merge new data with existing inventory
            if existing_inventory is not None:
                inventory_df = pd.concat([existing_inventory, inventory_df]).drop_duplicates(
                    subset="Serial Number", keep="last"
                )

            # Save the merged inventory back to the drive
            temp_file = INVENTORY_FILENAME
            inventory_df.to_csv(temp_file, index=False)

            # Prepare file metadata and media
            file_metadata = {
                'name': INVENTORY_FILENAME,
                'mimeType': 'text/csv'
            }

            media = MediaFileUpload(
                temp_file,
                mimetype='text/csv',
                resumable=True
            )

            # Check if file exists
            file_id = self.get_file_id(folder_id, INVENTORY_FILENAME)

            if file_id:
                # Update existing file
                self.service.files().update(
                    fileId=file_id,
                    media_body=media,
                    fields='id'
                ).execute()
                logger.info("Updated existing inventory file in Drive")
            else:
                # Create new file
                file_metadata['parents'] = [folder_id]
                self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
                logger.info("Created new inventory file in Drive")

            # Clean up temporary file
            if os.path.exists(temp_file):
                os.remove(temp_file)

            return True

        except Exception as e:
            logger.error(f"Failed to save to Drive: {str(e)}")
            return False

    def create_backup(self, inventory_df, folder_id):
        """Create backup of inventory file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            backup_filename = f"inventory_backup_{timestamp}.csv"
            
            # Save DataFrame to temporary file
            temp_file = backup_filename
            inventory_df.to_csv(temp_file, index=False)

            # Prepare file metadata and media
            file_metadata = {
                'name': backup_filename,
                'parents': [folder_id],
                'mimeType': 'text/csv'
            }

            media = MediaFileUpload(
                temp_file,
                mimetype='text/csv',
                resumable=True
            )

            # Create backup file
            self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()

            # Clean up temporary file
            if os.path.exists(temp_file):
                os.remove(temp_file)

            logger.info(f"Created backup file: {backup_filename}")
            return True

        except Exception as e:
            logger.error(f"Failed to create backup: {str(e)}")
            return False

    def download_inventory_csv(self, folder_id, file_name="wbpms_inventory_2024.csv"):
        """Download a CSV file from Google Drive."""
        try:
            file_id = self.get_file_id(folder_id, file_name)
            if not file_id:
                raise FileNotFoundError(f"File '{file_name}' not found in folder '{folder_id}'.")

            request = self.service.files().get_media(fileId=file_id)
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            file_content.seek(0)  # Reset the stream to the beginning
            return file_content
        except HttpError as error:
            logger.error(f"An error occurred while downloading the file: {error}")
            raise error
