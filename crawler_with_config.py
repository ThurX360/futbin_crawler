#!/usr/bin/env python3
"""
Futbin Crawler with JSON Configuration
Reads player links from player_links.json and extracts market data
"""

import json
import time
import csv
import os
from datetime import datetime
from typing import List, Dict, Optional
import logging

from futbin_crawler_working import FutbinCrawler

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ConfiguredFutbinCrawler:
    """
    Futbin crawler that uses JSON configuration file
    """
    
    def __init__(self, config_file: str = "player_links.json"):
        """
        Initialize crawler with configuration file
        
        Args:
            config_file: Path to JSON configuration file
        """
        self.config_file = config_file
        self.config = self._load_config()
        self.settings = self.config.get('settings', {})
        self.players = self.config.get('players', [])
        
        # Initialize the crawler
        headless = self.settings.get('headless_mode', False)
        self.crawler = FutbinCrawler(headless=headless)
        
        logger.info(f"Loaded configuration from {config_file}")
        logger.info(f"Found {len(self.players)} players, {sum(1 for p in self.players if p.get('enabled', True))} enabled")
    
    def _load_config(self) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file {self.config_file} not found!")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON configuration: {e}")
            raise
    
    def reload_config(self):
        """Reload configuration from file"""
        self.config = self._load_config()
        self.settings = self.config.get('settings', {})
        self.players = self.config.get('players', [])
        logger.info("Configuration reloaded")
    
    def get_enabled_players(self) -> List[Dict]:
        """Get list of enabled players from configuration"""
        return [p for p in self.players if p.get('enabled', True)]
    
    def extract_player_data(self, player_info: Dict) -> Dict:
        """
        Extract data for a single player
        
        Args:
            player_info: Dictionary with player information from config
            
        Returns:
            Extraction result dictionary
        """
        url = player_info['url']
        name = player_info.get('name', 'Unknown Player')
        
        logger.info(f"Extracting data for: {name}")
        
        try:
            result = self.crawler.extract(url)
            
            # Add player name and timestamp to the result
            if result['success']:
                result['data']['player_name'] = name
                result['data']['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                result['data']['notes'] = player_info.get('notes', '')
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting data for {name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'url': url,
                'data': {
                    'player_name': name,
                    'cheapest_sale': None,
                    'actual_price': None,
                    'average_price': None
                }
            }
    
    def process_all_players(self) -> List[Dict]:
        """
        Process all enabled players from configuration
        
        Returns:
            List of extraction results
        """
        enabled_players = self.get_enabled_players()
        
        if not enabled_players:
            logger.warning("No enabled players found in configuration!")
            return []
        
        results = []
        delay = self.settings.get('delay_between_requests', 3)
        
        for i, player in enumerate(enabled_players, 1):
            print(f"\n[{i}/{len(enabled_players)}] Processing {player.get('name', 'Unknown')}...")
            
            # Extract data
            result = self.extract_player_data(player)
            results.append(result)
            
            # Display result
            if result['success']:
                data = result['data']
                print(f"  ✅ Success!")
                print(f"     Cheapest: {data['cheapest_sale']:,}" if data['cheapest_sale'] else "     Cheapest: N/A")
                print(f"     Avg BIN: {data['actual_price']:,}" if data['actual_price'] else "     Avg BIN: N/A")
                print(f"     EA Avg: {data['average_price']:,}" if data['average_price'] else "     EA Avg: N/A")
            else:
                print(f"  ❌ Failed: {result.get('error', 'Unknown error')}")
            
            # Add delay between requests (except for last player)
            if i < len(enabled_players):
                logger.info(f"Waiting {delay} seconds before next request...")
                time.sleep(delay)
        
        return results
    
    def save_to_csv(self, results: List[Dict], filename: Optional[str] = None):
        """
        Save results to CSV file
        
        Args:
            results: List of extraction results
            filename: CSV filename (uses config default if not provided)
        """
        if not results:
            logger.warning("No results to save")
            return
        
        if filename is None:
            filename = self.settings.get('csv_filename', 'futbin_prices.csv')
        
        # Check if file exists
        file_exists = os.path.exists(filename)
        
        # Define CSV headers
        headers = [
            'timestamp', 'player_name', 'cheapest_sale', 
            'average_bin', 'ea_avg_price', 'notes', 'url'
        ]
        
        # Write to CSV
        with open(filename, 'a' if file_exists else 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            
            # Write header if new file
            if not file_exists:
                writer.writeheader()
            
            # Write data rows
            for result in results:
                if result['success']:
                    data = result['data']
                    row = {
                        'timestamp': data.get('timestamp', ''),
                        'player_name': data.get('player_name', ''),
                        'cheapest_sale': data.get('cheapest_sale', ''),
                        'average_bin': data.get('actual_price', ''),
                        'ea_avg_price': data.get('average_price', ''),
                        'notes': data.get('notes', ''),
                        'url': result.get('url', '')
                    }
                    writer.writerow(row)
        
        logger.info(f"✅ Results saved to {filename}")
    
    def save_to_json(self, results: List[Dict], filename: str = "extraction_results.json"):
        """
        Save results to JSON file
        
        Args:
            results: List of extraction results
            filename: JSON filename
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Results saved to {filename}")
    
    def generate_report(self, results: List[Dict]):
        """
        Generate a summary report
        
        Args:
            results: List of extraction results
        """
        print("\n" + "="*70)
        print("EXTRACTION REPORT")
        print("="*70)
        
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        print(f"\nTotal processed: {len(results)}")
        print(f"✅ Successful: {len(successful)}")
        print(f"❌ Failed: {len(failed)}")
        
        if successful:
            print("\n" + "-"*40)
            print("SUCCESSFUL EXTRACTIONS")
            print("-"*40)
            
            for result in successful:
                data = result['data']
                print(f"\n{data['player_name']}:")
                print(f"  Cheapest Sale: {data['cheapest_sale']:,}" if data['cheapest_sale'] else "  Cheapest Sale: N/A")
                print(f"  Average BIN: {data['actual_price']:,}" if data['actual_price'] else "  Average BIN: N/A")
                print(f"  EA Avg Price: {data['average_price']:,}" if data['average_price'] else "  EA Avg Price: N/A")
                if data.get('notes'):
                    print(f"  Notes: {data['notes']}")
        
        if failed:
            print("\n" + "-"*40)
            print("FAILED EXTRACTIONS")
            print("-"*40)
            
            for result in failed:
                print(f"\n{result['data'].get('player_name', 'Unknown')}:")
                print(f"  Error: {result.get('error', 'Unknown error')}")
    
    def cleanup(self):
        """Clean up resources"""
        if self.crawler:
            self.crawler.close()
            logger.info("Crawler closed")


def main():
    """Main function"""
    
    print("\n" + "="*70)
    print("FUTBIN CRAWLER - JSON CONFIGURATION")
    print("="*70)
    
    try:
        # Initialize crawler with config
        crawler = ConfiguredFutbinCrawler("player_links.json")
        
        # Process all enabled players
        results = crawler.process_all_players()
        
        # Generate report
        crawler.generate_report(results)
        
        # Save results if configured
        if crawler.settings.get('save_to_csv', True):
            crawler.save_to_csv(results)
        
        # Also save to JSON for complete data
        crawler.save_to_json(results)
        
        print("\n" + "="*70)
        print("✅ Processing complete!")
        print(f"Results saved to:")
        print(f"  - {crawler.settings.get('csv_filename', 'futbin_prices.csv')} (CSV)")
        print(f"  - extraction_results.json (JSON)")
        print("="*70)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\n❌ Fatal error: {e}")
    
    finally:
        # Clean up
        try:
            crawler.cleanup()
        except:
            pass


if __name__ == "__main__":
    main()
