#!/usr/bin/env python3
"""
Google Sheets Connector V2 for Futbin Crawler
Reads player configuration from Google Sheets "Players" tab
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


class GoogleSheetsConnectorV2:
    """
    Enhanced Google Sheets Connector that reads players from Google Sheets
    """
    
    def __init__(self, 
                 credentials_file: str = "credentials.json",
                 spreadsheet_id: str = None,
                 players_sheet: str = "Players",
                 data_sheet: str = "Sheet1"):
        """
        Initialize Google Sheets connector V2
        
        Args:
            credentials_file: Path to Google service account credentials JSON
            spreadsheet_id: Google Sheets ID (from URL)
            players_sheet: Name of the sheet containing player configurations
            data_sheet: Name of the sheet to write price data to
        """
        self.credentials_file = credentials_file
        self.spreadsheet_id = spreadsheet_id
        self.players_sheet = players_sheet
        self.data_sheet = data_sheet
        self.service = None
        self.crawler = None
        self.running = False
        self.players = []
        
        # Initialize Google Sheets service
        self._initialize_sheets_service()
        
        # Setup the sheets if needed
        self._setup_sheets()
        
    def _initialize_sheets_service(self):
        """Initialize Google Sheets API service"""
        try:
            # Check if credentials file exists
            if not os.path.exists(self.credentials_file):
                logger.error(f"Credentials file {self.credentials_file} not found!")
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
    
    def _setup_sheets(self):
        """Setup both Players and Data sheets with headers if needed"""
        try:
            # Setup Players sheet
            self._setup_players_sheet()
            
            # Setup Data sheet
            self._setup_data_sheet()
            
        except Exception as e:
            logger.error(f"Error setting up sheets: {e}")
    
    def _setup_players_sheet(self):
        """Setup Players sheet with headers and sample data if empty"""
        try:
            # Check if Players sheet exists
            players_headers = ['Name', 'Url', 'Rarity', 'Enabled']
            
            # Try to read the first row
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f'{self.players_sheet}!A1:D1'
            ).execute()
            
            values = result.get('values', [])
            
            # If no headers or wrong headers, set them up
            if not values or values[0] != players_headers:
                logger.info(f"Setting up {self.players_sheet} sheet headers...")
                
                # Add headers
                body = {'values': [players_headers]}
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f'{self.players_sheet}!A1:D1',
                    valueInputOption='RAW',
                    body=body
                ).execute()
                
                # Check if we need to add sample data
                result = self.service.spreadsheets().values().get(
                    spreadsheetId=self.spreadsheet_id,
                    range=f'{self.players_sheet}!A2:D'
                ).execute()
                
                
                # Format headers (bold)
                self._format_headers(self.players_sheet)
                
                logger.info(f"✅ {self.players_sheet} sheet setup complete")
                
        except HttpError as e:
            if 'Unable to parse range' in str(e):
                # Players sheet doesn't exist, create it
                self._create_sheet(self.players_sheet)
                self._setup_players_sheet()  # Recursive call to set it up
            else:
                raise
    
    def _setup_data_sheet(self):
        """Setup data sheet with headers if needed"""
        try:
            # Define headers for price data
            data_headers = ['Timestamp', 'Player Name', 'Cheapest Sale', 
                          'Average BIN', 'EA Avg Price', 'Rarity', 'URL']
            
            # Try to read the first row
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f'{self.data_sheet}!A1:G1'
            ).execute()
            
            values = result.get('values', [])
            
            # If no headers or wrong headers, set them up
            if not values or len(values[0]) < len(data_headers):
                logger.info(f"Setting up {self.data_sheet} sheet headers...")
                
                body = {'values': [data_headers]}
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f'{self.data_sheet}!A1:G1',
                    valueInputOption='RAW',
                    body=body
                ).execute()
                
                # Format headers
                self._format_headers(self.data_sheet)
                
                logger.info(f"✅ {self.data_sheet} sheet headers added")
                
        except Exception as e:
            logger.error(f"Error setting up data sheet: {e}")
    
    def _create_sheet(self, sheet_name: str):
        """Create a new sheet in the spreadsheet"""
        try:
            request = {
                'addSheet': {
                    'properties': {
                        'title': sheet_name
                    }
                }
            }
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={'requests': [request]}
            ).execute()
            
            logger.info(f"✅ Created new sheet: {sheet_name}")
            
        except Exception as e:
            logger.error(f"Error creating sheet {sheet_name}: {e}")
    
    def _format_headers(self, sheet_name: str):
        """Format headers to be bold with gray background"""
        try:
            sheet_id = self._get_sheet_id(sheet_name)
            
            requests = [{
                'repeatCell': {
                    'range': {
                        'sheetId': sheet_id,
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
            
        except Exception as e:
            logger.warning(f"Could not format headers for {sheet_name}: {e}")
    
    def _get_sheet_id(self, sheet_name: str):
        """Get the sheet ID for the specified sheet name"""
        try:
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            for sheet in spreadsheet['sheets']:
                if sheet['properties']['title'] == sheet_name:
                    return sheet['properties']['sheetId']
            
            return 0
            
        except Exception as e:
            logger.error(f"Error getting sheet ID: {e}")
            return 0
    
    def load_players_from_sheets(self):
        """Load player configuration from the Players sheet"""
        try:
            # Read all data from Players sheet
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f'{self.players_sheet}!A2:D'  # Skip header row
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                logger.warning("No players found in Players sheet!")
                return []
            
            self.players = []
            for row in values:
                if len(row) >= 4:
                    # Check if enabled (case-insensitive)
                    enabled = str(row[3]).upper() in ['TRUE', 'YES', '1', 'ENABLED']
                    
                    if enabled:
                        player = {
                            'name': row[0],
                            'url': row[1],
                            'rarity': row[2] if len(row) > 2 else '',
                            'enabled': enabled
                        }
                        self.players.append(player)
                        logger.info(f"Loaded player: {player['name']} ({player['rarity']})")
            
            logger.info(f"✅ Loaded {len(self.players)} enabled players from Google Sheets")
            return self.players
            
        except Exception as e:
            logger.error(f"Error loading players from sheets: {e}")
            return []
    
    def extract_player_data(self) -> List[Dict]:
        """Extract data for all enabled players"""
        if not self.crawler:
            self.crawler = FutbinCrawler(headless=True)
        
        # Reload players from sheets
        self.load_players_from_sheets()
        
        results = []
        
        for player in self.players:
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
                        'rarity': player.get('rarity', ''),
                        'url': player['url']
                    })
                else:
                    logger.warning(f"Failed to extract data for {player['name']}")
                    
            except Exception as e:
                logger.error(f"Error extracting {player['name']}: {e}")
        
        return results
    
    def push_to_sheets(self, data: List[Dict]):
        """Push extracted data to the data sheet"""
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
                    item['rarity'],
                    item['url']
                ]
                rows.append(row)
            
            # Get current data to find next empty row
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f'{self.data_sheet}!A:A'
            ).execute()
            
            current_rows = len(result.get('values', []))
            next_row = current_rows + 1 if current_rows > 0 else 2  # Start from row 2 if headers exist
            
            # Append data
            body = {'values': rows}
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f'{self.data_sheet}!A{next_row}',
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            logger.info(f"✅ Pushed {len(rows)} rows to {self.data_sheet}")
            
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
                    prices = []
                    if item['cheapest_sale']:
                        prices.append(f"Cheapest: {item['cheapest_sale']:,}")
                    if item['average_bin']:
                        prices.append(f"Avg: {item['average_bin']:,}")
                    if item['ea_avg_price']:
                        prices.append(f"EA: {item['ea_avg_price']:,}")
                    
                    price_str = " | ".join(prices) if prices else "No prices"
                    print(f"  • {item['player_name']} ({item['rarity']}): {price_str}")
            else:
                logger.warning("No data extracted")
                
        except Exception as e:
            logger.error(f"Error in run_once: {e}")
    
    def run_scheduled(self, interval_seconds: int = 30):
        """Run extraction on schedule"""
        self.running = True
        
        logger.info(f"🔄 Starting scheduled extraction every {interval_seconds} seconds")
        logger.info("Players configuration will be reloaded from Google Sheets on each run")
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
    print("FUTBIN CRAWLER - GOOGLE SHEETS INTEGRATION V2")
    print("="*70)
    print("\n📋 This version reads player configuration from Google Sheets!")
    print("   Add/edit players in the 'Players' sheet of your spreadsheet")
    print("="*70)
    
    # Check if spreadsheet ID is provided
    if len(sys.argv) > 1:
        spreadsheet_id = sys.argv[1]
    else:
        # Try to read from player_links.json
        try:
            with open('player_links.json', 'r') as f:
                config = json.load(f)
                spreadsheet_id = config.get('settings', {}).get('google_spreadsheet_id')
                if spreadsheet_id == 'YOUR_SPREADSHEET_ID_HERE':
                    spreadsheet_id = None
        except:
            spreadsheet_id = None
        
        if not spreadsheet_id:
            spreadsheet_id = input("\nEnter your Google Spreadsheet ID: ").strip()
        
        if not spreadsheet_id:
            print("❌ Spreadsheet ID is required!")
            return
    
    try:
        # Initialize connector
        connector = GoogleSheetsConnectorV2(
            spreadsheet_id=spreadsheet_id,
            credentials_file="credentials.json",
            players_sheet="Players",
            data_sheet="Sheet1"
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
        print("\nPlease make sure credentials.json exists")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\n❌ Fatal error: {e}")


if __name__ == "__main__":
    main()
