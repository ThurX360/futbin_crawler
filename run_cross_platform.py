#!/usr/bin/env python3
"""
Cross-Platform Runner for Futbin Crawler
Detects OS and ensures proper configuration
"""

import sys
import platform
import os
from futbin_crawler_working import FutbinCrawler


def check_platform():
    """Check and display platform information"""
    system = platform.system()
    version = platform.version()
    python_version = sys.version
    
    print("="*60)
    print("SYSTEM INFORMATION")
    print("="*60)
    print(f"Operating System: {system}")
    print(f"OS Version: {version}")
    print(f"Python Version: {python_version}")
    print(f"Architecture: {platform.machine()}")
    print("="*60)
    
    return system


def get_platform_specific_options(system):
    """Get platform-specific Chrome options"""
    
    headless = False
    
    if system == "Linux":
        # On Linux servers without display, force headless
        if not os.environ.get('DISPLAY'):
            print("📝 No display detected, running in headless mode")
            headless = True
        else:
            print("✅ Display detected, running with GUI")
    
    elif system == "Windows":
        print("✅ Windows detected, GUI mode available")
        
    elif system == "Darwin":  # macOS
        print("✅ macOS detected, GUI mode available")
    
    else:
        print(f"⚠️ Unknown system: {system}, defaulting to headless mode")
        headless = True
    
    return headless


def test_crawler():
    """Test the crawler on the current platform"""
    
    # Check platform
    system = check_platform()
    
    # Get platform-specific options
    headless = get_platform_specific_options(system)
    
    # Example URL
    url = "https://www.futbin.com/26/player/257/melchie-dumornay/market"
    
    print(f"\n🕷️ Starting Futbin Crawler...")
    print(f"Mode: {'Headless' if headless else 'GUI'}")
    print(f"URL: {url}\n")
    
    try:
        # Initialize crawler with platform-specific settings
        with FutbinCrawler(headless=headless) as crawler:
            # Extract data
            result = crawler.extract(url)
            
            if result['success']:
                print("✅ SUCCESS - Data extracted!\n")
                data = result['data']
                print(f"💰 Cheapest Sale: {data['cheapest_sale']:,} coins" if data['cheapest_sale'] else "💰 Cheapest Sale: Not found")
                print(f"📈 Average BIN: {data['actual_price']:,} coins" if data['actual_price'] else "📈 Average BIN: Not found")
                print(f"📊 EA Avg Price: {data['average_price']:,} coins" if data['average_price'] else "📊 EA Avg Price: Not found")
            else:
                print("❌ FAILED - Could not extract data")
                print(f"Error: {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting tips:")
        
        if system == "Linux":
            print("""
For Linux, ensure Chrome/Chromium is installed:
  Ubuntu/Debian: sudo apt-get install chromium-browser
  Fedora: sudo dnf install chromium
  Arch: sudo pacman -S chromium
""")
        elif system == "Windows":
            print("""
For Windows, ensure Google Chrome is installed:
  Download from: https://www.google.com/chrome/
""")


if __name__ == "__main__":
    test_crawler()
