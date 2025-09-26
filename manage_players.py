#!/usr/bin/env python3
"""
Utility script to manage player links in the JSON configuration
"""

import json
import sys
from typing import Optional


class PlayerManager:
    """
    Manager for player links configuration
    """
    
    def __init__(self, config_file: str = "player_links.json"):
        self.config_file = config_file
        self.load_config()
    
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
    
    def add_player(self, name: str, url: str, notes: str = "", enabled: bool = True):
        """Add a new player to configuration"""
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
        print("7. Exit")
        
        choice = input("\nSelect option (1-7): ").strip()
        
        if choice == "1":
            manager.list_players()
        
        elif choice == "2":
            print("\n--- ADD PLAYER ---")
            name = input("Player name: ").strip()
            url = input("Futbin URL: ").strip()
            notes = input("Notes (optional): ").strip()
            enabled = input("Enable player? (y/n): ").strip().lower() == 'y'
            
            if name and url:
                manager.add_player(name, url, notes, enabled)
            else:
                print("❌ Name and URL are required")
        
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
        
        elif command == "add" and len(sys.argv) >= 4:
            name = sys.argv[2]
            url = sys.argv[3]
            notes = sys.argv[4] if len(sys.argv) > 4 else ""
            manager.add_player(name, url, notes)
        
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
        
        else:
            print("Usage:")
            print("  python manage_players.py                    # Interactive mode")
            print("  python manage_players.py list               # List all players")
            print("  python manage_players.py add NAME URL [NOTES]")
            print("  python manage_players.py remove NAME")
            print("  python manage_players.py enable NAME")
            print("  python manage_players.py disable NAME")
            print("  python manage_players.py settings")
    
    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()
