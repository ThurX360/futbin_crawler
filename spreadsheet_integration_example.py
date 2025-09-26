#!/usr/bin/env python3
"""
Futbin Crawler - Spreadsheet Integration Example
Shows how to integrate the crawler with CSV files and potentially Google Sheets
"""

import csv
import json
import time
from datetime import datetime
from typing import List, Dict
import os

from futbin_crawler_working import FutbinCrawler


class FutbinSpreadsheetIntegration:
    """
    Example class showing spreadsheet integration
    """
    
    def __init__(self, csv_file: str = "futbin_prices.csv"):
        self.csv_file = csv_file
        self.crawler = FutbinCrawler(headless=False)
    
    def extract_player_data(self, url: str) -> Dict:
        """Extract data for a single player"""
        result = self.crawler.extract(url)
        
        # Add timestamp and player name
        if result['success']:
            # Extract player name from URL
            player_name = url.split('/')[-2].replace('-', ' ').title()
            result['data']['player_name'] = player_name
            result['data']['url'] = url
            result['data']['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return result
    
    def save_to_csv(self, data_list: List[Dict]):
        """Save extracted data to CSV file"""
        if not data_list:
            print("No data to save")
            return
        
        # Define CSV headers
        headers = [
            'timestamp', 'player_name', 'cheapest_sale', 
            'average_bin', 'ea_avg_price', 'url'
        ]
        
        # Check if file exists
        file_exists = os.path.exists(self.csv_file)
        
        # Write to CSV
        with open(self.csv_file, 'a' if file_exists else 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            
            # Write header if new file
            if not file_exists:
                writer.writeheader()
            
            # Write data rows
            for item in data_list:
                if item['success']:
                    row = {
                        'timestamp': item['data']['timestamp'],
                        'player_name': item['data']['player_name'],
                        'cheapest_sale': item['data']['cheapest_sale'],
                        'average_bin': item['data']['actual_price'],
                        'ea_avg_price': item['data']['average_price'],
                        'url': item['data']['url']
                    }
                    writer.writerow(row)
        
        print(f"✅ Data saved to {self.csv_file}")
    
    def process_multiple_players(self, urls: List[str]):
        """Process multiple player URLs"""
        results = []
        
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] Processing: {url}")
            
            try:
                result = self.extract_player_data(url)
                results.append(result)
                
                if result['success']:
                    data = result['data']
                    print(f"  ✅ {data['player_name']}")
                    print(f"     Cheapest: {data['cheapest_sale']:,}" if data['cheapest_sale'] else "     Cheapest: N/A")
                    print(f"     Avg BIN: {data['actual_price']:,}" if data['actual_price'] else "     Avg BIN: N/A")
                    print(f"     EA Avg: {data['average_price']:,}" if data['average_price'] else "     EA Avg: N/A")
                else:
                    print(f"  ❌ Failed: {result.get('error', 'Unknown error')}")
            
            except Exception as e:
                print(f"  ❌ Error: {e}")
            
            # Add delay between requests to avoid rate limiting
            if i < len(urls):
                time.sleep(3)
        
        return results
    
    def generate_price_report(self):
        """Generate a summary report from the CSV file"""
        if not os.path.exists(self.csv_file):
            print(f"❌ File {self.csv_file} does not exist")
            return
        
        print("\n" + "="*70)
        print("PRICE REPORT")
        print("="*70)
        
        with open(self.csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        if not rows:
            print("No data in CSV file")
            return
        
        # Group by player
        players = {}
        for row in rows:
            name = row['player_name']
            if name not in players:
                players[name] = []
            players[name].append(row)
        
        # Display summary for each player
        for player_name, entries in players.items():
            print(f"\n{player_name}")
            print("-" * 40)
            
            # Get latest entry
            latest = entries[-1]
            print(f"Latest prices ({latest['timestamp']}):")
            print(f"  Cheapest Sale: {latest['cheapest_sale']}")
            print(f"  Average BIN: {latest['average_bin']}")
            print(f"  EA Avg Price: {latest['ea_avg_price']}")
            
            # Calculate price changes if multiple entries
            if len(entries) > 1:
                first = entries[0]
                try:
                    cheapest_change = int(latest['cheapest_sale'] or 0) - int(first['cheapest_sale'] or 0)
                    avg_change = int(latest['average_bin'] or 0) - int(first['average_bin'] or 0)
                    
                    print(f"\nPrice changes since {first['timestamp']}:")
                    print(f"  Cheapest: {'+' if cheapest_change > 0 else ''}{cheapest_change:,}")
                    print(f"  Avg BIN: {'+' if avg_change > 0 else ''}{avg_change:,}")
                except (ValueError, TypeError):
                    pass
    
    def cleanup(self):
        """Clean up resources"""
        self.crawler.close()


def example_google_sheets_integration():
    """
    Example of how to integrate with Google Sheets
    (Requires google-api-python-client and credentials)
    """
    print("""
    To integrate with Google Sheets:
    
    1. Install Google Sheets API:
       pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2
    
    2. Enable Google Sheets API in Google Cloud Console
    
    3. Create credentials and save as 'credentials.json'
    
    4. Use code like this:
    
    ```python
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    
    def update_google_sheet(spreadsheet_id, data):
        creds = Credentials.from_authorized_user_file('token.json')
        service = build('sheets', 'v4', credentials=creds)
        
        # Update values
        body = {'values': data}
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='Sheet1!A1',
            valueInputOption='RAW',
            body=body
        ).execute()
    ```
    """)


def main():
    """Main function demonstrating usage"""
    
    print("\n" + "="*70)
    print("FUTBIN CRAWLER - SPREADSHEET INTEGRATION EXAMPLE")
    print("="*70)
    
    # Example player URLs
    urls = [
        "https://www.futbin.com/26/player/257/melchie-dumornay/market",
        # Add more player URLs here as needed
        # "https://www.futbin.com/26/player/XXX/player-name/market",
    ]
    
    # Create integration instance
    integration = FutbinSpreadsheetIntegration()
    
    try:
        # Process players and save to CSV
        print("\n📊 Processing player URLs...")
        results = integration.process_multiple_players(urls)
        
        # Save to CSV
        integration.save_to_csv(results)
        
        # Generate report
        integration.generate_price_report()
        
        # Show Google Sheets integration example
        print("\n" + "="*70)
        print("GOOGLE SHEETS INTEGRATION")
        print("="*70)
        example_google_sheets_integration()
        
        # Save full results to JSON
        with open('all_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        print("\n💾 Full results saved to all_results.json")
        
    finally:
        integration.cleanup()


if __name__ == "__main__":
    main()
