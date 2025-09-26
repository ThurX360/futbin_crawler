#!/usr/bin/env python3
"""
Futbin Player Market Crawler - Final Version
Robust extraction of player market data from Futbin.com
"""

import json
import time
import re
from typing import Dict, Optional
import logging

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FutbinCrawler:
    """
    Robust Futbin player market data crawler
    """
    
    def __init__(self, headless: bool = False, timeout: int = 15):
        """
        Initialize the crawler
        
        Args:
            headless: Run browser in headless mode (may not work with some sites)
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
            options.add_argument("--start-maximized")
            
            if self.headless:
                options.add_argument("--headless=new")
                logger.warning("Headless mode may not work properly with some anti-bot protected sites")
            
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
            
            # Remove currency symbols
            text = re.sub(r'[£$€¥₹]', '', text)
            
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
    
    def _extract_prices_selenium(self) -> Dict[str, Optional[int]]:
        """
        Extract prices using Selenium's element finding
        
        Returns:
            Dictionary with extracted prices
        """
        prices = {
            'cheapest_sale': None,
            'actual_price': None,  # Average BIN
            'average_price': None   # EA Avg. Price
        }
        
        try:
            wait = WebDriverWait(self.driver, self.timeout)
            
            # Wait for page to load properly
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2)  # Additional wait for dynamic content
            
            # Method 1: Try to find by text content
            elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Cheapest Sale') or contains(text(), 'Average BIN') or contains(text(), 'EA Avg')]")
            
            for element in elements:
                try:
                    parent = element.find_element(By.XPATH, "..")
                    text = parent.text
                    
                    if 'Cheapest Sale' in text and not prices['cheapest_sale']:
                        # Extract number from the text
                        numbers = re.findall(r'[\d,]+(?:\.\d+)?[KkMm]?', text)
                        for num in numbers:
                            if 'Cheapest' not in num:  # Skip if it's part of the label
                                price = self._parse_price(num)
                                if price and price > 100:  # Basic validation
                                    prices['cheapest_sale'] = price
                                    logger.info(f"Found Cheapest Sale: {price}")
                                    break
                    
                    elif 'Average BIN' in text and not prices['actual_price']:
                        numbers = re.findall(r'[\d,]+(?:\.\d+)?[KkMm]?', text)
                        for num in numbers:
                            if 'Average' not in num and 'BIN' not in num:
                                price = self._parse_price(num)
                                if price and price > 100:
                                    prices['actual_price'] = price
                                    logger.info(f"Found Average BIN: {price}")
                                    break
                    
                    elif 'EA Avg' in text and not prices['average_price']:
                        numbers = re.findall(r'[\d,]+(?:\.\d+)?[KkMm]?', text)
                        for num in numbers:
                            if 'EA' not in num and 'Avg' not in num:
                                price = self._parse_price(num)
                                if price and price > 100:
                                    prices['average_price'] = price
                                    logger.info(f"Found EA Avg Price: {price}")
                                    break
                    
                except Exception as e:
                    logger.debug(f"Error processing element: {e}")
            
            # Method 2: Look for specific class patterns
            if not all(prices.values()):
                price_elements = self.driver.find_elements(By.CLASS_NAME, "price_big_right")
                for elem in price_elements:
                    text = elem.text.strip()
                    price = self._parse_price(text)
                    if price and not prices['cheapest_sale']:
                        prices['cheapest_sale'] = price
                        logger.info(f"Found price from class: {price}")
            
            # Method 3: Parse entire page with BeautifulSoup
            if not all(prices.values()):
                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                
                # Look for table rows or divs containing the prices
                rows = soup.find_all(['tr', 'div'], string=re.compile('Cheapest Sale|Average BIN|EA Avg', re.I))
                
                for row in rows:
                    row_text = row.get_text()
                    
                    if 'Cheapest Sale' in row_text and not prices['cheapest_sale']:
                        # Find next sibling or child with price
                        next_elem = row.find_next_sibling() or row.find_next()
                        if next_elem:
                            price = self._parse_price(next_elem.get_text())
                            if price:
                                prices['cheapest_sale'] = price
                    
                    elif 'Average BIN' in row_text and not prices['actual_price']:
                        next_elem = row.find_next_sibling() or row.find_next()
                        if next_elem:
                            price = self._parse_price(next_elem.get_text())
                            if price:
                                prices['actual_price'] = price
                    
                    elif 'EA Avg' in row_text and not prices['average_price']:
                        next_elem = row.find_next_sibling() or row.find_next()
                        if next_elem:
                            price = self._parse_price(next_elem.get_text())
                            if price:
                                prices['average_price'] = price
            
        except Exception as e:
            logger.error(f"Error during price extraction: {e}")
        
        return prices
    
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
            
            # Extract prices
            prices = self._extract_prices_selenium()
            
            # Check if we got any data
            success = any(prices.values())
            
            result = {
                'success': success,
                'url': url,
                'data': prices
            }
            
            if not success:
                logger.warning("Could not extract any price data")
                result['error'] = "Failed to extract price data - page structure may have changed"
                
                # Save page source for debugging
                with open('debug_page.html', 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                logger.info("Page source saved to debug_page.html for debugging")
            
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
                    'average_price': None
                }
            }
    
    def extract_multiple(self, urls: list) -> list:
        """
        Extract data from multiple URLs
        
        Args:
            urls: List of Futbin player market URLs
            
        Returns:
            List of extraction results
        """
        results = []
        
        for i, url in enumerate(urls, 1):
            logger.info(f"Processing URL {i}/{len(urls)}")
            result = self.extract(url)
            results.append(result)
            
            # Add delay to avoid rate limiting
            if i < len(urls):
                time.sleep(2)
        
        return results
    
    def save_to_json(self, data: dict, filename: str = "futbin_data.json"):
        """Save extracted data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Data saved to {filename}")
    
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
    print("FUTBIN PLAYER MARKET CRAWLER")
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
            crawler.save_to_json(result, "player_market_data.json")
            
        else:
            print("❌ Extraction failed!")
            print(f"Error: {result.get('error', 'Unknown error')}")
        
        print("\n" + "="*70)
        print("Full JSON output:")
        print(json.dumps(result, indent=2))
        
        # Example: Extract multiple players (uncomment to use)
        """
        urls = [
            "https://www.futbin.com/26/player/257/melchie-dumornay/market",
            # Add more player URLs here
        ]
        
        results = crawler.extract_multiple(urls)
        crawler.save_to_json(results, "multiple_players.json")
        """


if __name__ == "__main__":
    main()
