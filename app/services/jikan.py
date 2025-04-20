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
                anime_data = data["data"]
                # Print debug info about the data structure
                console.print(f"[dim]Debug: Retrieved data for anime ID {anime_id}[/dim]")
                return anime_data
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

    def get_anime_full_details(self, anime_id):
        """
        Get comprehensive details about an anime including studio, episodes, synopsis, etc.

        Args:
            anime_id (int): Jikan/MyAnimeList anime ID

        Returns:
            dict: Comprehensive anime details
        """
        anime_details = self.get_anime_details(anime_id)

        if not anime_details:
            return None

        # Extract relevant information
        result = {
            "title": anime_details.get("title"),
            "episodes": anime_details.get("episodes"),
            "status": anime_details.get("status"),  # Airing, Finished Airing, etc.
            "synopsis": anime_details.get("synopsis"),
            "year": anime_details.get("year"),
            "mal_id": anime_details.get("mal_id"),
            "url": anime_details.get("url"),  # MAL URL
            "image_url": None,
            "studios": [],
            "seasons": 1  # Default to 1 season if not specified
        }

        # Get image URL
        if "images" in anime_details and "jpg" in anime_details["images"]:
            result["image_url"] = anime_details["images"]["jpg"].get("large_image_url")

        # Get studios
        if "studios" in anime_details and anime_details["studios"]:
            result["studios"] = [studio.get("name") for studio in anime_details["studios"]]

        # Try to determine number of seasons (this is an approximation)
        # MAL doesn't directly provide season count
        if "relations" in anime_details:
            # Count sequels and prequels as potential seasons
            related_seasons = 0
            for relation in anime_details["relations"]:
                if relation.get("relation") in ["Sequel", "Prequel"]:
                    related_seasons += 1
            if related_seasons > 0:
                result["seasons"] = related_seasons + 1  # +1 for the current season

        return result
