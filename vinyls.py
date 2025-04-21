#!/usr/bin/env python3
"""
Vinyl Collection Manager CLI

This application helps you manage your vinyl collection by:
1. Searching for vinyl records on Discogs
2. Adding them to your Notion database
"""

import sys
import questionary
from rich.console import Console
from rich.panel import Panel

from app.services.discogs import DiscogsService
from app.services.notion import NotionService
from app.utils.config_manager import ConfigManager
from app.utils.library_manager import library_menu

# Import ConfigManager for use in NotionService initialization
from app.utils.config_manager import ConfigManager

console = Console()

def main():
    """
    Main function to run the vinyl collection manager.
    """
    # Display welcome message
    console.print(Panel.fit(
        "[bold blue]Vinyl Collection Manager[/bold blue]\n"
        "Manage your vinyl collection with Notion",
        border_style="blue"
    ))

    # Initialize config manager
    config_manager = ConfigManager()

    # Check if config exists, if not, prompt for setup
    config = config_manager.load_config()
    if not config:
        console.print("[yellow]No configuration found. Let's set up your Notion integration.[/yellow]")
        setup_config(config_manager)

    # Initialize services with config
    # Reload config to ensure we have the latest values
    config = config_manager.load_config()

    # Initialize services with config
    discogs_token = config.get('discogs_token', '')
    notion_token = config.get('notion_token', '')
    vinyls_database_id = config.get('vinyls_database_id', '')

    vinyls_service = DiscogsService(token=discogs_token)
    notion_service = NotionService(notion_token, vinyls_database_id)

    # Main menu
    while True:
        choice = questionary.select(
            "What would you like to do?",
            choices=[
                "Add vinyl to collection",
                "View collection",
                "Configure settings",
                "Exit"
            ]
        ).ask()

        if choice == "Add vinyl to collection":
            add_vinyl(vinyls_service, notion_service)
        elif choice == "View collection":
            library_menu(notion_service, "vinyl")
        elif choice == "Configure settings":
            configure_settings(config_manager, vinyls_service, notion_service)
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

    # Prompt for Notion database ID
    vinyls_database_id = questionary.text(
        "Enter your Notion vinyls database ID or URL:",
        validate=lambda text: len(text) > 0 or "Database ID cannot be empty"
    ).ask()

    # Prompt for Discogs token (optional)
    discogs_token = questionary.text(
        "Enter your Discogs API token (optional):"
    ).ask()

    # Save configuration
    config = {
        'notion_token': notion_token,
        'vinyls_database_id': vinyls_database_id
    }

    if discogs_token:
        config['discogs_token'] = discogs_token

    config_manager.save_config(config)
    console.print("[green]Configuration saved successfully![/green]")

def configure_settings(config_manager, vinyls_service, notion_service):
    """
    Configure application settings.

    Args:
        config_manager (ConfigManager): The configuration manager
        vinyls_service (DiscogsService): The Discogs service
        notion_service (NotionService): The Notion service
    """
    # Load current config
    config = config_manager.load_config()

    # Show current settings
    console.print("\n[bold]Current Settings:[/bold]")
    console.print(f"Notion Token: {'*' * 10}{config.get('notion_token', '')[-4:] if config.get('notion_token') else 'Not set'}")
    console.print(f"Vinyls Database ID: {config.get('vinyls_database_id', 'Not set')}")
    console.print(f"Discogs Token: {'*' * 10}{config.get('discogs_token', '')[-4:] if config.get('discogs_token') else 'Not set'}")

    # Prompt for settings to change
    setting_to_change = questionary.select(
        "Which setting would you like to change?",
        choices=[
            "Notion Token",
            "Vinyls Database ID",
            "Discogs Token",
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

    elif setting_to_change == "Vinyls Database ID":
        new_value = questionary.text(
            "Enter new Vinyls database ID or URL:",
            validate=lambda text: len(text) > 0 or "Database ID cannot be empty"
        ).ask()
        config['vinyls_database_id'] = new_value

    elif setting_to_change == "Discogs Token":
        new_value = questionary.text(
            "Enter new Discogs token (leave empty to remove):"
        ).ask()
        if new_value:
            config['discogs_token'] = new_value
        else:
            config.pop('discogs_token', None)

    # Save updated config
    config_manager.save_config(config)
    console.print("[green]Configuration updated successfully![/green]")

    # Reinitialize services with new config
    discogs_token = config.get('discogs_token', '')
    notion_token = config.get('notion_token', '')
    vinyls_database_id = config.get('vinyls_database_id', '')

    vinyls_service.__init__(token=discogs_token)
    notion_service.__init__(notion_token, vinyls_database_id)

def add_vinyl(vinyls_service, notion_service):
    """
    Search for and add a vinyl to the Notion database.

    Args:
        vinyls_service (DiscogsService): The Discogs service
        notion_service (NotionService): The Notion service
    """
    # Choose search type
    search_type = questionary.select(
        "Search by:",
        choices=[
            "Title",
            "Artist",
            "Label",
            "Any"
        ],
        default="Any"
    ).ask()

    # Get search query from user
    query_prompt = f"Enter vinyl {search_type.lower()}:"
    query = questionary.text(query_prompt).ask()

    # Map UI search type to API search type
    search_type_map = {
        "Title": "title",
        "Artist": "artist",
        "Label": "label",
        "Any": "all"
    }

    # Search for the vinyl on Discogs
    console.print(f"[blue]Searching for [bold]{query}[/bold] on Discogs...[/blue]")

    try:
        search_results = vinyls_service.search_vinyl(
            query,
            search_type=search_type_map[search_type]
        )

        if not search_results:
            console.print(f"[yellow]No vinyl records found matching that {search_type.lower()}.[/yellow]")
            return

        # Let user select from matching results
        vinyl_choices = []
        for vinyl in search_results:
            # Format the vinyl information for display
            artist = vinyl.get('artist', 'Unknown')
            album = vinyl.get('album', 'Unknown')
            year = vinyl.get('year', 'Unknown')

            vinyl_choices.append(f"{artist} - {album} ({year})")
        vinyl_choices.append("Cancel")

        selected = questionary.select(
            "Select a vinyl:",
            choices=vinyl_choices
        ).ask()

        if selected == "Cancel":
            return

        # Find the selected vinyl in the results
        selected_index = vinyl_choices.index(selected)
        selected_vinyl = search_results[selected_index]

        # Get detailed vinyl information
        console.print("[blue]Retrieving detailed vinyl information...[/blue]")
        vinyl_details = vinyls_service.get_vinyl_details(selected_vinyl['id'])

        if not vinyl_details:
            console.print("[yellow]Could not retrieve detailed information for this vinyl.[/yellow]")
            return

        # Extract information from the details
        title = vinyl_details.get('album')
        artist = vinyl_details.get('artist', [])
        cover_url = vinyl_details.get('cover_url')
        release_year = vinyl_details.get('year')
        label = vinyl_details.get('label', [])
        format_type_str = ", ".join(vinyl_details.get('format', []))
        genre = vinyl_details.get('genre', [])
        country = vinyl_details.get('country')
        tracklist = vinyl_details.get('tracklist', [])
        notes = vinyl_details.get('notes')
        info_link = vinyl_details.get('resource_url')

        # Display detailed vinyl information
        console.print(f"[green]Selected: [bold]{title}[/bold][/green]")
        console.print(f"[cyan]Artist:[/cyan] {', '.join(artist)}")
        if release_year:
            console.print(f"[cyan]Released:[/cyan] {release_year}")
        if label:
            console.print(f"[cyan]Label:[/cyan] {', '.join(label)}")
        if format_type_str:
            console.print(f"[cyan]Format:[/cyan] {format_type_str}")
        if genre:
            console.print(f"[cyan]Genre:[/cyan] {', '.join(genre)}")
        if country:
            console.print(f"[cyan]Country:[/cyan] {country}")

        # Show a preview of the tracklist if available
        if tracklist:
            console.print("[cyan]Tracklist:[/cyan]")
            for track in tracklist[:5]:  # Show first 5 tracks
                position = track.get("position", "")
                track_title = track.get("title", "")
                duration = track.get("duration", "")
                console.print(f"  {position}. {track_title} ({duration})")

            if len(tracklist) > 5:
                console.print(f"  ... and {len(tracklist) - 5} more tracks")

        # Show a preview of the notes if available
        if notes:
            # Truncate notes if it's too long
            max_notes_length = 200
            short_notes = notes[:max_notes_length] + "..." if len(notes) > max_notes_length else notes
            console.print(f"[cyan]Notes:[/cyan] {short_notes}")

        # Prompt for vinyl status
        status_choices = [
            "In Collection",
            "Wishlist",
            "Sold",
            "No Status"
        ]

        status = questionary.select(
            "Vinyl status:",
            choices=status_choices,
            default="In Collection"
        ).ask()

        # Add to Notion
        console.print("[blue]Adding vinyl to Notion...[/blue]")

        try:
            notion_service.add_vinyl(
                title=title,
                artist=artist,
                icon_url=None,  # Vinyl records typically don't have icons
                poster_url=cover_url,
                release_year=release_year,
                status=status,
                format_type=format_type_str,
                label=label,
                genre=genre,
                tracklist=tracklist,
                notes=notes,
                country=country,
                info_link=info_link
            )

            console.print(f"[green]✓ Added [bold]{title}[/bold] to Notion database[/green]")
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")

if __name__ == "__main__":
    main()
