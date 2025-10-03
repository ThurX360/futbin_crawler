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
                if not result['data'].get('player_name'):
                    result['data']['player_name'] = name
                result['data']['configured_name'] = name
                result['data']['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                result['data']['notes'] = player_info.get('notes', '')
            else:
                result['data']['player_name'] = result['data'].get('player_name') or name
                result['data']['configured_name'] = name
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
                    'average_price': None,
                    'card_type': None,
                    'card_rarity': None,
                    'overall_rating': None,
                    'position': None,
                    'configured_name': name,
                    'notes': player_info.get('notes', '')
                }
            }
    
    @staticmethod
    def _format_price(value: Optional[int]) -> str:
        """Format integer price values with thousands separator"""
        if value is None:
            return "N/A"

        try:
            return f"{int(value):,}"
        except (TypeError, ValueError):
            return "N/A"

    def process_all_players(self, display_progress: bool = True) -> List[Dict]:
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
        delay = max(0, self.settings.get('delay_between_requests', 1))
        
        for i, player in enumerate(enabled_players, 1):
            if display_progress:
                print(f"\n[{i}/{len(enabled_players)}] Processing {player.get('name', 'Unknown')}...")
            
            # Extract data
            result = self.extract_player_data(player)
            results.append(result)
            
            # Display result
            if display_progress:
                if result['success']:
                    data = result['data']
                    print(f"  ✅ Success!")
                    print(f"     Player: {data.get('player_name', 'Unknown')}")
                    if data.get('card_type') or data.get('card_rarity'):
                        card_details = data.get('card_type') or data.get('card_rarity')
                        if data.get('card_rarity') and data.get('card_type') and data['card_rarity'] not in data['card_type']:
                            card_details = f"{data['card_type']} ({data['card_rarity']})"
                        print(f"     Card: {card_details}")
                    if data.get('overall_rating') or data.get('position'):
                        rating = data.get('overall_rating') or 'N/A'
                        position = data.get('position') or 'N/A'
                        print(f"     Rating/Position: {rating} / {position}")
                    print(f"     Cheapest: {self._format_price(data.get('cheapest_sale'))}")
                    print(f"     Avg BIN: {self._format_price(data.get('actual_price'))}")
                    print(f"     EA Avg: {self._format_price(data.get('average_price'))}")
                else:
                    print(f"  ❌ Failed: {result.get('error', 'Unknown error')}")

            # Add delay between requests (except for last player)
            if i < len(enabled_players) and delay:
                if display_progress:
                    logger.info(f"Waiting {delay} seconds before next request...")
                time.sleep(delay)

        return results

    def monitor_players(self) -> List[Dict]:
        """Continuously monitor enabled players and highlight buying opportunities"""

        enabled_players = self.get_enabled_players()

        if not enabled_players:
            logger.warning("No enabled players found in configuration!")
            return []

        interval = max(10, int(self.settings.get('monitoring_interval_seconds', 300)))
        drop_threshold = float(self.settings.get('price_drop_threshold', 0.1))
        profit_margin = float(self.settings.get('target_profit_margin', 0.08))

        print("\n" + "=" * 70)
        print("CONTINUOUS PRICE MONITORING")
        print("=" * 70)
        print("Press Ctrl+C to stop monitoring.")
        print(f"Tracking {len(enabled_players)} players every {interval} seconds.")
        print(f"Highlighting drops ≥ {drop_threshold * 100:.1f}% and profit margins ≥ {profit_margin * 100:.1f}%.")

        previous_prices: Dict[str, Dict[str, Optional[int]]] = {}
        iteration = 1
        last_results: List[Dict] = []

        try:
            while True:
                cycle_started = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print("\n" + "-" * 70)
                print(f"🔄 Cycle {iteration} started at {cycle_started}")

                results = self.process_all_players(display_progress=False)
                last_results = results

                failures = [r for r in results if not r['success']]

                recommendations = []

                for result in results:
                    url = result.get('url', '')
                    data = result.get('data', {}) or {}
                    name = data.get('configured_name') or data.get('player_name') or 'Unknown Player'

                    if not result['success']:
                        error_msg = result.get('error', 'Unknown error')
                        print(f"  ⚠️ {name}: Failed to refresh data ({error_msg})")
                        continue

                    cheapest = data.get('cheapest_sale')
                    avg_bin = data.get('actual_price')
                    ea_avg = data.get('average_price')
                    reference_price = next((price for price in (avg_bin, ea_avg) if price), None)

                    previous_entry = previous_prices.get(url)
                    previous_price = previous_entry.get('cheapest') if previous_entry else None

                    change_symbol = "="
                    change_text = "No change"
                    drop_pct = None

                    if cheapest and previous_price:
                        if cheapest < previous_price:
                            drop_pct = (previous_price - cheapest) / previous_price
                            change_symbol = "↓"
                            change_text = f"Down {drop_pct * 100:.1f}% ({self._format_price(previous_price)} → {self._format_price(cheapest)})"
                        elif cheapest > previous_price:
                            increase_pct = (cheapest - previous_price) / previous_price
                            change_symbol = "↑"
                            change_text = f"Up {increase_pct * 100:.1f}% ({self._format_price(previous_price)} → {self._format_price(cheapest)})"
                        else:
                            change_text = "Unchanged"

                    print(f"  {change_symbol} {name}")
                    print(f"     Cheapest: {self._format_price(cheapest)} | Avg BIN: {self._format_price(avg_bin)} | EA Avg: {self._format_price(ea_avg)}")
                    if previous_price:
                        print(f"     Trend: {change_text}")

                    margin = None
                    potential_profit = None
                    if cheapest and reference_price and reference_price > 0:
                        potential_profit = reference_price - cheapest
                        if potential_profit > 0:
                            margin = potential_profit / reference_price

                    if margin and margin >= profit_margin:
                        recommendations.append({
                            'name': name,
                            'cheapest': cheapest,
                            'reference_price': reference_price,
                            'margin': margin,
                            'drop_pct': drop_pct,
                            'url': url,
                            'reference_label': 'Avg BIN' if reference_price == avg_bin else 'EA Avg'
                        })
                    elif drop_pct and drop_pct >= drop_threshold and potential_profit and potential_profit > 0:
                        recommendations.append({
                            'name': name,
                            'cheapest': cheapest,
                            'reference_price': reference_price,
                            'margin': margin,
                            'drop_pct': drop_pct,
                            'url': url,
                            'reference_label': 'Avg BIN' if reference_price == avg_bin else 'EA Avg'
                        })

                    if cheapest:
                        previous_prices[url] = {
                            'cheapest': cheapest,
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }

                if failures:
                    print(f"\n  ⚠️ {len(failures)} player(s) failed in this cycle. See logs for details.")

                if recommendations:
                    print("\n  💡 Potential buy opportunities detected:")
                    recommendations.sort(key=lambda x: (x['margin'] or 0, x['drop_pct'] or 0), reverse=True)
                    for rec in recommendations:
                        margin_text = f"{rec['margin'] * 100:.1f}%" if rec['margin'] is not None else "N/A"
                        drop_text = f" | Drop {rec['drop_pct'] * 100:.1f}%" if rec['drop_pct'] is not None else ""
                        ref_price = self._format_price(rec['reference_price'])
                        print(f"   - {rec['name']}: {self._format_price(rec['cheapest'])} vs {rec['reference_label']} {ref_price} (Margin {margin_text}{drop_text})")
                        if rec['url']:
                            print(f"     URL: {rec['url']}")
                else:
                    print("\n  No buy signals this cycle based on configured thresholds.")

                print(f"\n✅ Cycle {iteration} complete. Next check in {interval} seconds...")
                iteration += 1

                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring stopped by user. Preparing final summary...")
        except Exception as e:
            logger.error(f"Monitoring stopped due to error: {e}")
            print(f"\n❌ Monitoring stopped due to error: {e}")

        return last_results
    
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
            'timestamp', 'player_name', 'configured_name', 'card_type', 'card_rarity',
            'overall_rating', 'position', 'cheapest_sale',
            'average_bin', 'ea_avg_price', 'notes', 'url'
        ]
        
        # Write to CSV
        with open(filename, 'w', newline='', encoding='utf-8') as f:
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
                        'configured_name': data.get('configured_name', ''),
                        'card_type': data.get('card_type', ''),
                        'card_rarity': data.get('card_rarity', ''),
                        'overall_rating': data.get('overall_rating', ''),
                        'position': data.get('position', ''),
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
                if data.get('card_type') or data.get('card_rarity'):
                    print(f"  Card: {data.get('card_type') or data.get('card_rarity')}")
                if data.get('overall_rating') or data.get('position'):
                    print(f"  Rating/Position: {data.get('overall_rating', 'N/A')} / {data.get('position', 'N/A')}")
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
                failed_name = result['data'].get('player_name') or result['data'].get('configured_name') or 'Unknown'
                print(f"\n{failed_name}:")
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
        
        if crawler.settings.get('continuous_monitoring', False):
            last_results = crawler.monitor_players()

            if last_results:
                if crawler.settings.get('save_to_csv', True):
                    crawler.save_to_csv(last_results)

                crawler.save_to_json(last_results)
                crawler.generate_report(last_results)

                print("\n" + "="*70)
                print("✅ Monitoring session ended")
                print(f"Latest snapshot saved to:")
                print(f"  - {crawler.settings.get('csv_filename', 'futbin_prices.csv')} (CSV)")
                print(f"  - extraction_results.json (JSON)")
                print("="*70)
            else:
                print("\n" + "="*70)
                print("⚠️ Monitoring session ended without successful data capture.")
                print("Check your configuration and try again.")
                print("="*70)
        else:
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
