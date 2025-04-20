#!/usr/bin/env python3
"""
Anime Collection Manager CLI

This application helps you manage your anime collection by:
1. Searching for anime on MyAnimeList (via Jikan API)
2. Adding them to your Notion database
"""

import sys
import questionary
from rich.console import Console
from rich.panel import Panel

from app.services.jikan import JikanService
from app.services.notion import NotionService
from app.utils.config_manager import ConfigManager
from app.utils.library_manager import library_menu

console = Console()

def main():
    """Main entry point for the CLI application."""
    console.print(Panel.fit(
        "[bold magenta]Anime Collection Manager[/bold magenta]\n"
        "[italic]Connect your anime to Notion[/italic]",
        border_style="magenta"
    ))

    # Load configuration
    config_manager = ConfigManager()
    config = config_manager.load_config()

    # Check if configuration is complete for anime
    if not config_manager.is_config_complete(config_type='anime'):
        console.print("[yellow]Anime configuration is incomplete. Please update settings.[/yellow]")
        if not settings_menu(config_manager):
            console.print("[red]Configuration required to continue.[/red]")
            return

    # Initialize services with config
    # Reload config to ensure we have the latest values
    config = config_manager.load_config()

    jikan_service = JikanService()
    notion_service = NotionService(
        config.get('notion_token', ''),
        config.get('anime_database_id', '')
    )

    # Main program loop
    while True:
        choice = questionary.select(
            "What would you like to do?",
            choices=[
                "Add Anime",
                "View Anime Library",
                "Settings",
                "Exit"
            ]
        ).ask()

        if choice == "Add Anime":
            add_anime(jikan_service, notion_service)
        elif choice == "View Anime Library":
            library_menu(notion_service, jikan_service)
        elif choice == "Settings":
            if settings_menu(config_manager):
                # Reload configuration and reinitialize services
                config = config_manager.load_config()
                notion_service = NotionService(
                    config.get('notion_token', ''),
                    config.get('anime_database_id', '')
                )
        elif choice == "Exit":
            console.print("[green]Goodbye![/green]")
            sys.exit(0)

def add_anime(jikan_service, notion_service):
    """Handle the anime addition workflow."""
    # Get anime name from user
    anime_name = questionary.text("Enter anime name:").ask()
    if not anime_name:
        console.print("[yellow]Anime name cannot be empty.[/yellow]")
        return

    console.print(f"[magenta]Searching for [bold]{anime_name}[/bold] on MyAnimeList...[/magenta]")

    # Search for the anime on MyAnimeList via Jikan
    try:
        search_results = jikan_service.search_anime(anime_name)

        if not search_results:
            console.print("[yellow]No anime found matching that name.[/yellow]")
            return

        # Let user select from matching results
        anime_choices = []
        for anime in search_results:
            # Check if the result has the expected structure
            if isinstance(anime, dict) and 'title' in anime:
                year = anime.get('year', 'Unknown')
                anime_choices.append(f"{anime['title']} ({year})")
        anime_choices.append("Cancel")

        selected = questionary.select(
            "Select an anime:",
            choices=anime_choices
        ).ask()

        if selected == "Cancel":
            return

        # Find the selected anime in the results
        selected_index = anime_choices.index(selected)
        selected_anime = search_results[selected_index]

        # Get the anime name and ID
        anime_name = selected_anime['title']
        anime_id = selected_anime['mal_id']

        console.print(f"[green]Selected: [bold]{anime_name}[/bold][/green]")

        # Get detailed anime information
        console.print("[magenta]Retrieving detailed anime information...[/magenta]")
        anime_details = jikan_service.get_anime_full_details(anime_id)

        if not anime_details:
            console.print("[yellow]Could not retrieve detailed information for this anime.[/yellow]")
            return

        # Extract information from the details
        image = anime_details.get("image_url")
        episodes = anime_details.get("episodes")
        synopsis = anime_details.get("synopsis")
        mal_url = anime_details.get("url")
        release_year = anime_details.get("year")
        airing_status = anime_details.get("status")
        seasons = anime_details.get("seasons")

        # Get studio information
        studios = anime_details.get("studios", [])
        studio = studios[0] if studios else None

        # Add to Notion
        console.print("[magenta]Adding anime to Notion...[/magenta]")

        # Prompt for anime status
        status_choices = [
            "Watching",
            "To Watch",
            "Watched",
            "Abandoned",
            "No Status"
        ]

        status = questionary.select(
            "Anime status:",
            choices=status_choices,
            default="No Status"
        ).ask()

        # Use the new add_anime method
        notion_service.add_anime(
            name=anime_name,
            icon_url=image,
            poster_url=image,
            release_year=release_year,
            status=status,
            studio=studio,
            episodes=episodes,
            seasons=seasons,
            airing_status=airing_status,
            synopsis=synopsis,
            mal_url=mal_url,
            anidb_url=None  # AniDB URL not available from Jikan API
        )

        console.print(f"[green]✓ Added [bold]{anime_name}[/bold] to Notion database[/green]")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")

def settings_menu(config_manager):
    """Handle the settings menu."""
    console.print(Panel.fit(
        "[bold]Settings[/bold]",
        border_style="magenta"
    ))

    # Load current config
    config = config_manager.load_config()

    # Update settings
    anime_db = questionary.text(
        "Anime Notion Database ID (or full URL):",
        default=config.get('anime_database_id', '')
    ).ask()

    notion_token = questionary.text(
        "Notion Integration Secret:",
        default=config.get('notion_token', '')
    ).ask()

    # Save new settings
    new_config = config.copy()  # Keep existing settings
    new_config.update({
        'anime_database_id': anime_db,
        'notion_token': notion_token
    })

    config_manager.save_config(new_config)
    console.print("[green]Settings saved successfully![/green]")

    # Return True if config is complete for anime
    return config_manager.is_config_complete(config_type='anime')

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Program interrupted.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Unexpected error: {str(e)}[/red]")
        sys.exit(1)
