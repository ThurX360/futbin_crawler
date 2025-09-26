#!/usr/bin/env python3
"""
Futbin Player Market Crawler - Undetected Chrome Version
Extracts player market data from Futbin.com player pages
"""

import json
import time
import re
from typing import Dict, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
import undetected_chromedriver as uc


class FutbinCrawlerUC:
    """
    A crawler for extracting player market data from Futbin.com using undetected-chromedriver
    """
    
    def __init__(self, headless: bool = False):
        """
        Initialize the crawler
        
        Args:
            headless: Whether to run browser in headless mode (may not work well with UC)
        """
        self.headless = headless
        self.driver = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def _setup_driver(self):
        """Setup undetected Chrome driver"""
        if self.driver:
            return
        
        try:
            # Create UC Chrome options
            options = uc.ChromeOptions()
            
            # Add options for better compatibility
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            
            # Note: headless mode might not work well with undetected-chromedriver
            if self.headless:
                options.add_argument("--headless=new")
            
            # Initialize undetected Chrome driver
            self.driver = uc.Chrome(options=options, version_main=None)
            
        except Exception as e:
            print(f"Failed to setup undetected Chrome driver: {e}")
            raise
    
    def _parse_price(self, price_text: str) -> Optional[int]:
        """
        Parse price text and convert to integer
        
        Args:
            price_text: Price text from the page (e.g., "54,500", "54.5K")
            
        Returns:
            Price as integer or None if parsing fails
        """
        if not price_text:
            return None
        
        try:
            # Remove any non-numeric characters except K, M, and decimal points
            price_text = price_text.strip().upper()
            
            # Handle K (thousands) and M (millions)
            multiplier = 1
            if 'M' in price_text:
                multiplier = 1000000
                price_text = price_text.replace('M', '')
            elif 'K' in price_text:
                multiplier = 1000
                price_text = price_text.replace('K', '')
            
            # Remove commas and other characters
            price_text = re.sub(r'[^\d.]', '', price_text)
            
            if price_text:
                return int(float(price_text) * multiplier)
        except Exception as e:
            print(f"Error parsing price '{price_text}': {e}")
        
        return None
    
    def extract(self, url: str) -> Dict[str, any]:
        """
        Main extraction method
        
        Args:
            url: Futbin player market URL
            
        Returns:
            Dictionary with extracted data and metadata
        """
        # Validate URL
        if 'futbin.com' not in url:
            return {
                'success': False,
                'error': 'Invalid URL. Must be a futbin.com URL',
                'data': None
            }
        
        self._setup_driver()
        
        try:
            print(f"Loading page: {url}")
            self.driver.get(url)
            
            # Wait for the page to load
            time.sleep(3)
            
            # Get page source
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'lxml')
            
            # Initialize data
            data = {
                'cheapest_sale': None,
                'actual_price': None,
                'average_price': None
            }
            
            # Method 1: Look for specific text patterns and their adjacent values
            all_text = soup.get_text()
            lines = all_text.split('\n')
            
            for i, line in enumerate(lines):
                line_clean = line.strip()
                
                # Look for Cheapest Sale
                if 'Cheapest Sale' in line_clean and i + 1 < len(lines):
                    for j in range(1, min(5, len(lines) - i)):
                        next_line = lines[i + j].strip()
                        if next_line and any(c.isdigit() for c in next_line):
                            price = self._parse_price(next_line)
                            if price and not data['cheapest_sale']:
                                data['cheapest_sale'] = price
                                print(f"Found Cheapest Sale: {price}")
                                break
                
                # Look for Average BIN
                if 'Average BIN' in line_clean and i + 1 < len(lines):
                    for j in range(1, min(5, len(lines) - i)):
                        next_line = lines[i + j].strip()
                        if next_line and any(c.isdigit() for c in next_line):
                            price = self._parse_price(next_line)
                            if price and not data['actual_price']:
                                data['actual_price'] = price
                                print(f"Found Average BIN: {price}")
                                break
                
                # Look for EA Avg Price
                if ('EA Avg' in line_clean or 'EA Average' in line_clean) and i + 1 < len(lines):
                    for j in range(1, min(5, len(lines) - i)):
                        next_line = lines[i + j].strip()
                        if next_line and any(c.isdigit() for c in next_line):
                            price = self._parse_price(next_line)
                            if price and not data['average_price']:
                                data['average_price'] = price
                                print(f"Found EA Avg Price: {price}")
                                break
            
            # Method 2: Try finding by HTML structure
            if not all([data['cheapest_sale'], data['actual_price'], data['average_price']]):
                print("Trying alternative extraction methods...")
                
                # Look for divs or spans with price-related classes
                price_elements = soup.find_all(['div', 'span', 'p'], class_=re.compile('price|value|stat', re.I))
                
                for elem in price_elements:
                    parent_text = elem.parent.get_text() if elem.parent else ""
                    elem_text = elem.get_text(strip=True)
                    
                    if 'Cheapest' in parent_text and not data['cheapest_sale']:
                        price = self._parse_price(elem_text)
                        if price:
                            data['cheapest_sale'] = price
                    
                    elif 'Average BIN' in parent_text and not data['actual_price']:
                        price = self._parse_price(elem_text)
                        if price:
                            data['actual_price'] = price
                    
                    elif 'EA' in parent_text and 'Avg' in parent_text and not data['average_price']:
                        price = self._parse_price(elem_text)
                        if price:
                            data['average_price'] = price
            
            # Prepare result
            result = {
                'success': bool(data['cheapest_sale'] or data['actual_price'] or data['average_price']),
                'url': url,
                'data': data
            }
            
            if not result['success']:
                # Save HTML for debugging
                with open('debug_page.html', 'w', encoding='utf-8') as f:
                    f.write(page_source)
                print("Page HTML saved to debug_page.html for inspection")
                result['error'] = "Could not extract price data. Page structure may have changed."
            
            return result
            
        except Exception as e:
            print(f"Error during extraction: {e}")
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
    
    def close(self):
        """Close the browser driver"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close()


def main():
    """Main function to demonstrate usage"""
    # Example URL
    url = "https://www.futbin.com/26/player/257/melchie-dumornay/market"
    
    print("="*60)
    print("FUTBIN CRAWLER - Undetected Chrome Version")
    print("="*60)
    print(f"\nExtracting data from: {url}\n")
    
    # Initialize crawler (headless=False for better compatibility)
    crawler = FutbinCrawlerUC(headless=False)
    
    try:
        # Extract data
        result = crawler.extract(url)
        
        # Print results
        print("\n" + "="*60)
        print("EXTRACTION RESULTS")
        print("="*60)
        print(json.dumps(result, indent=2))
        
        if result['success']:
            print("\n✅ Extraction successful!")
            data = result['data']
            print(f"\n💰 Cheapest Sale:  {data['cheapest_sale']:,}" if data['cheapest_sale'] else "\n💰 Cheapest Sale:  Not found")
            print(f"📈 Actual Price:   {data['actual_price']:,}" if data['actual_price'] else "📈 Actual Price:   Not found")
            print(f"📊 Average Price:  {data['average_price']:,}" if data['average_price'] else "📊 Average Price:  Not found")
        else:
            print("\n❌ Extraction failed!")
            if result.get('error'):
                print(f"Error: {result['error']}")
    
    finally:
        # Clean up
        crawler.close()
        print("\n✅ Browser closed")


if __name__ == "__main__":
    main()
