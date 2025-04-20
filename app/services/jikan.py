"""
Jikan Service - Handles interaction with the Jikan API (MyAnimeList)
"""

import requests
from rich.console import Console

console = Console()

class JikanService:
    """
    Service for interacting with the Jikan API.
    
    Provides methods for searching anime and retrieving anime assets.
    """
    
    # API URLs
    BASE_URL = "https://api.jikan.moe/v4"
    SEARCH_URL = f"{BASE_URL}/anime"
    ANIME_URL = f"{BASE_URL}/anime"
    
    def __init__(self):
        """
        Initialize the Jikan service.
        """
        self.headers = {}
    
    def search_anime(self, anime_name):
        """
        Search for anime by name.
        
        Args:
            anime_name (str): Name of the anime to search for
            
        Returns:
            list: List of matching anime
        """
        try:
            # Search for anime with the given name
            response = requests.get(
                f"{self.SEARCH_URL}",
                params={"q": anime_name},
                headers=self.headers
            )
            response.raise_for_status()
            
            data = response.json()
            
            if "data" in data:
                return data["data"]
            else:
                console.print("[red]API Error: No data returned[/red]")
                return []
        
        except requests.exceptions.RequestException as e:
            console.print(f"[red]Request Error: {str(e)}[/red]")
            return []
    
    def get_anime_details(self, anime_id):
        """
        Get detailed information about an anime.
        
        Args:
            anime_id (int): Jikan/MyAnimeList anime ID
            
        Returns:
            dict: Anime details
        """
        try:
            response = requests.get(
                f"{self.ANIME_URL}/{anime_id}",
                headers=self.headers
            )
            response.raise_for_status()
            
            data = response.json()
            
            if "data" in data:
                return data["data"]
            else:
                console.print("[red]API Error: No data returned[/red]")
                return None
        
        except requests.exceptions.RequestException as e:
            console.print(f"[red]Request Error when fetching anime details: {str(e)}[/red]")
            return None
    
    def get_anime_image(self, anime_id):
        """
        Get the image URL for an anime.
        
        Args:
            anime_id (int): Jikan/MyAnimeList anime ID
            
        Returns:
            str: URL of the anime image
        """
        anime_details = self.get_anime_details(anime_id)
        
        if anime_details and "images" in anime_details:
            # Get the image URL from the anime details
            images = anime_details["images"]
            if "jpg" in images and "large_image_url" in images["jpg"]:
                return images["jpg"]["large_image_url"]
            elif "jpg" in images and "image_url" in images["jpg"]:
                return images["jpg"]["image_url"]
        
        return None
