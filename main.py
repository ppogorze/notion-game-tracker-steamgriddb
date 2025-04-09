#!/usr/bin/env python3
"""
Game Collection Manager CLI

This application helps you manage your game collection by:
1. Searching for games on SteamGridDB
2. Adding them to your Notion database
"""

import os
import sys
import questionary
from rich.console import Console
from rich.panel import Panel

from app.services.steamgriddb import SteamGridDBService
from app.services.notion import NotionService
from app.utils.config_manager import ConfigManager
from app.utils.library_manager import library_menu

console = Console()

def main():
    """Main entry point for the CLI application."""
    console.print(Panel.fit(
        "[bold cyan]Game Collection Manager[/bold cyan]\n"
        "[italic]Connect your games to Notion[/italic]",
        border_style="cyan"
    ))
    
    # Load configuration
    config_manager = ConfigManager()
    config = config_manager.load_config()
    
    # Check if configuration is complete
    if not config_manager.is_config_complete():
        console.print("[yellow]Configuration is incomplete. Please update settings.[/yellow]")
        if not settings_menu(config_manager):
            console.print("[red]Configuration required to continue.[/red]")
            return
    
    # Initialize services with config
    # Reload config to ensure we have the latest values
    config = config_manager.load_config()
    
    steam_service = SteamGridDBService(config.get('steamgriddb_api_key', ''))
    notion_service = NotionService(
        config.get('notion_token', ''),
        config.get('notion_database_id', '')
    )
    
    # Main program loop
    while True:
        choice = questionary.select(
            "What would you like to do?",
            choices=[
                "Add Game",
                "View Game Library",
                "Settings",
                "Exit"
            ]
        ).ask()
        
        if choice == "Add Game":
            add_game(steam_service, notion_service)
        elif choice == "View Game Library":
            library_menu(notion_service, steam_service)
        elif choice == "Settings":
            if settings_menu(config_manager):
                # Reload configuration and reinitialize services
                config = config_manager.load_config()
                steam_service = SteamGridDBService(config.get('steamgriddb_api_key', ''))
                notion_service = NotionService(
                    config.get('notion_token', ''),
                    config.get('notion_database_id', '')
                )
        elif choice == "Exit":
            console.print("[green]Goodbye![/green]")
            sys.exit(0)

def add_game(steam_service, notion_service):
    """Handle the game addition workflow."""
    # Get game name from user
    game_name = questionary.text("Enter game name:").ask()
    if not game_name:
        console.print("[yellow]Game name cannot be empty.[/yellow]")
        return
    
    console.print(f"[cyan]Searching for [bold]{game_name}[/bold] on SteamGridDB...[/cyan]")
    
    # Search for the game on SteamGridDB
    try:
        search_results = steam_service.search_game(game_name)
        
        if not search_results:
            console.print("[yellow]No games found matching that name.[/yellow]")
            return
        
        # Let user select from matching results
        game_choices = []
        for game in search_results:
            # Check if the result has the expected structure
            if isinstance(game, dict) and 'name' in game:
                release_date = game.get('release_date', 'Unknown')
                game_choices.append(f"{game['name']} ({release_date})")
            elif isinstance(game, dict) and 'text' in game:
                # Handle autocomplete response format
                release_info = game.get('release', '')
                release_text = f" ({release_info})" if release_info else ""
                game_choices.append(f"{game['text']}{release_text}")
        game_choices.append("Cancel")
        
        selected = questionary.select(
            "Select a game:",
            choices=game_choices
        ).ask()
        
        if selected == "Cancel":
            return
        
        # Find the selected game in the results
        selected_index = game_choices.index(selected)
        selected_game = search_results[selected_index]
        
        # Get the game name and ID based on the response format
        if 'name' in selected_game:
            game_name = selected_game['name']
            game_id = selected_game['id']
        elif 'text' in selected_game:
            game_name = selected_game['text']
            game_id = selected_game['id']
        else:
            console.print("[red]Error: Invalid game data format[/red]")
            return
        
        console.print(f"[green]Selected: [bold]{game_name}[/bold][/green]")
        
        # Get game assets (icon and poster)
        console.print("[cyan]Retrieving game assets...[/cyan]")
        icon = steam_service.get_game_icon(game_id)
        poster = steam_service.get_game_poster(game_id)
        
        # Add to Notion
        console.print("[cyan]Adding game to Notion...[/cyan]")
        
        # Get release timestamp if available
        release_timestamp = None
        
        # Try different possible keys for the release timestamp
        for key in ['release', 'release_date']:
            if key in selected_game:
                try:
                    # First try direct conversion (for a numeric timestamp)
                    release_timestamp = int(selected_game[key])
                    break
                except (ValueError, TypeError):
                    # If direct conversion fails, try to extract timestamp from string
                    try:
                        # Extract timestamp from string like "(1632182400)"
                        timestamp_str = selected_game[key]
                        if isinstance(timestamp_str, str) and '(' in timestamp_str and ')' in timestamp_str:
                            # Extract the number between parentheses
                            timestamp_part = timestamp_str.split('(')[1].split(')')[0]
                            if timestamp_part.isdigit():
                                release_timestamp = int(timestamp_part)
                                break
                    except Exception:
                        # If all extraction attempts fail, continue to the next key
                        pass
        
        # Debug output
        console.print(f"[dim]Debug: Release timestamp extracted: {release_timestamp}[/dim]")
        
        # Prompt for game status
        status_choices = [
            "Chcę zagrać",
            "Przestałem grać",
            "W trakcie",
            "Ukończone",
            "No Status"
        ]
        
        status = questionary.select(
            "Game status:",
            choices=status_choices,
            default="No Status"
        ).ask()
        
        # Prompt for game platform
        platform_choices = [
            "PC",
            "PS4",
            "PS5",
            "Switch"
        ]
        
        platform = questionary.select(
            "Game platform:",
            choices=platform_choices,
            default="PC"
        ).ask()
        
        notion_service.add_game(
            name=game_name,
            icon_url=icon,
            poster_url=poster,
            release_timestamp=release_timestamp,
            status=status,
            platform=platform
        )
        
        console.print(f"[green]✓ Added [bold]{game_name}[/bold] to Notion database[/green]")
    
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")

def settings_menu(config_manager):
    """Handle the settings menu."""
    console.print(Panel.fit(
        "[bold]Settings[/bold]",
        border_style="cyan"
    ))
    
    # Load current config
    config = config_manager.load_config()
    
    # Update settings
    notion_db = questionary.text(
        "Notion Database ID (or full URL):",
        default=config.get('notion_database_id', '')
    ).ask()
    
    notion_token = questionary.text(
        "Notion Integration Secret:",
        default=config.get('notion_token', '')
    ).ask()
    
    steamgrid_key = questionary.text(
        "SteamGridDB API Key:",
        default=config.get('steamgriddb_api_key', '')
    ).ask()
    
    # Save new settings
    new_config = {
        'notion_database_id': notion_db,
        'notion_token': notion_token,
        'steamgriddb_api_key': steamgrid_key
    }
    
    config_manager.save_config(new_config)
    console.print("[green]Settings saved successfully![/green]")
    
    # Return True if config is complete
    return config_manager.is_config_complete()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Program interrupted.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Unexpected error: {str(e)}[/red]")
        sys.exit(1)
