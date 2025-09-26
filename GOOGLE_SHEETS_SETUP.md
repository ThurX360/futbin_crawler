# Google Sheets Integration Setup Guide

## 📋 Prerequisites

1. A Google account
2. A Google Sheets spreadsheet (create one or use existing)
3. Google Cloud Console access

## 🚀 Step-by-Step Setup

### Step 1: Enable Google Sheets API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. In the search bar, type "Google Sheets API"
4. Click on "Google Sheets API" and click **ENABLE**

### Step 2: Create Service Account Credentials

1. In Google Cloud Console, go to **APIs & Services** → **Credentials**
2. Click **CREATE CREDENTIALS** → **Service account**
3. Give it a name (e.g., "futbin-crawler")
4. Click **CREATE AND CONTINUE**
5. Skip the optional roles (click **CONTINUE**)
6. Click **DONE**

### Step 3: Download Credentials JSON

1. In the Credentials page, find your service account
2. Click on the service account email
3. Go to the **KEYS** tab
4. Click **ADD KEY** → **Create new key**
5. Choose **JSON** format
6. Click **CREATE**
7. Save the downloaded file as `credentials.json` in your futbin-crawler folder

### Step 4: Share Your Google Sheet

1. Open your Google Sheet
2. Copy the service account email from the credentials page (ends with @...iam.gserviceaccount.com)
3. Click **Share** button in your Google Sheet
4. Paste the service account email
5. Give it **Editor** permissions
6. Click **Send**

### Step 5: Get Your Spreadsheet ID

From your Google Sheets URL:
```
https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID/edit
```

Copy the `YOUR_SPREADSHEET_ID` part.

## 🎮 Running the Crawler

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run the Automated Crawler

```bash
python google_sheets_connector.py YOUR_SPREADSHEET_ID
```

Or just run without ID (it will ask for it):

```bash
python google_sheets_connector.py
```

## ⚙️ Configuration

### Update player_links.json (Optional)

Add the spreadsheet ID to your config:

```json
{
  "settings": {
    "google_spreadsheet_id": "YOUR_SPREADSHEET_ID",
    ...
  }
}
```

### Adjust Update Interval

By default, the crawler runs every 30 seconds. To change this, edit line in `google_sheets_connector.py`:

```python
connector.run_scheduled(interval_seconds=30)  # Change 30 to your desired interval
```

## 📊 Google Sheets Format

The data will be pushed to your sheet with these columns:
- **Timestamp** - When the data was extracted
- **Player Name** - Name of the player
- **Cheapest Sale** - Lowest listed price
- **Average BIN** - Average Buy It Now price
- **EA Avg Price** - EA's average price
- **Notes** - Any notes from config
- **URL** - Futbin URL

## 🛑 Stopping the Crawler

Press `Ctrl+C` to stop the automated extraction.

## ❓ Troubleshooting

### "Credentials file not found"
- Make sure `credentials.json` is in the futbin-crawler folder
- Follow Step 3 to download the credentials

### "Permission denied" or "404 Not Found"
- Make sure you shared the Google Sheet with the service account email
- Verify the spreadsheet ID is correct

### "API not enabled"
- Go back to Step 1 and enable the Google Sheets API

### Rate Limiting
- Google Sheets API has quotas (300 requests per minute)
- The 30-second interval should be safe
- If you get rate limited, increase the interval

## 📈 Example Output

Every 30 seconds, new rows will be added to your Google Sheet:

| Timestamp | Player Name | Cheapest Sale | Average BIN | EA Avg Price | Notes | URL |
|-----------|------------|---------------|-------------|--------------|-------|-----|
| 2025-09-26 15:30:00 | Melchie Dumornay | 54000 | 60556 | 65000 | Gold Rare | https://... |
| 2025-09-26 15:30:00 | Ronaldo | 9800 | 12289 | 13125 | | https://... |
| 2025-09-26 15:30:00 | Isak | 15000 | 18500 | 20000 | | https://... |
