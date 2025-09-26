#!/usr/bin/env python3
"""
Futbin Player Market Crawler
Extracts player market data from Futbin.com player pages
"""

import json
import time
import re
from typing import Dict, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class FutbinCrawler:
    """
    A crawler for extracting player market data from Futbin.com
    """
    
    def __init__(self, use_selenium: bool = True, headless: bool = True):
        """
        Initialize the crawler
        
        Args:
            use_selenium: Whether to use Selenium (recommended for dynamic content)
            headless: Whether to run browser in headless mode
        """
        self.use_selenium = use_selenium
        self.headless = headless
        self.driver = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def _setup_driver(self):
        """Setup Selenium Chrome driver"""
        if self.driver:
            return
        
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(f"user-agent={self.headers['User-Agent']}")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            # Try to use webdriver-manager first
            from selenium.webdriver.chrome.service import Service as ChromeService
            from webdriver_manager.chrome import ChromeDriverManager
            from webdriver_manager.core.os_manager import ChromeType
            
            service = ChromeService(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            print(f"WebDriver Manager failed: {e}")
            print("Trying alternative setup...")
            
            # Fallback: try without service (uses PATH chromedriver)
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
            except Exception as e2:
                print(f"Chrome setup failed: {e2}")
                print("Please ensure Chrome and chromedriver are installed.")
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
    
    def _extract_with_selenium(self, url: str) -> Dict[str, any]:
        """
        Extract data using Selenium
        
        Args:
            url: Futbin player market URL
            
        Returns:
            Dictionary with extracted data
        """
        self._setup_driver()
        
        try:
            print(f"Loading page with Selenium: {url}")
            self.driver.get(url)
            
            # Wait for the market data to load
            wait = WebDriverWait(self.driver, 10)
            
            # Wait for the price elements to be present
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".price-box, .market-box, [id*='price'], [class*='price']")))
            
            # Give additional time for dynamic content to load
            time.sleep(2)
            
            # Get page source and parse with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            
            # Extract data from the parsed HTML
            data = self._extract_from_soup(soup)
            
            # If BeautifulSoup extraction didn't work well, try direct Selenium extraction
            if not all([data.get('cheapest_sale'), data.get('average_price')]):
                print("Attempting direct Selenium extraction...")
                data = self._extract_with_selenium_direct()
            
            return data
            
        except Exception as e:
            print(f"Error during Selenium extraction: {e}")
            return {
                'cheapest_sale': None,
                'actual_price': None,
                'average_price': None,
                'error': str(e)
            }
    
    def _extract_with_selenium_direct(self) -> Dict[str, any]:
        """
        Extract data directly using Selenium element finding
        
        Returns:
            Dictionary with extracted data
        """
        data = {
            'cheapest_sale': None,
            'actual_price': None,
            'average_price': None
        }
        
        try:
            # Look for Cheapest Sale
            cheapest_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Cheapest Sale')]/following-sibling::*")
            if not cheapest_elements:
                cheapest_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Cheapest Sale')]/..//*[contains(@class, 'value') or contains(@class, 'price')]")
            
            for elem in cheapest_elements[:3]:  # Check first few elements
                text = elem.text.strip()
                if text and any(char.isdigit() for char in text):
                    price = self._parse_price(text)
                    if price:
                        data['cheapest_sale'] = price
                        break
            
            # Look for Average BIN (Actual Price)
            avg_bin_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Average BIN')]/following-sibling::*")
            if not avg_bin_elements:
                avg_bin_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Average BIN')]/..//*[contains(@class, 'value') or contains(@class, 'price')]")
            
            for elem in avg_bin_elements[:3]:
                text = elem.text.strip()
                if text and any(char.isdigit() for char in text):
                    price = self._parse_price(text)
                    if price:
                        data['actual_price'] = price
                        break
            
            # Look for EA Avg. Price
            ea_price_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'EA Avg') or contains(text(), 'EA Average')]/following-sibling::*")
            if not ea_price_elements:
                ea_price_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'EA Avg') or contains(text(), 'EA Average')]/..//*[contains(@class, 'value') or contains(@class, 'price')]")
            
            for elem in ea_price_elements[:3]:
                text = elem.text.strip()
                if text and any(char.isdigit() for char in text):
                    price = self._parse_price(text)
                    if price:
                        data['average_price'] = price
                        break
            
        except Exception as e:
            print(f"Error in direct Selenium extraction: {e}")
        
        return data
    
    def _extract_from_soup(self, soup: BeautifulSoup) -> Dict[str, any]:
        """
        Extract data from BeautifulSoup parsed HTML
        
        Args:
            soup: BeautifulSoup parsed HTML
            
        Returns:
            Dictionary with extracted data
        """
        data = {
            'cheapest_sale': None,
            'actual_price': None,
            'average_price': None
        }
        
        try:
            # Try to find price boxes or divs containing the prices
            # These selectors are based on common patterns in Futbin's HTML
            
            # Method 1: Look for labeled sections
            sections = soup.find_all(['div', 'section', 'article'], class_=re.compile('price|market|stat', re.I))
            
            for section in sections:
                text = section.get_text(strip=True)
                
                # Cheapest Sale
                if 'Cheapest Sale' in text and not data['cheapest_sale']:
                    # Find the price value after the label
                    price_elem = section.find(text=re.compile(r'[\d,]+'))
                    if price_elem:
                        data['cheapest_sale'] = self._parse_price(price_elem)
                
                # Average BIN (Actual Price)
                if 'Average BIN' in text and not data['actual_price']:
                    price_elem = section.find(text=re.compile(r'[\d,]+'))
                    if price_elem:
                        data['actual_price'] = self._parse_price(price_elem)
                
                # EA Avg Price
                if ('EA Avg' in text or 'EA Average' in text) and not data['average_price']:
                    price_elem = section.find(text=re.compile(r'[\d,]+'))
                    if price_elem:
                        data['average_price'] = self._parse_price(price_elem)
            
            # Method 2: Look for specific IDs or classes
            if not data['cheapest_sale']:
                elem = soup.find(id=re.compile('cheapest', re.I)) or soup.find(class_=re.compile('cheapest', re.I))
                if elem:
                    data['cheapest_sale'] = self._parse_price(elem.get_text(strip=True))
            
            if not data['actual_price']:
                elem = soup.find(id=re.compile('average.*bin', re.I)) or soup.find(class_=re.compile('average.*bin', re.I))
                if elem:
                    data['actual_price'] = self._parse_price(elem.get_text(strip=True))
            
            if not data['average_price']:
                elem = soup.find(id=re.compile('ea.*avg', re.I)) or soup.find(class_=re.compile('ea.*avg', re.I))
                if elem:
                    data['average_price'] = self._parse_price(elem.get_text(strip=True))
            
        except Exception as e:
            print(f"Error extracting from soup: {e}")
        
        return data
    
    def _extract_with_requests(self, url: str) -> Dict[str, any]:
        """
        Extract data using requests and BeautifulSoup
        
        Args:
            url: Futbin player market URL
            
        Returns:
            Dictionary with extracted data
        """
        try:
            print(f"Fetching page with requests: {url}")
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            return self._extract_from_soup(soup)
            
        except Exception as e:
            print(f"Error during requests extraction: {e}")
            return {
                'cheapest_sale': None,
                'actual_price': None,
                'average_price': None,
                'error': str(e)
            }
    
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
        
        # Extract data
        if self.use_selenium:
            data = self._extract_with_selenium(url)
        else:
            data = self._extract_with_requests(url)
        
        # Prepare result
        result = {
            'success': bool(data.get('cheapest_sale') or data.get('actual_price') or data.get('average_price')),
            'url': url,
            'data': {
                'cheapest_sale': data.get('cheapest_sale'),
                'actual_price': data.get('actual_price'),
                'average_price': data.get('average_price')
            }
        }
        
        if data.get('error'):
            result['error'] = data['error']
        
        return result
    
    def close(self):
        """Close the Selenium driver if it's open"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close()


def main():
    """Main function to demonstrate usage"""
    # Example URL
    url = "https://www.futbin.com/26/player/257/melchie-dumornay/market"
    
    print(f"Extracting data from: {url}\n")
    
    # Initialize crawler (use_selenium=True for dynamic content)
    crawler = FutbinCrawler(use_selenium=True, headless=True)
    
    try:
        # Extract data
        result = crawler.extract(url)
        
        # Print results
        print(json.dumps(result, indent=2))
        
        if result['success']:
            print("\n✅ Extraction successful!")
            print(f"Cheapest Sale: {result['data']['cheapest_sale']}")
            print(f"Actual Price: {result['data']['actual_price']}")
            print(f"Average Price: {result['data']['average_price']}")
        else:
            print("\n❌ Extraction failed!")
            if result.get('error'):
                print(f"Error: {result['error']}")
    
    finally:
        # Clean up
        crawler.close()


if __name__ == "__main__":
    main()
