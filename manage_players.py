#!/usr/bin/env python3
"""
Utility script to manage player links in the JSON configuration
"""

import json
import sys
from typing import List, Optional

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus


class PlayerManager:
    """
    Manager for player links configuration
    """

    FUTBIN_SEARCH_URL = "https://www.futbin.com/players?page=1&search={query}"
    FUTBIN_PLAYERS_LIST_URL = "https://www.futbin.com/players?page={page}"
    USER_AGENT = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )

    def __init__(self, config_file: str = "player_links.json"):
        self.config_file = config_file
        self.load_config()

    def _normalize_url(self, url: str) -> str:
        """Ensure Futbin URLs are complete and point to the market tab"""
        if not url:
            return url

        if not url.startswith("http"):
            url = f"https://www.futbin.com{url}" if url.startswith("/") else f"https://www.futbin.com/{url}"

        if not url.endswith("/market"):
            url = url.rstrip("/") + "/market"

        return url

    def search_player_urls(self, name: str, limit: int = 5) -> List[dict]:
        """Search Futbin for player URLs by name"""
        if not name:
            return []

        search_url = self.FUTBIN_SEARCH_URL.format(query=quote_plus(name))
        headers = {"User-Agent": self.USER_AGENT}

        try:
            response = requests.get(search_url, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"❌ Futbin search failed with status code {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, "html.parser")
            rows = soup.select("table tbody tr")
            results = []

            for row in rows:
                link = row.find("a", href=True)
                if not link:
                    continue

                player_name = link.get_text(strip=True)
                href = self._normalize_url(link["href"])

                if href and player_name:
                    results.append({"name": player_name, "url": href})

                if len(results) >= limit:
                    break

            if not results:
                print(f"❌ No players found for '{name}'")

            return results

        except requests.RequestException as exc:
            print(f"❌ Error searching Futbin: {exc}")
            return []

    def fetch_players_page(self, page: int) -> List[dict]:
        """Fetch a page of players from Futbin listings"""
        list_url = self.FUTBIN_PLAYERS_LIST_URL.format(page=page)
        headers = {"User-Agent": self.USER_AGENT}

        try:
            response = requests.get(list_url, headers=headers, timeout=20)
            if response.status_code != 200:
                print(f"❌ Futbin listing request failed (page {page}) with status {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, "html.parser")
            rows = soup.select("table tbody tr")
            players = []

            for row in rows:
                link = None
                for anchor in row.find_all("a", href=True):
                    if "/player/" in anchor["href"]:
                        link = anchor
                        break

                if not link:
                    continue

                name = link.get_text(strip=True)
                url = self._normalize_url(link["href"])

                if not name or not url:
                    continue

                version = ""
                version_cell = row.find("span", class_="players_club_nation")
                if version_cell:
                    version = version_cell.get_text(strip=True)

                players.append({
                    "name": name,
                    "url": url,
                    "notes": version
                })

            return players

        except requests.RequestException as exc:
            print(f"❌ Error loading Futbin page {page}: {exc}")
            return []

    def load_config(self):
        """Load configuration from file"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            print(f"Creating new configuration file: {self.config_file}")
            self.config = {
                "players": [],
                "settings": {
                    "delay_between_requests": 3,
                    "headless_mode": False,
                    "save_to_csv": True,
                    "csv_filename": "futbin_prices.csv"
                }
            }
            self.save_config()
    
    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        print(f"✅ Configuration saved to {self.config_file}")
    
    def add_player(self, name: str, url: Optional[str] = None, notes: str = "", enabled: bool = True):
        """Add a new player to configuration"""
        if not url:
            print(f"🔍 Searching Futbin for '{name}'...")
            matches = self.search_player_urls(name)

            if not matches:
                print("❌ Could not find a matching player. Please provide the URL manually.")
                return False

            url = matches[0]["url"]
            print(f"✅ Using URL for '{matches[0]['name']}': {url}")
        else:
            url = self._normalize_url(url)

        player = {
            "name": name,
            "url": url,
            "enabled": enabled,
            "notes": notes
        }
        
        # Check if player already exists
        for existing in self.config['players']:
            if existing['url'] == url:
                print(f"⚠️ Player with URL already exists: {existing['name']}")
                return False
        
        self.config['players'].append(player)
        self.save_config()
        print(f"✅ Added player: {name}")
        return True
    
    def remove_player(self, name: str):
        """Remove a player by name"""
        original_count = len(self.config['players'])
        self.config['players'] = [p for p in self.config['players'] if p['name'] != name]
        
        if len(self.config['players']) < original_count:
            self.save_config()
            print(f"✅ Removed player: {name}")
            return True
        else:
            print(f"❌ Player not found: {name}")
            return False
    
    def enable_player(self, name: str, enabled: bool = True):
        """Enable or disable a player"""
        for player in self.config['players']:
            if player['name'] == name:
                player['enabled'] = enabled
                self.save_config()
                status = "enabled" if enabled else "disabled"
                print(f"✅ Player {status}: {name}")
                return True
        
        print(f"❌ Player not found: {name}")
        return False

    def list_players(self):
        """List all players in configuration"""
        if not self.config['players']:
            print("No players configured")
            return
        
        print("\n" + "="*70)
        print("CONFIGURED PLAYERS")
        print("="*70)
        
        for i, player in enumerate(self.config['players'], 1):
            status = "✅" if player.get('enabled', True) else "❌"
            print(f"\n{i}. {status} {player['name']}")
            print(f"   URL: {player['url']}")
            if player.get('notes'):
                print(f"   Notes: {player['notes']}")
    
    def update_settings(self, key: str, value):
        """Update a setting"""
        if key in self.config['settings']:
            old_value = self.config['settings'][key]
            self.config['settings'][key] = value
            self.save_config()
            print(f"✅ Updated {key}: {old_value} → {value}")
        else:
            print(f"❌ Unknown setting: {key}")
    
    def show_settings(self):
        """Display current settings"""
        print("\n" + "="*70)
        print("CURRENT SETTINGS")
        print("="*70)
        
        for key, value in self.config['settings'].items():
            print(f"{key}: {value}")

    def bulk_import_players(self, start_page: int = 1, end_page: Optional[int] = None,
                             max_players: Optional[int] = None, enable: bool = True):
        """Import players from Futbin listing pages"""

        existing_urls = {player['url'] for player in self.config['players']}
        imported = 0
        current_page = start_page

        while True:
            if end_page is not None and current_page > end_page:
                break

            print(f"📄 Fetching Futbin page {current_page}...")
            players = self.fetch_players_page(current_page)
            if not players:
                print("⚠️ No players returned for this page; stopping import.")
                break

            added_this_page = 0
            for player in players:
                if player['url'] in existing_urls:
                    continue

                self.config['players'].append({
                    "name": player['name'],
                    "url": player['url'],
                    "enabled": enable,
                    "notes": player.get('notes', "")
                })
                existing_urls.add(player['url'])
                imported += 1
                added_this_page += 1

                if max_players is not None and imported >= max_players:
                    break

            if max_players is not None and imported >= max_players:
                break

            print(f"   ↳ Added {added_this_page} new players")
            current_page += 1

        if imported:
            self.save_config()
            print(f"✅ Imported {imported} players from Futbin")
        else:
            print("⚠️ No new players were imported")


def interactive_mode():
    """Interactive mode for managing players"""
    manager = PlayerManager()
    
    while True:
        print("\n" + "="*50)
        print("PLAYER MANAGER")
        print("="*50)
        print("1. List players")
        print("2. Add player")
        print("3. Remove player")
        print("4. Enable/Disable player")
        print("5. Show settings")
        print("6. Update setting")
        print("7. Bulk import from Futbin")
        print("8. Exit")

        choice = input("\nSelect option (1-8): ").strip()

        if choice == "1":
            manager.list_players()
        
        elif choice == "2":
            print("\n--- ADD PLAYER ---")
            name = input("Player name: ").strip()
            url = input("Futbin URL (leave blank to search): ").strip()
            notes = input("Notes (optional): ").strip()
            enabled = input("Enable player? (y/n): ").strip().lower() == 'y'

            if name and url:
                manager.add_player(name, url, notes, enabled)
            elif name:
                if not url:
                    matches = manager.search_player_urls(name)
                    if matches:
                        print("\nSearch results:")
                        for idx, match in enumerate(matches, 1):
                            print(f"{idx}. {match['name']} - {match['url']}")

                        selection = input("Select player (1-{}), or 0 to cancel: ".format(len(matches))).strip()

                        if selection.isdigit():
                            index = int(selection)
                            if index == 0:
                                print("❌ Cancelled")
                                continue
                            if 1 <= index <= len(matches):
                                chosen = matches[index - 1]
                                manager.add_player(chosen["name"], chosen["url"], notes, enabled)
                                continue

                        print("❌ Invalid selection")
                    else:
                        print("❌ Could not find a matching player")
            else:
                print("❌ Player name is required")

        elif choice == "3":
            manager.list_players()
            name = input("\nEnter player name to remove: ").strip()
            if name:
                manager.remove_player(name)
        
        elif choice == "4":
            manager.list_players()
            name = input("\nEnter player name to toggle: ").strip()
            if name:
                enable = input("Enable player? (y/n): ").strip().lower() == 'y'
                manager.enable_player(name, enable)
        
        elif choice == "5":
            manager.show_settings()
        
        elif choice == "6":
            manager.show_settings()
            print("\nAvailable settings:")
            print("- delay_between_requests (seconds)")
            print("- headless_mode (true/false)")
            print("- save_to_csv (true/false)")
            print("- csv_filename")
            
            key = input("\nSetting to update: ").strip()
            if key in ["delay_between_requests"]:
                value = int(input(f"New value for {key}: ").strip())
            elif key in ["headless_mode", "save_to_csv"]:
                value = input(f"New value for {key} (true/false): ").strip().lower() == 'true'
            else:
                value = input(f"New value for {key}: ").strip()

            manager.update_settings(key, value)

        elif choice == "7":
            print("\n--- BULK IMPORT ---")
            start_page = input("Start page (default 1): ").strip()
            end_page = input("End page (leave blank for until empty): ").strip()
            max_players = input("Maximum players to import (leave blank for unlimited): ").strip()
            enable = input("Enable imported players? (y/n, default y): ").strip().lower() != 'n'

            start_page_val = int(start_page) if start_page.isdigit() else 1
            end_page_val = int(end_page) if end_page.isdigit() else None
            max_players_val = int(max_players) if max_players.isdigit() else None

            manager.bulk_import_players(
                start_page=start_page_val,
                end_page=end_page_val,
                max_players=max_players_val,
                enable=enable
            )

        elif choice == "8":
            print("Goodbye!")
            break

        else:
            print("Invalid option")


def main():
    """Main function"""
    
    if len(sys.argv) > 1:
        # Command line mode
        manager = PlayerManager()
        command = sys.argv[1].lower()
        
        if command == "list":
            manager.list_players()
        
        elif command == "add" and len(sys.argv) >= 3:
            name = sys.argv[2]
            url = sys.argv[3] if len(sys.argv) >= 4 else None
            notes = sys.argv[4] if len(sys.argv) >= 5 else ""
            manager.add_player(name, url, notes)

        elif command == "search" and len(sys.argv) >= 3:
            name = " ".join(sys.argv[2:])
            results = manager.search_player_urls(name, limit=10)
            if results:
                print("\nSearch results:")
                for idx, result in enumerate(results, 1):
                    print(f"{idx}. {result['name']} -> {result['url']}")

        elif command == "remove" and len(sys.argv) >= 3:
            name = sys.argv[2]
            manager.remove_player(name)
        
        elif command == "enable" and len(sys.argv) >= 3:
            name = sys.argv[2]
            manager.enable_player(name, True)
        
        elif command == "disable" and len(sys.argv) >= 3:
            name = sys.argv[2]
            manager.enable_player(name, False)
        
        elif command == "settings":
            manager.show_settings()
        
        elif command == "import_all":
            start_page = int(sys.argv[2]) if len(sys.argv) >= 3 else 1
            end_page = int(sys.argv[3]) if len(sys.argv) >= 4 else None
            max_players = int(sys.argv[4]) if len(sys.argv) >= 5 else None
            manager.bulk_import_players(start_page=start_page, end_page=end_page, max_players=max_players)

        else:
            print("Usage:")
            print("  python manage_players.py                    # Interactive mode")
            print("  python manage_players.py list               # List all players")
            print("  python manage_players.py add NAME [URL] [NOTES]")
            print("  python manage_players.py search NAME        # Search for player URLs")
            print("  python manage_players.py remove NAME")
            print("  python manage_players.py enable NAME")
            print("  python manage_players.py disable NAME")
            print("  python manage_players.py settings")
            print("  python manage_players.py import_all [START_PAGE] [END_PAGE] [MAX]")
    
    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()
