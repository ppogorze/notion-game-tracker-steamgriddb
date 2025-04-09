"""
SteamGridDB Service - Handles interaction with the SteamGridDB API
"""

import requests
from rich.console import Console

console = Console()

class SteamGridDBService:
    """
    Service for interacting with the SteamGridDB API.
    
    Provides methods for searching games and retrieving game assets.
    """
    
    # API URLs
    BASE_URL = "https://www.steamgriddb.com/api/v2"
    SEARCH_URL = f"{BASE_URL}/search/autocomplete"
    GRID_URL = f"{BASE_URL}/grids/game"
    ICON_URL = f"{BASE_URL}/icons/game"
    
    def __init__(self, api_key):
        """
        Initialize the SteamGridDB service.
        
        Args:
            api_key (str): SteamGridDB API key
        """
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}"
        }
    
    def search_game(self, game_name):
        """
        Search for games by name using autocomplete endpoint.
        
        Args:
            game_name (str): Name of the game to search for
            
        Returns:
            list: List of matching games
        """
        if not self.api_key:
            raise ValueError("SteamGridDB API key is not set")
        
        try:
            # The autocomplete endpoint requires the term as part of the URL path
            response = requests.get(
                f"{self.SEARCH_URL}/{game_name}",
                headers=self.headers
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data["success"]:
                return data["data"]
            else:
                console.print(f"[red]API Error: {data.get('errors', ['Unknown error'])[0]}[/red]")
                return []
        
        except requests.exceptions.RequestException as e:
            console.print(f"[red]Request Error: {str(e)}[/red]")
            return []
    
    def get_game_icon(self, game_id):
        """
        Get the icon URL for a game.
        
        Args:
            game_id (int): SteamGridDB game ID
            
        Returns:
            str: URL of the game icon
        """
        if not self.api_key:
            raise ValueError("SteamGridDB API key is not set")
        
        try:
            response = requests.get(
                f"{self.ICON_URL}/{game_id}",
                headers=self.headers
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data["success"] and data["data"]:
                # Get the first icon (prefer PNG)
                icons = data["data"]
                png_icons = [icon for icon in icons if icon.get("mime", "").endswith("png")]
                
                if png_icons:
                    # Prefer PNG icons
                    return png_icons[0]["url"]
                elif icons:
                    # Any icon is better than nothing
                    return icons[0]["url"]
            
            # Return None if no icons found
            return None
        
        except requests.exceptions.RequestException as e:
            console.print(f"[red]Request Error when fetching icon: {str(e)}[/red]")
            return None
    
    def get_game_poster(self, game_id):
        """
        Get the poster (grid) URL for a game.
        
        Args:
            game_id (int): SteamGridDB game ID
            
        Returns:
            str: URL of the game poster
        """
        if not self.api_key:
            raise ValueError("SteamGridDB API key is not set")
        
        try:
            response = requests.get(
                f"{self.GRID_URL}/{game_id}",
                headers=self.headers
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data["success"] and data["data"]:
                # Get the first poster
                posters = data["data"]
                if posters:
                    return posters[0]["url"]
            
            # Return None if no posters found
            return None
        
        except requests.exceptions.RequestException as e:
            console.print(f"[red]Request Error when fetching poster: {str(e)}[/red]")
            return None
