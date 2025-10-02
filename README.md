# Futbin Player Market Crawler

Automated price tracker for Futbin.com with Google Sheets integration.

## 🎯 Key Features

✅ **Google Sheets V2** - Manage players directly in spreadsheet  
✅ **Auto-sync** - Updates every 30 seconds  
✅ **Smart dropdowns** - Auto-updates validation lists  
✅ **Multi-player** - Track unlimited players  
✅ **Anti-bot bypass** - Uses undetected-chromedriver

## What It Extracts

- **Cheapest Sale** - Lowest listed price
- **Average BIN** - Buy It Now average
- **EA Average** - EA's calculated price

## Installation

1. Clone repository
```bash
git clone https://github.com/yourusername/futbin-crawler
cd futbin-crawler
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Make sure you have Chrome browser installed (required for Selenium)

## 🚀 Quick Start

### Google Sheets Integration (Recommended)

1. **Setup Google Cloud** - Follow setup in [GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md)
2. **Run V2 Connector**:
```bash
python google_sheets_connector_v2.py YOUR_SPREADSHEET_ID
```
3. **Manage players** directly in Google Sheets "Players" tab

### Alternative: JSON Configuration

```bash
# Manage players locally
python manage_players.py

# Quickly add a player by name (URL auto-detected)
python manage_players.py add "Kylian Mbappé"

# Run crawler with JSON config
python crawler_with_config.py
```


## 🔗 Google Sheets Integration Details

### Google Cloud Setup (5 Steps)

1️⃣ **Enable API**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create project → Search "Google Sheets API" → Enable

2️⃣ **Create Service Account**
   - APIs & Services → Credentials → Create Credentials
   - Service account → Name: `futbin-crawler-bot`

3️⃣ **Download Key**
   - Click service account → Keys tab → Add Key
   - JSON format → Save as `credentials.json`

4️⃣ **Share Sheet**
   - Copy service account email
   - Share Google Sheet with this email as Editor

5️⃣ **Get Sheet ID**
   - From URL: `docs.google.com/spreadsheets/d/ABC123/edit`
   - Your ID: `ABC123`

## 📁 Files

**Main Scripts**
- `google_sheets_connector_v2.py` - V2 with player management in Sheets
- `futbin_crawler_working.py` - Core extraction engine
- `manage_players.py` - Player management CLI

**Documentation**
- `GOOGLE_SHEETS_SETUP.md` - Google Cloud setup guide
- `GOOGLE_SHEETS_PLAYERS_GUIDE.md` - Player management guide

**🔒 Security**
- Never commit `credentials.json` to Git!
- Already added to `.gitignore`

## Tips

- Use V2 for Google Sheets management
- Dropdowns auto-update with new values
- Changes apply on next 30-second cycle
- Press Ctrl+C to stop

## License

Educational purposes only.

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
