# Futbin Player Market Crawler

A Python-based web crawler for extracting player market data from Futbin.com player pages.

**✅ WORKING VERSION: Use `futbin_crawler_working.py` for the fully functional crawler**

## Features

- Extracts key market data:
  - **Cheapest Sale**: The lowest price the player is being sold for
  - **Actual Price**: The current average BIN (Buy It Now) price
  - **Average Price**: The EA average price

- Supports both static and dynamic content extraction
- Uses Selenium for JavaScript-rendered content
- Includes error handling and fallback mechanisms
- Returns data in structured JSON format

## Installation

1. Clone or download this repository

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Make sure you have Chrome browser installed (required for Selenium)

## Usage

### Basic Usage (Use the Working Version)

```python
from futbin_crawler_working import FutbinCrawler

# Initialize the crawler
crawler = FutbinCrawler(use_selenium=True, headless=True)

# Extract data from a player's market page
url = "https://www.futbin.com/26/player/257/melchie-dumornay/market"
result = crawler.extract(url)

# Print the results
if result['success']:
    print(f"Cheapest Sale: {result['data']['cheapest_sale']}")
    print(f"Actual Price: {result['data']['actual_price']}")
    print(f"Average Price: {result['data']['average_price']}")

# Clean up
crawler.close()
```

### Run the Working Crawler

```bash
python futbin_crawler_working.py
```

This will extract data from the Melchie Dumornay player page and display the results.

### Run Spreadsheet Integration Example

```bash
python spreadsheet_integration_example.py
```

This demonstrates CSV export and shows how to integrate with Google Sheets.

## API Reference

### FutbinCrawler Class

#### `__init__(use_selenium=True, headless=True)`
- `use_selenium`: Whether to use Selenium for dynamic content (recommended)
- `headless`: Whether to run browser in headless mode (no GUI)

#### `extract(url)`
Extracts market data from a Futbin player URL.

**Returns:**
```json
{
  "success": true,
  "url": "https://futbin.com/...",
  "data": {
    "cheapest_sale": 54500,
    "actual_price": 60373,
    "average_price": 65000
  }
}
```

#### `close()`
Closes the Selenium driver and cleans up resources.

## Data Fields

- **Cheapest Sale**: The lowest listed price for the player card
- **Actual Price**: The current average BIN (Buy It Now) price - what players are actually selling for
- **Average Price**: The EA-calculated average price across all platforms

## Future Integration

This crawler is designed to be easily integrated with:
- Google Sheets (via Google Sheets API)
- Excel files (via openpyxl or pandas)
- Databases (PostgreSQL, MongoDB, etc.)
- REST APIs
- Automated monitoring systems

### Example: Save to CSV

```python
import csv
from futbin_crawler import FutbinCrawler

crawler = FutbinCrawler()
urls = [
    "https://www.futbin.com/26/player/257/melchie-dumornay/market",
    # Add more URLs
]

with open('player_prices.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['url', 'cheapest_sale', 'actual_price', 'average_price'])
    writer.writeheader()
    
    for url in urls:
        result = crawler.extract(url)
        if result['success']:
            writer.writerow({
                'url': url,
                **result['data']
            })

crawler.close()
```

## Troubleshooting

1. **Chrome/Chromedriver Issues**: The crawler uses `webdriver-manager` to automatically handle Chrome driver installation.

2. **Data Not Found**: Futbin may change their HTML structure. The crawler includes multiple extraction methods as fallbacks.

3. **Rate Limiting**: If making multiple requests, add delays between them to avoid being blocked:
```python
import time
time.sleep(2)  # Wait 2 seconds between requests
```

## Notes

- The crawler respects website structure and includes proper headers
- For production use, consider implementing rate limiting and caching
- Always check Futbin's terms of service and robots.txt

## License

This project is for educational purposes. Please respect Futbin's terms of service when using this crawler.
