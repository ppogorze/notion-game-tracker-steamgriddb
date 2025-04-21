#!/usr/bin/env python3
"""
Collection Manager CLI

This application helps you manage your collection of:
1. Games
2. Anime
3. Books
4. Vinyl Records
"""

import sys
import questionary
from rich.console import Console
from rich.panel import Panel

from app.utils.config_manager import ConfigManager
from app.services.notion import NotionService

console = Console()

def main():
    """
    Main function to run the collection manager.
    """
    # Display welcome message
    console.print(Panel.fit(
        "[bold blue]Collection Manager[/bold blue]\n"
        "Manage your games, anime, books, and vinyl records with Notion",
        border_style="blue"
    ))

    # Initialize config manager
    config_manager = ConfigManager()

    # Check if config exists, if not, prompt for setup
    config = config_manager.load_config()
    if not config:
        console.print("[yellow]No configuration found. Let's set up your Notion integration.[/yellow]")
        setup_config(config_manager)

    # Main menu
    while True:
        choice = questionary.select(
            "What would you like to manage?",
            choices=[
                "Games",
                "Anime",
                "Books",
                "Vinyl Records",
                "Configure settings",
                "Exit"
            ]
        ).ask()

        if choice == "Games":
            import games
            games.main()
        elif choice == "Anime":
            import anime
            anime.main()
        elif choice == "Books":
            import books
            books.main()
        elif choice == "Vinyl Records":
            import vinyls
            vinyls.main()
        elif choice == "Configure settings":
            configure_settings(config_manager)
        elif choice == "Exit":
            console.print("[blue]Goodbye![/blue]")
            sys.exit(0)

def setup_config(config_manager):
    """
    Set up the initial configuration.

    Args:
        config_manager (ConfigManager): The configuration manager
    """
    # Prompt for Notion token
    notion_token = questionary.text(
        "Enter your Notion integration token:",
        validate=lambda text: len(text) > 0 or "Token cannot be empty"
    ).ask()

    # Prompt for Notion database IDs
    games_database_id = questionary.text(
        "Enter your Notion games database ID or URL (leave empty if not using):"
    ).ask()

    anime_database_id = questionary.text(
        "Enter your Notion anime database ID or URL (leave empty if not using):"
    ).ask()

    books_database_id = questionary.text(
        "Enter your Notion books database ID or URL (leave empty if not using):"
    ).ask()

    vinyls_database_id = questionary.text(
        "Enter your Notion vinyl records database ID or URL (leave empty if not using):"
    ).ask()

    # Save configuration
    config = {
        'notion_token': notion_token
    }

    if games_database_id:
        config['games_database_id'] = games_database_id

    if anime_database_id:
        config['anime_database_id'] = anime_database_id

    if books_database_id:
        config['books_database_id'] = books_database_id

    if vinyls_database_id:
        config['vinyls_database_id'] = vinyls_database_id

    config_manager.save_config(config)
    console.print("[green]Configuration saved successfully![/green]")

def configure_settings(config_manager):
    """
    Configure application settings.

    Args:
        config_manager (ConfigManager): The configuration manager
    """
    # Load current config
    config = config_manager.load_config()

    # Show current settings
    console.print("\n[bold]Current Settings:[/bold]")
    console.print(f"Notion Token: {'*' * 10}{config.get('notion_token', '')[-4:] if config.get('notion_token') else 'Not set'}")
    console.print(f"Games Database ID: {config.get('games_database_id', 'Not set')}")
    console.print(f"Anime Database ID: {config.get('anime_database_id', 'Not set')}")
    console.print(f"Books Database ID: {config.get('books_database_id', 'Not set')}")
    console.print(f"Vinyl Records Database ID: {config.get('vinyls_database_id', 'Not set')}")

    # Prompt for settings to change
    setting_to_change = questionary.select(
        "Which setting would you like to change?",
        choices=[
            "Notion Token",
            "Games Database ID",
            "Anime Database ID",
            "Books Database ID",
            "Vinyl Records Database ID",
            "Back to Main Menu"
        ]
    ).ask()

    if setting_to_change == "Back to Main Menu":
        return

    # Update the selected setting
    if setting_to_change == "Notion Token":
        new_value = questionary.text(
            "Enter new Notion token:",
            validate=lambda text: len(text) > 0 or "Token cannot be empty"
        ).ask()
        config['notion_token'] = new_value

    elif setting_to_change == "Games Database ID":
        new_value = questionary.text(
            "Enter new Games database ID or URL (leave empty to remove):"
        ).ask()
        if new_value:
            config['games_database_id'] = new_value
        else:
            config.pop('games_database_id', None)

    elif setting_to_change == "Anime Database ID":
        new_value = questionary.text(
            "Enter new Anime database ID or URL (leave empty to remove):"
        ).ask()
        if new_value:
            config['anime_database_id'] = new_value
        else:
            config.pop('anime_database_id', None)

    elif setting_to_change == "Books Database ID":
        new_value = questionary.text(
            "Enter new Books database ID or URL (leave empty to remove):"
        ).ask()
        if new_value:
            config['books_database_id'] = new_value
        else:
            config.pop('books_database_id', None)

    elif setting_to_change == "Vinyl Records Database ID":
        new_value = questionary.text(
            "Enter new Vinyl Records database ID or URL (leave empty to remove):"
        ).ask()
        if new_value:
            config['vinyls_database_id'] = new_value
        else:
            config.pop('vinyls_database_id', None)

    # Save updated config
    config_manager.save_config(config)
    console.print("[green]Configuration updated successfully![/green]")

if __name__ == "__main__":
    main()
