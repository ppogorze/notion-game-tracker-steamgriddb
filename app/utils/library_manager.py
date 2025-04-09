"""
Library Manager - Handles the game library management UI
"""

import sys
import questionary
from rich.console import Console
from rich.panel import Panel

console = Console()

def library_menu(notion_service, steam_service=None):
    """
    Handle the game library management menu.
    
    Args:
        notion_service: The Notion service
        steam_service: Optional SteamGridDB service for updating game assets
    
    Returns:
        None
    """
    console.print(Panel.fit(
        "[bold cyan]Game Library Management[/bold cyan]",
        border_style="cyan"
    ))
    
    while True:
        choice = questionary.select(
            "Library options:",
            choices=[
                "List All Games",
                "Search Games",
                "Edit Game",
                "Delete Game",
                "Back to Main Menu"
            ]
        ).ask()
        
        if choice == "List All Games":
            list_all_games(notion_service)
        elif choice == "Search Games":
            search_games(notion_service)
        elif choice == "Edit Game":
            edit_game(notion_service, steam_service)
        elif choice == "Delete Game":
            delete_game(notion_service)
        elif choice == "Back to Main Menu":
            return

def list_all_games(notion_service, start_cursor=None, page_size=10):
    """
    List all games in the library with pagination.
    
    Args:
        notion_service: The Notion service
        start_cursor: Pagination cursor
        page_size: Number of games per page
    
    Returns:
        None
    """
    try:
        # Get games from Notion
        games, next_cursor = notion_service.list_games(limit=page_size, start_cursor=start_cursor)
        
        if not games:
            console.print("[yellow]No games found in your library.[/yellow]")
            return
        
        # Format and display the games table
        table = notion_service.format_games_table(games)
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
        console.print(f"[red]Error listing games: {str(e)}[/red]")

def search_games(notion_service):
    """
    Search for games by name.
    
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
        # Search for games
        games = notion_service.search_games(query)
        
        if not games:
            console.print(f"[yellow]No games found matching '{query}'.[/yellow]")
            return
        
        # Format and display the games table
        table = notion_service.format_games_table(games)
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
            # Convert games list to dictionary for easy lookup
            games_dict = {game.get("properties", {}).get("name", f"Unknown Game {i}"): game 
                         for i, game in enumerate(games)}
            
            # Let user select a game
            game_names = list(games_dict.keys())
            game_names.append("Cancel")
            
            selected = questionary.select(
                "Select a game to edit:",
                choices=game_names
            ).ask()
            
            if selected != "Cancel":
                selected_game = games_dict[selected]
                edit_specific_game(notion_service, selected_game)
        
        elif action_choice == "Delete a Game":
            # Convert games list to dictionary for easy lookup
            games_dict = {game.get("properties", {}).get("name", f"Unknown Game {i}"): game 
                         for i, game in enumerate(games)}
            
            # Let user select a game
            game_names = list(games_dict.keys())
            game_names.append("Cancel")
            
            selected = questionary.select(
                "Select a game to delete:",
                choices=game_names
            ).ask()
            
            if selected != "Cancel":
                selected_game = games_dict[selected]
                delete_specific_game(notion_service, selected_game)
    
    except Exception as e:
        console.print(f"[red]Error searching games: {str(e)}[/red]")

def edit_game(notion_service, steam_service=None):
    """
    Edit a game in the library.
    
    Args:
        notion_service: The Notion service
        steam_service: Optional SteamGridDB service for updating game assets
    
    Returns:
        None
    """
    try:
        # Get first page of games
        games, _ = notion_service.list_games(limit=50)
        
        if not games:
            console.print("[yellow]No games found in your library.[/yellow]")
            return
        
        # Convert games list to dictionary for easy lookup
        games_dict = {game.get("properties", {}).get("name", f"Unknown Game {i}"): game 
                     for i, game in enumerate(games)}
        
        # Let user select a game
        game_names = list(games_dict.keys())
        game_names.append("Cancel")
        
        selected = questionary.select(
            "Select a game to edit:",
            choices=game_names
        ).ask()
        
        if selected == "Cancel":
            return
        
        selected_game = games_dict[selected]
        edit_specific_game(notion_service, selected_game, steam_service)
    
    except Exception as e:
        console.print(f"[red]Error editing game: {str(e)}[/red]")

def edit_specific_game(notion_service, game, steam_service=None):
    """
    Edit a specific game.
    
    Args:
        notion_service: The Notion service
        game: The game data to edit
        steam_service: Optional SteamGridDB service for updating game assets
    
    Returns:
        None
    """
    game_id = game.get("id")
    props = game.get("properties", {})
    current_name = props.get("name", "Unknown")
    current_year = props.get("release_year")
    
    # Ask for new values
    new_name = questionary.text(
        "Game name:",
        default=current_name
    ).ask()
    
    new_year_str = questionary.text(
        "Release year:",
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
    status_choices = [
        "Chcę zagrać",
        "Przestałem grać",
        "W trakcie",
        "Ukończone",
        "No Status"
    ]
    
    new_status = questionary.select(
        "Game status:",
        choices=status_choices,
        default=current_status if current_status in status_choices else "No Status"
    ).ask()
    
    # Get current platform and prompt for new platform
    current_platform = props.get("platform", "PC")
    platform_choices = [
        "PC",
        "PS4",
        "PS5",
        "Switch"
    ]
    
    new_platform = questionary.select(
        "Game platform:",
        choices=platform_choices,
        default=current_platform if current_platform in platform_choices else "PC"
    ).ask()
    
    # Determine what has changed
    name_changed = new_name and new_name != current_name
    year_changed = new_year and new_year != current_year
    status_changed = new_status != current_status
    platform_changed = new_platform != current_platform
    
    # Update game icon and poster
    update_assets = False
    new_icon = None
    new_poster = None
    
    if steam_service and questionary.confirm("Update game assets (icon and poster)?").ask():
        update_assets = True
        
        # Search for the game on SteamGridDB
        console.print(f"[cyan]Searching for [bold]{new_name}[/bold] on SteamGridDB...[/cyan]")
        search_results = steam_service.search_game(new_name)
        
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
                    new_icon = steam_service.get_game_icon(game_id_sgdb)
                    new_poster = steam_service.get_game_poster(game_id_sgdb)
                    
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
    
    # Update the game if anything has changed
    if name_changed or year_changed or status_changed or platform_changed or update_assets:
        console.print("[cyan]Updating game in Notion...[/cyan]")
        
        success = notion_service.update_game(
            page_id=game_id,
            name=new_name if name_changed else None,
            release_year=new_year if year_changed else None,
            status=new_status if status_changed else None,
            platform=new_platform if platform_changed else None,
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
    Delete a game from the library.
    
    Args:
        notion_service: The Notion service
    
    Returns:
        None
    """
    try:
        # Get first page of games
        games, _ = notion_service.list_games(limit=50)
        
        if not games:
            console.print("[yellow]No games found in your library.[/yellow]")
            return
        
        # Convert games list to dictionary for easy lookup
        games_dict = {game.get("properties", {}).get("name", f"Unknown Game {i}"): game 
                     for i, game in enumerate(games)}
        
        # Let user select a game
        game_names = list(games_dict.keys())
        game_names.append("Cancel")
        
        selected = questionary.select(
            "Select a game to delete:",
            choices=game_names
        ).ask()
        
        if selected == "Cancel":
            return
        
        selected_game = games_dict[selected]
        delete_specific_game(notion_service, selected_game)
    
    except Exception as e:
        console.print(f"[red]Error deleting game: {str(e)}[/red]")

def delete_specific_game(notion_service, game):
    """
    Delete a specific game.
    
    Args:
        notion_service: The Notion service
        game: The game data to delete
    
    Returns:
        None
    """
    game_id = game.get("id")
    name = game.get("properties", {}).get("name", "Unknown")
    
    # Confirm deletion
    confirmed = questionary.confirm(
        f"Are you sure you want to delete '{name}'? This action cannot be undone."
    ).ask()
    
    if not confirmed:
        console.print("[yellow]Deletion cancelled.[/yellow]")
        return
    
    # Delete the game
    success = notion_service.delete_game(game_id)
    
    if success:
        console.print(f"[green]✓ Deleted [bold]{name}[/bold][/green]")
    else:
        console.print(f"[red]Failed to delete [bold]{name}[/bold][/red]")
