"""
Notion Service - Handles interaction with the Notion API
"""

import re
import requests
from urllib.parse import urlparse
from notion_client import Client
from rich.console import Console
from rich.table import Table
from datetime import datetime

console = Console()

class NotionService:
    """
    Service for interacting with the Notion API.
    
    Provides methods for adding games to a Notion database.
    """
    
    def __init__(self, token, database_id):
        """
        Initialize the Notion service.
        
        Args:
            token (str): Notion API token (integration secret)
            database_id (str): Notion database ID
        """
        self.token = token
        self.database_id = self._clean_database_id(database_id)
        
        if token:
            self.client = Client(auth=token)
        else:
            self.client = None
    
    def _clean_database_id(self, database_id):
        """
        Extract and clean the database ID from a URL or direct ID.
        
        Args:
            database_id (str): Notion database URL or ID
            
        Returns:
            str: Cleaned database ID
        """
        if not database_id:
            return None
            
        # If it's a URL, extract the ID
        if database_id.startswith('https://'):
            # Parse the URL
            parsed_url = urlparse(database_id)
            path = parsed_url.path
            
            # Extract the ID from the path
            # URL format: https://www.notion.so/{workspace}/{database_id}
            # or https://www.notion.so/{workspace}/{page_title}-{database_id}
            path_parts = path.rstrip('/').split('/')
            last_part = path_parts[-1]
            
            # Check if the ID is embedded in the last part with a title
            if '-' in last_part:
                # Extract the ID after the last dash
                id_parts = last_part.split('-')
                database_id = id_parts[-1]
            else:
                # The ID is the whole last part
                database_id = last_part
        
        # Remove any dashes from the ID
        database_id = database_id.replace('-', '')
        
        # Notion IDs are 32 characters long
        if len(database_id) > 32:
            database_id = database_id[:32]
        
        return database_id
    
    def list_games(self, limit=100, start_cursor=None, sort_by=None):
        """
        Get a list of games from the Notion database.
        
        Args:
            limit (int): Maximum number of games to return
            start_cursor (str, optional): Pagination cursor
            sort_by (dict, optional): Sorting criteria
            
        Returns:
            tuple: (list of games, next_cursor) - The list of games and cursor for pagination
        """
        if not self.client or not self.database_id:
            raise ValueError("Notion token or database ID is not set")
        
        try:
            # Prepare query parameters
            params = {
                "database_id": self.database_id,
                "page_size": limit
            }
            
            # Add start cursor if provided (for pagination)
            if start_cursor:
                params["start_cursor"] = start_cursor
                
            # Add sorting if provided
            if sort_by:
                params["sorts"] = [sort_by]
            else:
                # Default sort by Name
                params["sorts"] = [{"property": "Name", "direction": "ascending"}]
            
            # Query the database
            response = self.client.databases.query(**params)
            
            # Process results
            games = []
            for page in response.get("results", []):
                # Extract game data
                game_data = {
                    "id": page["id"],
                    "url": page["url"],
                    "created_time": page.get("created_time"),
                    "last_edited_time": page.get("last_edited_time"),
                    "properties": {}
                }
                
                # Extract properties
                props = page.get("properties", {})
                
                # Name (title)
                if "Name" in props and props["Name"].get("title"):
                    title_parts = [
                        part.get("plain_text", "") 
                        for part in props["Name"].get("title", [])
                    ]
                    game_data["properties"]["name"] = "".join(title_parts)
                
                # Release year (Wydano)
                if "Wydano" in props and props["Wydano"].get("number") is not None:
                    game_data["properties"]["release_year"] = props["Wydano"].get("number")
                
                # Status (if available - multi-select field)
                if "Status" in props and props["Status"].get("multi_select"):
                    status_values = props["Status"]["multi_select"]
                    if status_values:
                        # Take the first status in the multi-select
                        game_data["properties"]["status"] = status_values[0].get("name", "")
                
                # Platform (if available - select field)
                if "Platforma" in props and props["Platforma"].get("select"):
                    platform_data = props["Platforma"]["select"]
                    if platform_data and "name" in platform_data:
                        game_data["properties"]["platform"] = platform_data["name"]
                
                # Get cover image if available
                if "cover" in page and page["cover"] and page["cover"].get("type") == "external":
                    game_data["cover_url"] = page["cover"]["external"]["url"]
                
                # Get icon if available
                if "icon" in page and page["icon"] and page["icon"].get("type") == "external":
                    game_data["icon_url"] = page["icon"]["external"]["url"]
                
                games.append(game_data)
            
            # Get next cursor for pagination
            next_cursor = response.get("next_cursor")
            
            return games, next_cursor
            
        except Exception as e:
            console.print(f"[red]Error listing games: {str(e)}[/red]")
            return [], None
    
    def get_game(self, page_id):
        """
        Get a single game by its page ID.
        
        Args:
            page_id (str): Notion page ID
            
        Returns:
            dict: Game data
        """
        if not self.client:
            raise ValueError("Notion token is not set")
        
        try:
            # Retrieve the page
            response = self.client.pages.retrieve(page_id=page_id)
            
            # Extract game data
            game_data = {
                "id": response["id"],
                "url": response["url"],
                "created_time": response.get("created_time"),
                "last_edited_time": response.get("last_edited_time"),
                "properties": {}
            }
            
            # Extract properties
            props = response.get("properties", {})
            
            # Name (title)
            if "Name" in props and props["Name"].get("title"):
                title_parts = [
                    part.get("plain_text", "") 
                    for part in props["Name"].get("title", [])
                ]
                game_data["properties"]["name"] = "".join(title_parts)
            
            # Release year (Wydano)
            if "Wydano" in props and props["Wydano"].get("number") is not None:
                game_data["properties"]["release_year"] = props["Wydano"].get("number")
            
            # Status (if available - multi-select field)
            if "Status" in props and props["Status"].get("multi_select"):
                status_values = props["Status"]["multi_select"]
                if status_values:
                    # Take the first status in the multi-select
                    game_data["properties"]["status"] = status_values[0].get("name", "")
            
            # Get cover image if available
            if "cover" in response and response["cover"] and response["cover"].get("type") == "external":
                game_data["cover_url"] = response["cover"]["external"]["url"]
            
            # Get icon if available
            if "icon" in response and response["icon"] and response["icon"].get("type") == "external":
                game_data["icon_url"] = response["icon"]["external"]["url"]
            
            return game_data
            
        except Exception as e:
            console.print(f"[red]Error retrieving game: {str(e)}[/red]")
            return None
    
    def update_game(self, page_id, name=None, release_year=None, icon_url=None, poster_url=None, status=None, platform=None):
        """
        Update an existing game in the Notion database.
        
        Args:
            page_id (str): Notion page ID
            name (str, optional): New game name
            release_year (int, optional): New release year
            icon_url (str, optional): New icon URL
            poster_url (str, optional): New poster URL
            status (str, optional): Game status (multi-select in Notion)
            platform (str, optional): Game platform (single-select in Notion)
            
        Returns:
            bool: True if updated successfully, False otherwise
        """
        if not self.client:
            raise ValueError("Notion token is not set")
        
        try:
            # Create update data
            update_data = {"page_id": page_id}
            
            # Add properties to update
            properties = {}
            
            # Update name if provided
            if name:
                properties["Name"] = {
                    "title": [
                        {
                            "text": {
                                "content": name
                            }
                        }
                    ]
                }
            
            # Update release year if provided
            if release_year:
                properties["Wydano"] = {
                    "number": release_year
                }
            
            # Update status if provided
            if status is not None:
                if status.lower() == "no status":
                    # Empty multi-select (clear status)
                    properties["Status"] = {
                        "multi_select": []
                    }
                else:
                    # Add single status as multi-select
                    properties["Status"] = {
                        "multi_select": [
                            {
                                "name": status
                            }
                        ]
                    }
            
            # Update platform if provided
            if platform is not None:
                properties["Platforma"] = {
                    "select": {
                        "name": platform
                    }
                }
            
            # Add properties to update data if any
            if properties:
                update_data["properties"] = properties
            
            # Update icon if provided
            if icon_url:
                update_data["icon"] = {
                    "type": "external",
                    "external": {
                        "url": icon_url
                    }
                }
            
            # Update cover if provided
            if poster_url:
                update_data["cover"] = {
                    "type": "external",
                    "external": {
                        "url": poster_url
                    }
                }
            
            # Update the page
            response = self.client.pages.update(**update_data)
            
            return "id" in response
        
        except Exception as e:
            console.print(f"[red]Error updating game: {str(e)}[/red]")
            return False
    
    def delete_game(self, page_id):
        """
        Delete a game from the Notion database by archiving it.
        
        Args:
            page_id (str): Notion page ID
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        if not self.client:
            raise ValueError("Notion token is not set")
        
        try:
            # Archive the page (Notion's way of deleting)
            response = self.client.pages.update(
                page_id=page_id,
                archived=True
            )
            
            return response.get("archived", False)
        
        except Exception as e:
            console.print(f"[red]Error deleting game: {str(e)}[/red]")
            return False
    
    def search_games(self, query):
        """
        Search for games in the database by name.
        
        Args:
            query (str): Search query
            
        Returns:
            list: List of matching games
        """
        if not self.client or not self.database_id:
            raise ValueError("Notion token or database ID is not set")
        
        try:
            # Prepare query parameters for database query
            params = {
                "database_id": self.database_id,
                "filter": {
                    "property": "Name",
                    "title": {
                        "contains": query
                    }
                }
            }
            
            # Query the database
            response = self.client.databases.query(**params)
            
            # Process results (similar to list_games)
            games = []
            for page in response.get("results", []):
                # Extract game data
                game_data = {
                    "id": page["id"],
                    "url": page["url"],
                    "properties": {}
                }
                
                # Extract properties
                props = page.get("properties", {})
                
                # Name (title)
                if "Name" in props and props["Name"].get("title"):
                    title_parts = [
                        part.get("plain_text", "") 
                        for part in props["Name"].get("title", [])
                    ]
                    game_data["properties"]["name"] = "".join(title_parts)
                
                # Release year (Wydano)
                if "Wydano" in props and props["Wydano"].get("number") is not None:
                    game_data["properties"]["release_year"] = props["Wydano"].get("number")
                
                # Status (if available - multi-select field)
                if "Status" in props and props["Status"].get("multi_select"):
                    status_values = props["Status"]["multi_select"]
                    if status_values:
                        # Take the first status in the multi-select
                        game_data["properties"]["status"] = status_values[0].get("name", "")
                
                # Platform (if available - select field)
                if "Platforma" in props and props["Platforma"].get("select"):
                    platform_data = props["Platforma"]["select"]
                    if platform_data and "name" in platform_data:
                        game_data["properties"]["platform"] = platform_data["name"]
                
                # Get cover image if available
                if "cover" in page and page["cover"] and page["cover"].get("type") == "external":
                    game_data["cover_url"] = page["cover"]["external"]["url"]
                
                games.append(game_data)
            
            return games
            
        except Exception as e:
            console.print(f"[red]Error searching games: {str(e)}[/red]")
            return []
    
    def format_games_table(self, games):
        """
        Format a list of games as a rich table.
        
        Args:
            games (list): List of game data
            
        Returns:
            Table: Formatted rich table
        """
        # Create a table
        table = Table(title="Game Library")
        
        # Add columns
        table.add_column("Name", style="cyan")
        table.add_column("Release Year", style="green", justify="center")
        table.add_column("Status", style="magenta")
        table.add_column("ID", style="dim")
        
        # Add rows
        for game in games:
            props = game.get("properties", {})
            name = props.get("name", "Unknown")
            year = str(props.get("release_year", "")) if props.get("release_year") else ""
            status = props.get("status", "")
            
            # Truncate ID for display
            game_id = game.get("id", "")
            if len(game_id) > 10:
                game_id = game_id[:10] + "..."
            
            table.add_row(name, year, status, game_id)
        
        return table
    
    def add_game(self, name, icon_url=None, poster_url=None, release_timestamp=None, status=None, platform=None):
        """
        Add a game to the Notion database.
        
        Args:
            name (str): Game name
            icon_url (str, optional): URL of the game icon. Defaults to None.
            poster_url (str, optional): URL of the game poster. Defaults to None.
            release_timestamp (int, optional): Unix timestamp of the release date. Defaults to None.
            status (str, optional): Game status (multi-select in Notion). Defaults to None.
            platform (str, optional): Game platform (single-select in Notion). Defaults to None.
            
        Returns:
            bool: True if the game was added successfully, False otherwise
        """
        if not self.client:
            raise ValueError("Notion token is not set")
        
        if not self.database_id:
            raise ValueError("Notion database ID is not set")
        
        try:
            # Create the page properties
            properties = {
                "Name": {
                    "title": [
                        {
                            "text": {
                                "content": name
                            }
                        }
                    ]
                }
            }
            
            # Add release year if provided
            if release_timestamp:
                # Convert Unix timestamp to year
                release_date = datetime.fromtimestamp(release_timestamp)
                release_year = release_date.year
                
                # Add the release year to the Wydano property (number type)
                properties["Wydano"] = {
                    "number": release_year
                }
            
            # Add status if provided
            if status:
                if status.lower() == "no status":
                    # Empty multi-select (clear status)
                    properties["Status"] = {
                        "multi_select": []
                    }
                else:
                    # Add single status as multi-select
                    properties["Status"] = {
                        "multi_select": [
                            {
                                "name": status
                            }
                        ]
                    }
            
            # Add platform if provided (single-select)
            if platform:
                properties["Platforma"] = {
                    "select": {
                        "name": platform
                    }
                }
            
            # Create the basic page
            page_data = {
                "parent": {
                    "database_id": self.database_id
                },
                "properties": properties
            }
            
            # Add icon if provided
            if icon_url:
                page_data["icon"] = {
                    "type": "external",
                    "external": {
                        "url": icon_url
                    }
                }
            
            # Add cover if provided
            if poster_url:
                page_data["cover"] = {
                    "type": "external",
                    "external": {
                        "url": poster_url
                    }
                }
            
            # Create the page in Notion
            response = self.client.pages.create(**page_data)
            
            # Return True if the page was created successfully
            return "id" in response
        
        except Exception as e:
            console.print(f"[red]Notion API Error: {str(e)}[/red]")
            return False
