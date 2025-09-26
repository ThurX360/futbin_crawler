# Futbin Player Market Crawler

A Python-based web crawler for extracting player market data from Futbin.com player pages.

**✅ WORKING VERSION: Successfully extracts data for multiple players using JSON configuration**

## 🚀 Latest Test Results

Successfully extracted data for:
- **Melchie Dumornay**: Cheapest 54,000 | Avg BIN 60,556 | EA Avg 65,000
- **Cristiano Ronaldo**: Cheapest 9,800 | Avg BIN 12,289 | EA Avg 13,125

## Features

### Core Capabilities
- **Multi-player support** via JSON configuration
- **Player management system** with interactive interface
- **Automatic data extraction** for:
  - Cheapest Sale price
  - Average BIN (Buy It Now) price
  - EA Average price
- **CSV export** for spreadsheet integration
- **JSON export** for API integration
- **Configurable settings** (delays, headless mode, etc.)
- **Cross-platform support** (Windows, Linux, macOS)

### Technical Features
- Uses `undetected-chromedriver` to bypass anti-bot protection
- BeautifulSoup for HTML parsing
- Selenium for JavaScript-rendered content
- Robust error handling and logging
- Rate limiting protection

## Installation

1. Clone or download this repository

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Make sure you have Chrome browser installed (required for Selenium)

## 🎯 Quick Start

### Method 1: JSON Configuration (Recommended)

The easiest way to use the crawler is with the JSON configuration system:

1. **Add players to track** using the interactive manager:
```bash
python manage_players.py
```

2. **Run the crawler** to extract data for all enabled players:
```bash
python crawler_with_config.py
```

Your data will be saved to:
- `futbin_prices.csv` - For spreadsheet import
- `extraction_results.json` - Complete data with metadata

### Method 2: Direct Usage (Single Player)

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

## 📋 Player Management System

### Managing Players with `player_links.json`

The crawler uses a JSON configuration file to manage multiple players:

```json
{
  "players": [
    {
      "name": "Melchie Dumornay",
      "url": "https://www.futbin.com/26/player/257/melchie-dumornay/market",
      "enabled": true,
      "notes": "Gold Rare - EA FC 26"
    },
    {
      "name": "Ronaldo",
      "url": "https://www.futbin.com/26/player/724/cristiano-ronaldo-dos-santos-aveiro/market",
      "enabled": true,
      "notes": ""
    }
  ],
  "settings": {
    "delay_between_requests": 3,
    "headless_mode": false,
    "save_to_csv": true,
    "csv_filename": "futbin_prices.csv"
  }
}
```

### Using the Player Manager

#### Interactive Mode
```bash
python manage_players.py
```

This opens an interactive menu where you can:
- List all configured players
- Add new players
- Remove players
- Enable/disable players
- Update crawler settings

#### Command-Line Mode
```bash
# List all players
python manage_players.py list

# Add a new player
python manage_players.py add "Player Name" "https://futbin.com/url" "Notes"

# Enable/disable a player
python manage_players.py enable "Player Name"
python manage_players.py disable "Player Name"

# Remove a player
python manage_players.py remove "Player Name"

# View current settings
python manage_players.py settings
```

### Running the Crawler with Configuration

```bash
python crawler_with_config.py
```

This will:
1. Load all players from `player_links.json`
2. Extract data for each **enabled** player
3. Wait 3 seconds between requests (configurable)
4. Save results to CSV and JSON files
5. Display a summary report

### Example Output

```
[1/2] Processing Melchie Dumornay...
  ✅ Success!
     Cheapest: 54,000
     Avg BIN: 60,556
     EA Avg: 65,000

[2/2] Processing Ronaldo...
  ✅ Success!
     Cheapest: 9,800
     Avg BIN: 12,289
     EA Avg: 13,125
```

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

## 📁 Project Files

### Main Files
- `crawler_with_config.py` - Main crawler using JSON configuration
- `player_links.json` - Configuration file for player URLs and settings
- `manage_players.py` - Interactive player management utility
- `futbin_crawler_working.py` - Core crawler engine
- `spreadsheet_integration_example.py` - CSV/spreadsheet integration examples

### Output Files
- `futbin_prices.csv` - Price data in CSV format
- `extraction_results.json` - Complete extraction results with metadata

## Data Fields

- **Cheapest Sale**: The lowest listed price for the player card
- **Actual Price**: The current average BIN (Buy It Now) price - what players are actually selling for
- **Average Price**: The EA-calculated average price across all platforms
- **Timestamp**: Date and time of data extraction
- **Player Name**: Name of the player
- **Notes**: Any additional notes about the player

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
