#!/usr/bin/env python3
"""
Futbin Player Market Crawler - Working Version
Successfully extracts player market data from Futbin.com
"""

import json
import re
import time
from typing import Dict, Optional
import logging

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FutbinCrawler:
    """
    Working Futbin player market data crawler
    """
    
    def __init__(self, headless: bool = False, timeout: int = 15):
        """
        Initialize the crawler
        
        Args:
            headless: Run browser in headless mode
            timeout: Maximum wait time for page elements (seconds)
        """
        self.headless = headless
        self.timeout = timeout
        self.driver = None
    
    def _setup_driver(self):
        """Setup Chrome driver with undetected-chromedriver"""
        if self.driver:
            return
        
        try:
            options = uc.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            
            if self.headless:
                options.add_argument("--headless=new")
            
            logger.info("Initializing Chrome driver...")
            self.driver = uc.Chrome(options=options)
            logger.info("Chrome driver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup Chrome driver: {e}")
            raise
    
    def _parse_price(self, text: str) -> Optional[int]:
        """
        Parse price text to integer
        
        Args:
            text: Price text (e.g., "54,500", "54.5K", "54500")
            
        Returns:
            Price as integer or None
        """
        if not text:
            return None
        
        try:
            # Clean the text
            text = str(text).strip().upper()
            
            # Remove currency symbols and coin image references
            text = re.sub(r'[£$€¥₹]', '', text)
            text = re.sub(r'\<img.*?\>', '', text)  # Remove HTML img tags
            
            # Handle K and M suffixes
            multiplier = 1
            if 'M' in text:
                multiplier = 1000000
                text = text.replace('M', '')
            elif 'K' in text:
                multiplier = 1000
                text = text.replace('K', '')
            
            # Remove all non-numeric except decimal point
            text = re.sub(r'[^\d.]', '', text)
            
            if text:
                # Convert to float first, then to int
                value = float(text) * multiplier
                return int(value)
                
        except (ValueError, AttributeError) as e:
            logger.debug(f"Could not parse price from '{text}': {e}")
        
        return None
    
    def _clean_text(self, value: Optional[str]) -> Optional[str]:
        """Utility method to normalize whitespace in extracted text"""
        if not value:
            return None
        cleaned = re.sub(r"\s+", " ", value).strip()
        return cleaned or None

    def _format_card_text(self, value: Optional[str]) -> Optional[str]:
        """Format card related values like rarity/type into readable text"""
        if not value:
            return None

        special_tokens = {"TOTW", "TOTS", "TOTY", "UCL", "OTW", "ICON", "HERO", "WC"}
        cleaned = re.sub(r"[_-]+", " ", value).strip()
        if not cleaned:
            return None

        formatted_tokens = []
        for token in cleaned.split():
            upper_token = token.upper()
            if upper_token in special_tokens:
                formatted_tokens.append(upper_token)
            else:
                formatted_tokens.append(token.capitalize())

        return " ".join(formatted_tokens)

    def _extract_player_metadata(self, soup: BeautifulSoup, page_source: str) -> Dict[str, Optional[str]]:
        """Extract player metadata such as name, card type and rarity"""

        metadata = {
            'player_name': None,
            'card_type': None,
            'card_rarity': None,
            'overall_rating': None,
            'position': None
        }

        def update(field: str, value: Optional[str]):
            if value and not metadata.get(field):
                metadata[field] = value

        # Attempt to extract player name from meta tags
        title_meta = soup.find('meta', property='og:title') or soup.find('meta', attrs={'name': 'title'})
        if title_meta and title_meta.get('content'):
            title_content = title_meta['content'].split('|')[0]
            update('player_name', self._clean_text(title_content))

        # Fallback to header elements on the page
        if not metadata['player_name']:
            name_elem = soup.select_one('.player-name, .pcdisplay-name, h1')
            if name_elem:
                update('player_name', self._clean_text(name_elem.get_text()))

        # Meta description often contains card type information
        description_meta = soup.find('meta', property='og:description') or soup.find('meta', attrs={'name': 'description'})
        description_text = description_meta.get('content') if description_meta else None

        if description_text:
            cleaned_description = self._clean_text(description_text)
            if cleaned_description:
                # Attempt to extract card related keywords from the description
                card_match = re.search(r'(Gold|Silver|Bronze|Icon|Hero|Promo|Rare|Common|Special)[^.,;]*', cleaned_description, re.IGNORECASE)
                if card_match:
                    update('card_type', self._format_card_text(card_match.group(0)))

                if not metadata['player_name']:
                    name_match = re.match(r'([^,\-]+)', cleaned_description)
                    if name_match:
                        update('player_name', self._clean_text(name_match.group(1)))

        # Search the raw page source for JSON data that contains card metadata
        json_fields = {
            'card_type': ['cardtype', 'cardType', 'version'],
            'card_rarity': ['rarity'],
            'overall_rating': ['rating'],
            'position': ['position']
        }

        for field, keys in json_fields.items():
            for key in keys:
                match = re.search(rf'"{key}"\s*:\s*"?([^"\n\r]+?)"?[,}}]', page_source, re.IGNORECASE)
                if match:
                    value = match.group(1)
                    if field in {'card_type', 'card_rarity'}:
                        value = self._format_card_text(value)
                    elif field == 'overall_rating':
                        value = re.sub(r'[^0-9]', '', value)
                    update(field, self._clean_text(value))
                    break

        return metadata

    def extract(self, url: str) -> Dict[str, any]:
        """
        Extract player market data from Futbin URL
        
        Args:
            url: Futbin player market URL
            
        Returns:
            Dictionary with success status and extracted data
        """
        if 'futbin.com' not in url:
            return {
                'success': False,
                'error': 'Invalid URL - must be a futbin.com URL',
                'data': None
            }
        
        self._setup_driver()
        
        try:
            logger.info(f"Loading URL: {url}")
            self.driver.get(url)
            
            # Wait for page body and dynamic market grid content to load
            wait = WebDriverWait(self.driver, self.timeout)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            try:
                wait.until(lambda driver: driver.find_elements(By.CSS_SELECTOR, 'div.market-grid-container'))
            except TimeoutException:
                logger.warning("Market grid did not load within timeout, continuing with available content")

            # Get page source and parse with BeautifulSoup
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            # Initialize data dictionary
            data = {
                'cheapest_sale': None,
                'actual_price': None,  # Average BIN
                'average_price': None,  # EA Avg. Price
                'player_name': None,
                'card_type': None,
                'card_rarity': None,
                'overall_rating': None,
                'position': None
            }
            
            # Find Cheapest Sale
            cheapest_container = soup.find('div', class_='market-grid-cheapest-sale')
            if cheapest_container:
                # Look for the price within the container
                price_elem = cheapest_container.find('div', class_='standard-font')
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    data['cheapest_sale'] = self._parse_price(price_text)
                    logger.info(f"Found Cheapest Sale: {data['cheapest_sale']}")
            
            # Find Average BIN
            avg_bin_container = soup.find('div', class_='market-grid-average-bin')
            if avg_bin_container:
                # Look for the price within the container
                price_elem = avg_bin_container.find('div', class_='standard-font')
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    data['actual_price'] = self._parse_price(price_text)
                    logger.info(f"Found Average BIN: {data['actual_price']}")
            
            # Find EA Avg. Price
            ea_avg_container = soup.find('div', class_='market-grid-ea-avg')
            if ea_avg_container:
                # Look for the price within the container
                price_elem = ea_avg_container.find('div', class_='standard-font')
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    data['average_price'] = self._parse_price(price_text)
                    logger.info(f"Found EA Avg. Price: {data['average_price']}")
            
            # Alternative method: Search by text labels
            if not all(data.values()):
                logger.info("Trying alternative extraction method...")
                
                # Find all divs with market grid container titles
                title_divs = soup.find_all('div', class_='market-grid-container-title')
                
                for title_div in title_divs:
                    title_text = title_div.get_text(strip=True)
                    parent = title_div.find_parent('div', class_=re.compile('market-grid-'))
                    
                    if parent:
                        # Find the price div within the parent
                        price_div = parent.find('div', class_='standard-font')
                        if price_div:
                            price_text = price_div.get_text(strip=True)
                            
                            if 'Cheapest Sale' in title_text and not data['cheapest_sale']:
                                data['cheapest_sale'] = self._parse_price(price_text)
                                logger.info(f"Found Cheapest Sale (alt): {data['cheapest_sale']}")
                            elif 'Average BIN' in title_text and not data['actual_price']:
                                data['actual_price'] = self._parse_price(price_text)
                                logger.info(f"Found Average BIN (alt): {data['actual_price']}")
                            elif 'EA Avg' in title_text and not data['average_price']:
                                data['average_price'] = self._parse_price(price_text)
                                logger.info(f"Found EA Avg. Price (alt): {data['average_price']}")
            
            # Extract metadata such as player name and card type
            metadata = self._extract_player_metadata(soup, page_source)
            for key, value in metadata.items():
                if value:
                    data[key] = value

            # Check if we got any price data (metadata alone does not count as success)
            success = any(data[key] for key in ('cheapest_sale', 'actual_price', 'average_price'))

            result = {
                'success': success,
                'url': url,
                'data': data
            }
            
            if not success:
                logger.warning("Could not extract any price data")
                result['error'] = "Failed to extract price data - page structure may have changed"
            
            return result
            
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'url': url,
                'data': {
                    'cheapest_sale': None,
                    'actual_price': None,
                    'average_price': None,
                    'player_name': None,
                    'card_type': None,
                    'card_rarity': None,
                    'overall_rating': None,
                    'position': None
                }
            }
    
    def close(self):
        """Close the browser driver"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser closed")
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
            finally:
                self.driver = None
    
    def __enter__(self):
        """Context manager support"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self.close()


def main():
    """Main function with example usage"""
    
    # Example URL
    url = "https://www.futbin.com/26/player/257/melchie-dumornay/market"
    
    print("\n" + "="*70)
    print("FUTBIN PLAYER MARKET CRAWLER - WORKING VERSION")
    print("="*70 + "\n")
    
    # Use context manager for automatic cleanup
    with FutbinCrawler(headless=False) as crawler:
        
        # Extract data from single URL
        print(f"Extracting data from: {url}\n")
        result = crawler.extract(url)
        
        # Display results
        print("\n" + "-"*70)
        print("EXTRACTION RESULTS")
        print("-"*70)
        
        if result['success']:
            print("✅ Extraction successful!\n")
            
            data = result['data']
            
            # Format prices for display
            def format_price(price):
                if price is None:
                    return "Not found"
                return f"{price:,} coins"
            
            print(f"💰 Cheapest Sale:  {format_price(data['cheapest_sale'])}")
            print(f"📈 Average BIN:    {format_price(data['actual_price'])}")
            print(f"📊 EA Avg. Price:  {format_price(data['average_price'])}")
            
            # Save to JSON
            with open('player_market_data.json', 'w') as f:
                json.dump(result, f, indent=2)
            print("\n💾 Data saved to player_market_data.json")
            
        else:
            print("❌ Extraction failed!")
            print(f"Error: {result.get('error', 'Unknown error')}")
        
        print("\n" + "="*70)
        print("Full JSON output:")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
