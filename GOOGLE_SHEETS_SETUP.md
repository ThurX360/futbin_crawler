# Google Sheets Setup Guide

## Prerequisites
- Google account
- Google Sheets spreadsheet
- Python with pip installed

## Quick Setup (5 Steps)

### 1️⃣ Enable Google Sheets API
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create project named `futbin-crawler`
3. Search for "Google Sheets API" → Click **ENABLE**

### 2️⃣ Create Service Account
1. Go to **APIs & Services** → **Credentials**
2. Click **CREATE CREDENTIALS** → **Service account**
3. Name: `futbin-crawler-bot` → **CREATE**
4. Skip optional steps → **DONE**

### 3️⃣ Download Credentials
1. Click your service account email
2. Go to **KEYS** tab → **ADD KEY** → **Create new key**
3. Choose **JSON** → **CREATE**
4. Rename downloaded file to `credentials.json`
5. Move to futbin-crawler folder

### 4️⃣ Share Your Google Sheet
1. Copy service account email (ends with @...iam.gserviceaccount.com)
2. Open your Google Sheet → Click **Share**
3. Paste email → Set to **Editor**
4. Uncheck "Notify people" → **Share**

### 5️⃣ Get Spreadsheet ID
From URL: `https://docs.google.com/spreadsheets/d/ABC123XYZ/edit`  
Your ID: `ABC123XYZ`

## Running the Crawler

### Install & Run
```bash
# Install dependencies
pip install -r requirements.txt

# Run V2 (Recommended - manages players in Google Sheets)
python google_sheets_connector_v2.py YOUR_SPREADSHEET_ID

# Run V1 (uses player_links.json)
python google_sheets_connector.py YOUR_SPREADSHEET_ID
```

## Troubleshooting

| Error | Solution |
|-------|----------|
| "Credentials file not found" | Ensure `credentials.json` is in project folder |
| "Permission denied" | Share sheet with service account email |
| "API not enabled" | Enable Google Sheets API in Cloud Console |
| Rate limiting | Default 30-second interval is safe |

## Tips
- Press `Ctrl+C` to stop
- V2 reads players from "Players" sheet
- Data goes to "Sheet1" with timestamps
- Dropdowns auto-update with new values
