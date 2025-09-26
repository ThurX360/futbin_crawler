#!/usr/bin/env python3
"""
Google Sheets Connector for Futbin Crawler
Automatically runs every 30 seconds and pushes data to Google Sheets
"""

import json
import time
import os
import sys
from datetime import datetime
from typing import List, Dict, Optional
import logging
import threading
import signal

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from futbin_crawler_working import FutbinCrawler

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GoogleSheetsConnector:
    """
    Connects Futbin Crawler to Google Sheets
    """
    
    def __init__(self, 
                 credentials_file: str = "credentials.json",
                 spreadsheet_id: str = None,
                 config_file: str = "player_links.json",
                 sheet_name: str = "Sheet1"):
        """
        Initialize Google Sheets connector
        
        Args:
            credentials_file: Path to Google service account credentials JSON
            spreadsheet_id: Google Sheets ID (from URL)
            config_file: Player configuration file
            sheet_name: Name of the sheet tab to use
        """
        self.credentials_file = credentials_file
        self.spreadsheet_id = spreadsheet_id
        self.config_file = config_file
        self.sheet_name = sheet_name
        self.service = None
        self.crawler = None
        self.running = False
        
        # Load configuration
        self._load_config()
        
        # Initialize Google Sheets service
        self._initialize_sheets_service()
        
    def _load_config(self):
        """Load player configuration"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
                self.players = self.config.get('players', [])
                self.settings = self.config.get('settings', {})
                
            # Check if spreadsheet_id is in config
            if not self.spreadsheet_id:
                self.spreadsheet_id = self.settings.get('google_spreadsheet_id')
                
            if not self.spreadsheet_id:
                raise ValueError("Spreadsheet ID not provided. Add it to player_links.json or pass as parameter")
                
            logger.info(f"Loaded {len(self.players)} players from configuration")
            
        except FileNotFoundError:
            logger.error(f"Configuration file {self.config_file} not found!")
            raise
    
    def _initialize_sheets_service(self):
        """Initialize Google Sheets API service"""
        try:
            # Check if credentials file exists
            if not os.path.exists(self.credentials_file):
                logger.error(f"""
                ❌ Google Sheets credentials not found!
                
                To set up Google Sheets integration:
                
                1. Go to Google Cloud Console: https://console.cloud.google.com/
                2. Create a new project or select existing
                3. Enable Google Sheets API
                4. Create Service Account credentials
                5. Download JSON key and save as '{self.credentials_file}'
                6. Share your Google Sheet with the service account email
                """)
                raise FileNotFoundError(f"Credentials file {self.credentials_file} not found")
            
            # Set up credentials
            creds = service_account.Credentials.from_service_account_file(
                self.credentials_file,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            
            # Build the service
            self.service = build('sheets', 'v4', credentials=creds)
            logger.info("✅ Google Sheets API initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets API: {e}")
            raise
    
    def _setup_spreadsheet(self):
        """Setup spreadsheet with headers if needed"""
        try:
            # Define headers
            headers = [
                'Timestamp', 'Player Name', 'Cheapest Sale', 
                'Average BIN', 'EA Avg Price', 'Notes', 'URL'
            ]
            
            # Try to read the first row
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f'{self.sheet_name}!A1:G1'
            ).execute()
            
            values = result.get('values', [])
            
            # If no headers, add them
            if not values or values[0] != headers:
                logger.info("Setting up spreadsheet headers...")
                
                body = {'values': [headers]}
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f'{self.sheet_name}!A1:G1',
                    valueInputOption='RAW',
                    body=body
                ).execute()
                
                # Format headers (bold)
                requests = [{
                    'repeatCell': {
                        'range': {
                            'sheetId': self._get_sheet_id(),
                            'startRowIndex': 0,
                            'endRowIndex': 1
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'textFormat': {'bold': True},
                                'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
                            }
                        },
                        'fields': 'userEnteredFormat(textFormat,backgroundColor)'
                    }
                }]
                
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body={'requests': requests}
                ).execute()
                
                logger.info("✅ Headers added to spreadsheet")
                
        except Exception as e:
            logger.error(f"Error setting up spreadsheet: {e}")
    
    def _get_sheet_id(self):
        """Get the sheet ID for the specified sheet name"""
        try:
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            for sheet in spreadsheet['sheets']:
                if sheet['properties']['title'] == self.sheet_name:
                    return sheet['properties']['sheetId']
            
            # If sheet doesn't exist, create it
            request = {
                'addSheet': {
                    'properties': {
                        'title': self.sheet_name
                    }
                }
            }
            
            response = self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={'requests': [request]}
            ).execute()
            
            return response['replies'][0]['addSheet']['properties']['sheetId']
            
        except Exception as e:
            logger.error(f"Error getting sheet ID: {e}")
            return 0
    
    def extract_player_data(self) -> List[Dict]:
        """Extract data for all enabled players"""
        if not self.crawler:
            self.crawler = FutbinCrawler(headless=True)
        
        results = []
        enabled_players = [p for p in self.players if p.get('enabled', True)]
        
        for player in enabled_players:
            try:
                logger.info(f"Extracting: {player['name']}")
                result = self.crawler.extract(player['url'])
                
                if result['success']:
                    data = result['data']
                    results.append({
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'player_name': player['name'],
                        'cheapest_sale': data.get('cheapest_sale', ''),
                        'average_bin': data.get('actual_price', ''),
                        'ea_avg_price': data.get('average_price', ''),
                        'notes': player.get('notes', ''),
                        'url': player['url']
                    })
                else:
                    logger.warning(f"Failed to extract data for {player['name']}")
                    
            except Exception as e:
                logger.error(f"Error extracting {player['name']}: {e}")
        
        return results
    
    def push_to_sheets(self, data: List[Dict]):
        """Push extracted data to Google Sheets"""
        if not data:
            logger.warning("No data to push to sheets")
            return
        
        try:
            # Convert data to rows
            rows = []
            for item in data:
                row = [
                    item['timestamp'],
                    item['player_name'],
                    str(item['cheapest_sale']) if item['cheapest_sale'] else '',
                    str(item['average_bin']) if item['average_bin'] else '',
                    str(item['ea_avg_price']) if item['ea_avg_price'] else '',
                    item['notes'],
                    item['url']
                ]
                rows.append(row)
            
            # Get current data to find next empty row
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f'{self.sheet_name}!A:A'
            ).execute()
            
            current_rows = len(result.get('values', []))
            next_row = current_rows + 1 if current_rows > 0 else 2  # Start from row 2 if headers exist
            
            # Append data
            body = {'values': rows}
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f'{self.sheet_name}!A{next_row}',
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            logger.info(f"✅ Pushed {len(rows)} rows to Google Sheets")
            
        except HttpError as e:
            logger.error(f"Google Sheets API error: {e}")
        except Exception as e:
            logger.error(f"Error pushing to sheets: {e}")
    
    def run_once(self):
        """Run extraction and push once"""
        try:
            logger.info("Starting data extraction...")
            data = self.extract_player_data()
            
            if data:
                self.push_to_sheets(data)
                
                # Display summary
                print(f"\n📊 Extracted {len(data)} players:")
                for item in data:
                    print(f"  • {item['player_name']}: {item['cheapest_sale']} | {item['average_bin']} | {item['ea_avg_price']}")
            else:
                logger.warning("No data extracted")
                
        except Exception as e:
            logger.error(f"Error in run_once: {e}")
    
    def run_scheduled(self, interval_seconds: int = 30):
        """Run extraction on schedule"""
        self.running = True
        
        # Setup the spreadsheet on first run
        self._setup_spreadsheet()
        
        logger.info(f"🔄 Starting scheduled extraction every {interval_seconds} seconds")
        logger.info("Press Ctrl+C to stop")
        
        def run_loop():
            while self.running:
                try:
                    self.run_once()
                    logger.info(f"⏰ Next extraction in {interval_seconds} seconds...")
                    
                    # Sleep in small intervals to allow for clean shutdown
                    for _ in range(interval_seconds):
                        if not self.running:
                            break
                        time.sleep(1)
                        
                except Exception as e:
                    logger.error(f"Error in scheduled run: {e}")
                    time.sleep(interval_seconds)
        
        # Run in thread
        thread = threading.Thread(target=run_loop)
        thread.start()
        
        try:
            thread.join()
        except KeyboardInterrupt:
            logger.info("\n🛑 Stopping scheduled extraction...")
            self.stop()
    
    def stop(self):
        """Stop the scheduled extraction"""
        self.running = False
        if self.crawler:
            self.crawler.close()
            logger.info("Crawler closed")


def main():
    """Main function"""
    
    print("\n" + "="*70)
    print("FUTBIN CRAWLER - GOOGLE SHEETS INTEGRATION")
    print("="*70)
    
    # Check if spreadsheet ID is provided
    if len(sys.argv) > 1:
        spreadsheet_id = sys.argv[1]
    else:
        spreadsheet_id = input("\nEnter your Google Spreadsheet ID (from the URL): ").strip()
        
        if not spreadsheet_id:
            print("❌ Spreadsheet ID is required!")
            print("\nExample: If your sheet URL is:")
            print("https://docs.google.com/spreadsheets/d/ABC123XYZ/edit")
            print("Then the ID is: ABC123XYZ")
            return
    
    try:
        # Initialize connector
        connector = GoogleSheetsConnector(
            spreadsheet_id=spreadsheet_id,
            credentials_file="credentials.json",
            config_file="player_links.json"
        )
        
        # Handle Ctrl+C gracefully
        def signal_handler(sig, frame):
            print("\n\n🛑 Stopping crawler...")
            connector.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Run scheduled extraction
        connector.run_scheduled(interval_seconds=30)
        
    except FileNotFoundError as e:
        print(f"\n❌ {e}")
        print("\nPlease follow the setup instructions above to configure Google Sheets API")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\n❌ Fatal error: {e}")


if __name__ == "__main__":
    main()
