# Google Sheets Player Management (V2)

## Quick Start
Manage players directly in Google Sheets - no JSON editing required!

## Players Sheet Structure

| Column | Description | Example |
| **Name** | Player's display name | Ronaldo |
| **FutBinLink** | Full Futbin market URL | https://www.futbin.com/26/player/724/.../market |
| **Rarity** | Card type/rarity | Icon, Gold Rare, Hero, TOTW |
| **Enabled** | Track this player? | TRUE or FALSE |

## Adding Players

1. Open Google Sheets → "Players" tab
2. Add new row with player details
3. Set Enabled = TRUE to track

### Example

| Name | FutBinLink | Rarity | Enabled |
| Melchie Dumornay | https://www.futbin.com/26/player/257/melchie-dumornay/market | Gold Rare | TRUE |
| Ronaldo | https://www.futbin.com/26/player/724/cristiano-ronaldo-dos-santos-aveiro/market | Icon | TRUE |
| Isak | https://www.futbin.com/26/player/52/alexander-isak/market | Gold Rare | TRUE |
| Mbappe | https://www.futbin.com/26/player/XXX/mbappe/market | Gold Rare | FALSE |

## Getting Futbin URLs

1. Search player on [Futbin.com](https://www.futbin.com)
2. Click player → "Market" tab
3. Copy URL (must end with `/market`)

## Enable/Disable Values

| Enable | Disable |
|--------|---------|  
| TRUE, YES, 1 | FALSE, NO, 0 |

## Running

```bash
python google_sheets_connector_v2.py YOUR_SPREADSHEET_ID
```

### Process
1. Reads "Players" sheet
2. Extracts prices for enabled players
3. Updates dropdowns automatically
4. Pushes to "Sheet1"
5. Repeats every 30 seconds

## Key Features

✅ No JSON editing  
✅ Real-time updates (30-second cycles)  
✅ Automatic dropdown updates  
✅ Team collaboration  
✅ Visual management  

## Output Columns

Data in "Sheet1":
- Timestamp
- Player Name (auto-updates dropdown)
- Cheapest Sale  
- Average BIN
- EA Avg Price
- Rarity (auto-updates dropdown)
- URL

## Troubleshooting

| Issue | Fix |
|-------|-----|
| No players found | Ensure Enabled = TRUE |
| Player not tracked | Check URL ends with /market |
| Changes not applied | Wait for next 30-second cycle |

## Tips

- Sort by Rarity for organization
- Add extra columns for notes (won't affect crawler)
- Test with one player first
- Use Google Sheets filters for large lists
- Changes apply on next 30-second cycle
