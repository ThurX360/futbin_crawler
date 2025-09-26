# Managing Players in Google Sheets

## Overview

With `google_sheets_connector_v2.py`, you can now manage all your players directly in Google Sheets! No more editing JSON files - just update your spreadsheet and the crawler will automatically read the latest player list.

## Setting Up the Players Sheet

### The "Players" Sheet Structure

Your Google Sheet now has a "Players" sheet with 4 columns:

| Column | Description | Example |
|--------|-------------|---------|
| **Name** | Player's display name | Ronaldo |
| **FutBinLink** | Full Futbin market URL | https://www.futbin.com/26/player/724/.../market |
| **Rarity** | Card type/rarity | Icon, Gold Rare, Hero, TOTW |
| **Enabled** | Track this player? | TRUE or FALSE |

### Adding New Players

1. Open your Google Sheet
2. Go to the "Players" tab
3. Add a new row with:
   - **Name**: Any name you want to display
   - **FutBinLink**: Copy the full URL from Futbin player's market page
   - **Rarity**: Type of card (optional, for your reference)
   - **Enabled**: Set to `TRUE` to track, `FALSE` to skip

### Example Players Sheet

| Name | FutBinLink | Rarity | Enabled |
|------|------------|--------|---------|
| Melchie Dumornay | https://www.futbin.com/26/player/257/melchie-dumornay/market | Gold Rare | TRUE |
| Ronaldo | https://www.futbin.com/26/player/724/cristiano-ronaldo-dos-santos-aveiro/market | Icon | TRUE |
| Isak | https://www.futbin.com/26/player/52/alexander-isak/market | Gold Rare | TRUE |
| Mbappe | https://www.futbin.com/26/player/XXX/mbappe/market | Gold Rare | FALSE |

## How to Get Futbin URLs

1. Go to [Futbin.com](https://www.futbin.com)
2. Search for your player
3. Click on the player card
4. Click on the "Market" tab
5. Copy the URL from your browser
6. Make sure it ends with `/market`

## Enabling/Disabling Players

In the **Enabled** column, you can use any of these values:

**To ENABLE tracking:**
- `TRUE`
- `YES` 
- `1`
- `ENABLED`

**To DISABLE tracking:**
- `FALSE`
- `NO`
- `0`
- `DISABLED`
- (or leave empty)

## Running the Enhanced Connector

```bash
python google_sheets_connector_v2.py YOUR_SPREADSHEET_ID
```

Or just:
```bash
python google_sheets_connector_v2.py
```
(It will ask for the ID or read from player_links.json)

## What Happens When Running

1. **Reads Players Sheet** - Gets the latest player list from Google Sheets
2. **Extracts Prices** - Only for players marked as Enabled
3. **Pushes to Sheet1** - Adds price data with timestamps
4. **Repeats Every 30 Seconds** - Automatically refreshes player list each time

## Benefits of Google Sheets Management

✅ **No Code Editing** - Add/remove players directly in spreadsheet  
✅ **Real-time Updates** - Changes take effect on next extraction cycle  
✅ **Team Collaboration** - Multiple people can manage the player list  
✅ **Easy Enable/Disable** - Temporarily stop tracking without deleting  
✅ **Visual Interface** - See all your players at a glance  

## Tips

1. **Organize by Rarity** - Sort your Players sheet by Rarity column
2. **Add Notes** - You can add extra columns for your own notes (won't affect the crawler)
3. **Test First** - Add one player and verify it works before adding many
4. **Check URLs** - Make sure all URLs end with `/market`
5. **Use Filters** - Google Sheets filters can help manage large player lists

## Data Output

Price data is saved to "Sheet1" with these columns:
- Timestamp
- Player Name
- Cheapest Sale
- Average BIN
- EA Avg Price
- Rarity (from Players sheet)
- URL

## Troubleshooting

**"No players found in Players sheet!"**
- Make sure you have at least one player with Enabled = TRUE
- Check that the sheet is named exactly "Players"

**Player not being tracked**
- Verify Enabled column is set to TRUE
- Check the URL is correct and accessible
- Make sure the player name doesn't have special characters that might cause issues

**Changes not taking effect**
- Wait for the next 30-second cycle
- The player list is reloaded automatically each time

## Advanced Usage

### Custom Update Intervals

Edit the last line in `google_sheets_connector_v2.py`:
```python
connector.run_scheduled(interval_seconds=30)  # Change 30 to your desired seconds
```

### Different Sheet Names

You can use different sheet names:
```python
connector = GoogleSheetsConnectorV2(
    spreadsheet_id=spreadsheet_id,
    players_sheet="MyPlayers",  # Your custom name
    data_sheet="PriceData"      # Your custom name
)
