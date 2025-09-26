#!/usr/bin/env python3
"""
Simple test script for the Futbin crawler
"""

import json
from futbin_crawler import FutbinCrawler


def test_single_player():
    """Test extraction for a single player"""
    
    # The URL you provided
    url = "https://www.futbin.com/26/player/257/melchie-dumornay/market"
    
    print("="*60)
    print("FUTBIN PLAYER MARKET CRAWLER TEST")
    print("="*60)
    print(f"\nTesting URL: {url}\n")
    
    # Create crawler instance
    print("Initializing crawler...")
    crawler = FutbinCrawler(use_selenium=True, headless=True)
    
    try:
        # Extract data
        print("Extracting data from page...\n")
        result = crawler.extract(url)
        
        # Display results
        if result['success']:
            print("✅ SUCCESS - Data extracted successfully!\n")
            print("Raw JSON Response:")
            print("-" * 40)
            print(json.dumps(result, indent=2))
            print("-" * 40)
            
            print("\n📊 EXTRACTED DATA:")
            print("-" * 40)
            
            data = result['data']
            
            # Format prices with commas for readability
            def format_price(price):
                if price is None:
                    return "Not found"
                return f"{price:,}"
            
            print(f"💰 Cheapest Sale:  {format_price(data['cheapest_sale'])}")
            print(f"📈 Actual Price:   {format_price(data['actual_price'])}")
            print(f"📊 Average Price:  {format_price(data['average_price'])}")
            
        else:
            print("❌ FAILED - Could not extract data\n")
            if result.get('error'):
                print(f"Error: {result['error']}")
            print("\nResponse:")
            print(json.dumps(result, indent=2))
    
    except Exception as e:
        print(f"\n❌ Exception occurred: {e}")
    
    finally:
        # Always close the crawler to clean up resources
        crawler.close()
        print("\n✅ Crawler closed successfully")


def test_multiple_players():
    """Test extraction for multiple players"""
    
    # Add more URLs here if you want to test multiple players
    urls = [
        "https://www.futbin.com/26/player/257/melchie-dumornay/market",
        # Add more player URLs here
    ]
    
    print("="*60)
    print("TESTING MULTIPLE PLAYERS")
    print("="*60)
    
    crawler = FutbinCrawler(use_selenium=True, headless=True)
    results = []
    
    try:
        for url in urls:
            print(f"\nExtracting: {url}")
            result = crawler.extract(url)
            results.append(result)
            
            if result['success']:
                data = result['data']
                print(f"  ✅ Cheapest: {data['cheapest_sale']}, Actual: {data['actual_price']}, Average: {data['average_price']}")
            else:
                print(f"  ❌ Failed to extract data")
    
    finally:
        crawler.close()
    
    # Save all results to a file
    with open('extraction_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n📁 Results saved to extraction_results.json")


if __name__ == "__main__":
    # Run single player test
    test_single_player()
    
    # Uncomment to test multiple players
    # print("\n" + "="*60 + "\n")
    # test_multiple_players()
