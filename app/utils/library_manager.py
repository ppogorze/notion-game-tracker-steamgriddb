"""
Library Manager - Handles the library management UI for games, anime, books, and vinyls
"""

import questionary
from rich.console import Console
from rich.panel import Panel

console = Console()

def library_menu(notion_service, media_service=None):
    """
    Handle the library management menu for games, anime, or books.

    Args:
        notion_service: The Notion service
        media_service: Optional service for the specific media type (SteamGridDB, Jikan, GoogleBooks)

    Returns:
        None
    """
    # Determine the media type based on the service provided or parameter
    media_type = "Game"
    border_color = "cyan"

    if media_service == "vinyl":
        media_type = "Vinyl"
        border_color = "green"
    elif hasattr(media_service, 'search_anime'):
        media_type = "Anime"
        border_color = "magenta"
    elif hasattr(media_service, 'search_book'):
        media_type = "Book"
        border_color = "blue"
    elif hasattr(media_service, 'search_vinyl'):
        media_type = "Vinyl"
        border_color = "green"

    console.print(Panel.fit(
        f"[bold {border_color}]{media_type} Library Management[/bold {border_color}]",
        border_style=border_color
    ))

    while True:
        choice = questionary.select(
            "Library options:",
            choices=[
                f"List All {media_type}s",
                f"Search {media_type}s",
                f"Edit {media_type}",
                f"Delete {media_type}",
                "Back to Main Menu"
            ]
        ).ask()

        if choice.startswith("List All"):
            list_all_games(notion_service)
        elif choice.startswith("Search"):
            search_games(notion_service)
        elif choice.startswith("Edit"):
            edit_game(notion_service, media_service)
        elif choice.startswith("Delete"):
            delete_game(notion_service)
        elif choice == "Back to Main Menu":
            return

def list_all_games(notion_service, start_cursor=None, page_size=10):
    """
    List all items in the library with pagination.

    Args:
        notion_service: The Notion service
        start_cursor: Pagination cursor
        page_size: Number of items per page

    Returns:
        None
    """
    try:
        # Get items from Notion
        items, next_cursor = notion_service.list_games(limit=page_size, start_cursor=start_cursor)

        # Determine the media type based on the service
        media_type = "games"
        if hasattr(notion_service, 'anime_database_id') and notion_service.database_id == notion_service.anime_database_id:
            media_type = "anime"
        elif hasattr(notion_service, 'books_database_id') and notion_service.database_id == notion_service.books_database_id:
            media_type = "books"
        elif hasattr(notion_service, 'vinyls_database_id') and notion_service.database_id == notion_service.vinyls_database_id:
            media_type = "vinyls"

        if not items:
            console.print(f"[yellow]No {media_type} found in your library.[/yellow]")
            return

        # Format and display the items table
        table = notion_service.format_games_table(items)
        console.print(table)

        # Pagination controls
        pagination_choices = ["Back to Library Menu"]

        if next_cursor:
            pagination_choices.insert(0, "Next Page")

        if start_cursor:
            pagination_choices.insert(0, "Previous Page")

        pagination_choice = questionary.select(
            "Options:",
            choices=pagination_choices
        ).ask()

        if pagination_choice == "Next Page":
            list_all_games(notion_service, start_cursor=next_cursor, page_size=page_size)
        elif pagination_choice == "Previous Page":
            # We don't actually store previous cursors, so we start over and page through
            # This is a limitation of the Notion API
            console.print("[yellow]Returning to first page...[/yellow]")
            list_all_games(notion_service, page_size=page_size)

    except Exception as e:
        console.print(f"[red]Error listing items: {str(e)}[/red]")

def search_games(notion_service):
    """
    Search for items by name.

    Args:
        notion_service: The Notion service

    Returns:
        None
    """
    # Get search query from user
    query = questionary.text("Enter search query:").ask()

    if not query:
        console.print("[yellow]Search query cannot be empty.[/yellow]")
        return

    try:
        # Determine the media type based on the service
        media_type = "games"
        if hasattr(notion_service, 'anime_database_id') and notion_service.database_id == notion_service.anime_database_id:
            media_type = "anime"
        elif hasattr(notion_service, 'books_database_id') and notion_service.database_id == notion_service.books_database_id:
            media_type = "books"
        elif hasattr(notion_service, 'vinyls_database_id') and notion_service.database_id == notion_service.vinyls_database_id:
            media_type = "vinyls"

        # Search for items
        items = notion_service.search_games(query)

        if not items:
            console.print(f"[yellow]No {media_type} found matching '{query}'.[/yellow]")
            return

        # Format and display the items table
        table = notion_service.format_games_table(items)
        console.print(table)

        # Ask if user wants to take action on a search result
        action_choice = questionary.select(
            "Would you like to:",
            choices=[
                "Edit a Game",
                "Delete a Game",
                "Back to Library Menu"
            ]
        ).ask()

        if action_choice == "Edit a Game":
            # Convert items list to dictionary for easy lookup
            items_dict = {item.get("properties", {}).get("name", f"Unknown Item {i}"): item
                         for i, item in enumerate(items)}

            # Let user select an item
            item_names = list(items_dict.keys())
            item_names.append("Cancel")

            selected = questionary.select(
                "Select an item to edit:",
                choices=item_names
            ).ask()

            if selected != "Cancel":
                selected_item = items_dict[selected]
                edit_specific_game(notion_service, selected_item)

        elif action_choice == "Delete a Game":
            # Convert items list to dictionary for easy lookup
            items_dict = {item.get("properties", {}).get("name", f"Unknown Item {i}"): item
                         for i, item in enumerate(items)}

            # Let user select an item
            item_names = list(items_dict.keys())
            item_names.append("Cancel")

            selected = questionary.select(
                "Select an item to delete:",
                choices=item_names
            ).ask()

            if selected != "Cancel":
                selected_item = items_dict[selected]
                delete_specific_game(notion_service, selected_item)

    except Exception as e:
        console.print(f"[red]Error searching: {str(e)}[/red]")

def edit_game(notion_service, media_service=None):
    """
    Edit an item in the library.

    Args:
        notion_service: The Notion service
        media_service: Optional service for the specific media type

    Returns:
        None
    """
    try:
        # Determine the media type based on the service
        media_type = "game"
        if media_service == "vinyl":
            media_type = "vinyl"
        elif hasattr(media_service, 'search_anime'):
            media_type = "anime"
        elif hasattr(media_service, 'search_book'):
            media_type = "book"
        elif hasattr(media_service, 'search_vinyl'):
            media_type = "vinyl"

        # Get first page of items
        items, _ = notion_service.list_games(limit=50)

        if not items:
            console.print(f"[yellow]No {media_type}s found in your library.[/yellow]")
            return

        # Convert items list to dictionary for easy lookup
        items_dict = {item.get("properties", {}).get("name", f"Unknown {media_type.capitalize()} {i}"): item
                     for i, item in enumerate(items)}

        # Let user select an item
        item_names = list(items_dict.keys())
        item_names.append("Cancel")

        selected = questionary.select(
            f"Select a {media_type} to edit:",
            choices=item_names
        ).ask()

        if selected == "Cancel":
            return

        selected_item = items_dict[selected]
        edit_specific_game(notion_service, selected_item, media_service)

    except Exception as e:
        console.print(f"[red]Error editing item: {str(e)}[/red]")

def edit_specific_game(notion_service, item, media_service=None):
    """
    Edit a specific item (game, anime, or book).

    Args:
        notion_service: The Notion service
        item: The item data to edit
        media_service: Optional service for the specific media type

    Returns:
        None
    """
    item_id = item.get("id")
    props = item.get("properties", {})
    current_name = props.get("name", "Unknown")
    current_year = props.get("release_year")

    # Determine the media type based on the service
    media_type = "Game"
    if media_service == "vinyl":
        media_type = "Vinyl"
    elif hasattr(media_service, 'search_anime'):
        media_type = "Anime"
    elif hasattr(media_service, 'search_book'):
        media_type = "Book"
    elif hasattr(media_service, 'search_vinyl'):
        media_type = "Vinyl"

    # Ask for new values
    new_name = questionary.text(
        f"{media_type} name:",
        default=current_name
    ).ask()

    year_label = "Release year" if media_type != "Vinyl" else "Release year"
    new_year_str = questionary.text(
        f"{year_label}:",
        default=str(current_year) if current_year else ""
    ).ask()

    # Convert year to integer
    new_year = None
    if new_year_str:
        try:
            new_year = int(new_year_str)
        except ValueError:
            console.print("[yellow]Invalid year format, skipping year update.[/yellow]")

    # Get current status and prompt for new status
    current_status = props.get("status", "")

    # Different status choices based on media type
    if media_type == "Vinyl":
        status_choices = [
            "In Collection",
            "Wishlist",
            "Sold",
            "No Status"
        ]
    elif media_type == "Anime":
        status_choices = [
            "Watching",
            "To Watch",
            "Watched",
            "Abandoned",
            "No Status"
        ]
    elif media_type == "Book":
        status_choices = [
            "Reading",
            "To Read",
            "Read",
            "Abandoned",
            "No Status"
        ]
    else:  # Default for games
        status_choices = [
            "Chcę zagrać",
            "Przestałem grać",
            "W trakcie",
            "Ukończone",
            "No Status"
        ]

    new_status = questionary.select(
        f"{media_type} status:",
        choices=status_choices,
        default=current_status if current_status in status_choices else "No Status"
    ).ask()

    # Get current platform/format and prompt for new value
    if media_type == "Vinyl":
        current_format = props.get("format", "")
        format_choices = [
            "LP",
            "EP",
            "Single",
            "Album",
            "Compilation",
            "Box Set",
            "Other"
        ]

        new_format = questionary.select(
            "Format:",
            choices=format_choices,
            default=current_format if current_format in format_choices else "LP"
        ).ask()
        new_platform = None  # Not used for vinyls
    else:
        # For games, anime, books
        current_platform = props.get("platform", "PC")
        platform_choices = [
            "PC",
            "PS4",
            "PS5",
            "Switch"
        ]

        new_platform = questionary.select(
            f"{media_type} platform:",
            choices=platform_choices,
            default=current_platform if current_platform in platform_choices else "PC"
        ).ask()
        new_format = None  # Not used for games, anime, books

    # Determine what has changed
    name_changed = new_name and new_name != current_name
    year_changed = new_year and new_year != current_year
    status_changed = new_status != current_status

    if media_type == "Vinyl":
        format_changed = new_format != current_format
        platform_changed = False  # Not used for vinyls
    else:
        platform_changed = new_platform != current_platform
        format_changed = False  # Not used for games, anime, books

    # Determine if we can update assets based on the media service type
    update_assets = False
    new_icon = None
    new_poster = None

    # Only offer asset updates for games (SteamGridDB service)
    if hasattr(media_service, 'search_game') and hasattr(media_service, 'get_game_icon'):
        if questionary.confirm("Update game assets (icon and poster)?").ask():
            update_assets = True

            # Search for the game on SteamGridDB
            console.print(f"[cyan]Searching for [bold]{new_name}[/bold] on SteamGridDB...[/cyan]")
            search_results = media_service.search_game(new_name)

            if search_results:
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
                    "Select a game for assets:",
                    choices=game_choices
                ).ask()

                if selected != "Cancel":
                    # Find the selected game in the results
                    selected_index = game_choices.index(selected)
                    selected_game = search_results[selected_index]

                    # Get the game ID based on the response format
                    if 'name' in selected_game:
                        game_id_sgdb = selected_game['id']
                    elif 'text' in selected_game:
                        game_id_sgdb = selected_game['id']
                    else:
                        console.print("[yellow]Invalid game data format, skipping asset update.[/yellow]")
                        update_assets = False

                    if update_assets:
                        # Get game assets
                        console.print("[cyan]Retrieving game assets...[/cyan]")
                        new_icon = media_service.get_game_icon(game_id_sgdb)
                        new_poster = media_service.get_game_poster(game_id_sgdb)

                        # Try to extract release year from the selected game
                        new_year = None
                        for key in ['release', 'release_date']:
                            if key in selected_game:
                                try:
                                    # First try direct conversion
                                    release_timestamp = int(selected_game[key])
                                    from datetime import datetime
                                    new_year = datetime.fromtimestamp(release_timestamp).year
                                    break
                                except (ValueError, TypeError):
                                    # If direct conversion fails, try to extract timestamp from string
                                    try:
                                        # Selected text may include timestamp in the format "Game Name (1632182400)"
                                        if isinstance(selected, str) and '(' in selected and ')' in selected:
                                            # Extract the number between parentheses
                                            timestamp_part = selected.split('(')[1].split(')')[0]
                                            if timestamp_part.isdigit():
                                                from datetime import datetime
                                                release_timestamp = int(timestamp_part)
                                                new_year = datetime.fromtimestamp(release_timestamp).year
                                                break
                                    except Exception:
                                        # If all extraction attempts fail, just use the existing release year
                                        pass

                        # If we found a new year from the assets, update it
                        if new_year:
                            console.print(f"[cyan]Found release year: [bold]{new_year}[/bold][/cyan]")
            else:
                console.print("[yellow]No games found on SteamGridDB. Assets won't be updated.[/yellow]")
                update_assets = False

    # Update the item if anything has changed
    if name_changed or year_changed or status_changed or platform_changed or format_changed or update_assets:
        console.print("[cyan]Updating game in Notion...[/cyan]")

        if media_type == "Vinyl":
            success = notion_service.update_game(
                page_id=item_id,
                name=new_name if name_changed else None,
                release_year=new_year if year_changed else None,
                status=new_status if status_changed else None,
                format_type=new_format if format_changed else None,  # Use format for vinyls
                icon_url=new_icon,
                poster_url=new_poster
            )
        else:
            success = notion_service.update_game(
                page_id=item_id,
                name=new_name if name_changed else None,
                release_year=new_year if year_changed else None,
                status=new_status if status_changed else None,
                platform=new_platform if platform_changed else None,  # Use platform for games, anime, books
                icon_url=new_icon,
                poster_url=new_poster
            )

        if success:
            console.print(f"[green]✓ Updated [bold]{new_name if name_changed else current_name}[/bold][/green]")
        else:
            console.print("[red]Failed to update game.[/red]")
    else:
        console.print("[yellow]No changes made.[/yellow]")

def delete_game(notion_service):
    """
    Delete an item from the library.

    Args:
        notion_service: The Notion service

    Returns:
        None
    """
    try:
        # Determine the media type based on the service
        media_type = "game"
        if hasattr(notion_service, 'anime_database_id') and notion_service.database_id == notion_service.anime_database_id:
            media_type = "anime"
        elif hasattr(notion_service, 'books_database_id') and notion_service.database_id == notion_service.books_database_id:
            media_type = "book"
        elif hasattr(notion_service, 'vinyls_database_id') and notion_service.database_id == notion_service.vinyls_database_id:
            media_type = "vinyl"

        # Get first page of items
        items, _ = notion_service.list_games(limit=50)

        if not items:
            console.print(f"[yellow]No {media_type}s found in your library.[/yellow]")
            return

        # Convert items list to dictionary for easy lookup
        items_dict = {item.get("properties", {}).get("name", f"Unknown {media_type.capitalize()} {i}"): item
                     for i, item in enumerate(items)}

        # Let user select an item
        item_names = list(items_dict.keys())
        item_names.append("Cancel")

        selected = questionary.select(
            f"Select a {media_type} to delete:",
            choices=item_names
        ).ask()

        if selected == "Cancel":
            return

        selected_item = items_dict[selected]
        delete_specific_game(notion_service, selected_item)

    except Exception as e:
        console.print(f"[red]Error deleting item: {str(e)}[/red]")

def delete_specific_game(notion_service, item):
    """
    Delete a specific item (game, anime, or book).

    Args:
        notion_service: The Notion service
        item: The item data to delete

    Returns:
        None
    """
    item_id = item.get("id")
    name = item.get("properties", {}).get("name", "Unknown")

    # Confirm deletion
    confirmed = questionary.confirm(
        f"Are you sure you want to delete '{name}'? This action cannot be undone."
    ).ask()

    if not confirmed:
        console.print("[yellow]Deletion cancelled.[/yellow]")
        return

    # Delete the item
    success = notion_service.delete_game(item_id)

    if success:
        console.print(f"[green]✓ Deleted [bold]{name}[/bold][/green]")
    else:
        console.print(f"[red]Failed to delete [bold]{name}[/bold][/red]")
