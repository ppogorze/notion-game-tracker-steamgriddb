"""
Discogs Service - Handles interaction with the Discogs API
"""

import requests
from rich.console import Console

console = Console()

class DiscogsService:
    """
    Service for interacting with the Discogs API.
    
    Provides methods for searching vinyl records and retrieving record details.
    """
    
    # API endpoints
    BASE_URL = "https://api.discogs.com"
    SEARCH_URL = f"{BASE_URL}/database/search"
    RELEASE_URL = f"{BASE_URL}/releases"
    
    def __init__(self, token=None):
        """
        Initialize the Discogs service.
        
        Args:
            token (str, optional): Discogs API token. Defaults to None.
        """
        self.token = token
        self.headers = {
            "User-Agent": "Collection-Manager/1.0 (https://github.com/yourusername/collection-manager)"
        }
    
    def search_vinyl(self, query, search_type="all"):
        """
        Search for vinyl records by query.
        
        Args:
            query (str): Search query (title, artist, etc.)
            search_type (str, optional): Type of search. Defaults to "all".
                Options: "title", "artist", "label", "all"
            
        Returns:
            list: List of matching vinyl records
        """
        try:
            # Prepare search parameters
            params = {
                "q": query,
                "format": "Vinyl",
                "per_page": 20,
                "type": "release"
            }
            
            # Add token if available
            if self.token:
                params["token"] = self.token
            
            # Modify query based on search type
            if search_type == "title":
                params["title"] = query
                params.pop("q", None)
            elif search_type == "artist":
                params["artist"] = query
                params.pop("q", None)
            elif search_type == "label":
                params["label"] = query
                params.pop("q", None)
            
            # Make the API request
            response = requests.get(
                self.SEARCH_URL,
                params=params,
                headers=self.headers
            )
            response.raise_for_status()
            
            data = response.json()
            
            if "results" in data and data["results"]:
                # Process and return the results
                results = []
                for vinyl in data["results"]:
                    results.append(self._process_search_result(vinyl))
                
                return results
            else:
                console.print("[yellow]No vinyl records found matching that query.[/yellow]")
                return []
        
        except requests.exceptions.RequestException as e:
            console.print(f"[red]Request Error: {str(e)}[/red]")
            return []
    
    def _process_search_result(self, vinyl):
        """
        Process a vinyl search result from the API.
        
        Args:
            vinyl (dict): Vinyl data from the API
            
        Returns:
            dict: Processed vinyl data
        """
        # Extract basic information
        result = {
            "id": str(vinyl.get("id", "")),
            "title": vinyl.get("title", "Unknown Title"),
            "year": vinyl.get("year"),
            "label": vinyl.get("label", []),
            "format": vinyl.get("format", []),
            "genre": vinyl.get("genre", []),
            "style": vinyl.get("style", []),
            "country": vinyl.get("country"),
            "cover_url": vinyl.get("cover_image"),
            "thumb_url": vinyl.get("thumb"),
            "resource_url": vinyl.get("resource_url")
        }
        
        # Extract artist from title
        if " - " in result["title"]:
            parts = result["title"].split(" - ", 1)
            result["artist"] = parts[0].strip()
            result["album"] = parts[1].strip()
        else:
            result["artist"] = "Unknown Artist"
            result["album"] = result["title"]
        
        return result
    
    def get_vinyl_details(self, vinyl_id):
        """
        Get detailed information about a vinyl record.
        
        Args:
            vinyl_id (str): Discogs vinyl ID
            
        Returns:
            dict: Vinyl details
        """
        try:
            # Prepare request parameters
            params = {}
            if self.token:
                params["token"] = self.token
            
            # Make the API request
            url = f"{self.RELEASE_URL}/{vinyl_id}"
            response = requests.get(
                url,
                params=params,
                headers=self.headers
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Process the data
            result = {
                "id": str(data.get("id", "")),
                "title": data.get("title", "Unknown Title"),
                "artist": [],
                "album": data.get("title", "Unknown Title"),
                "year": data.get("year"),
                "label": [],
                "format": [],
                "genre": data.get("genres", []),
                "style": data.get("styles", []),
                "country": data.get("country"),
                "cover_url": None,
                "thumb_url": None,
                "tracklist": [],
                "notes": data.get("notes"),
                "released": data.get("released"),
                "resource_url": data.get("resource_url")
            }
            
            # Extract artists
            if "artists" in data:
                for artist in data["artists"]:
                    result["artist"].append(artist.get("name", "").replace(" (", "").replace(")", ""))
            
            # Extract labels
            if "labels" in data:
                for label in data["labels"]:
                    result["label"].append(label.get("name", ""))
            
            # Extract formats
            if "formats" in data:
                for format_info in data["formats"]:
                    format_name = format_info.get("name", "")
                    if format_name:
                        result["format"].append(format_name)
                    
                    # Extract additional format descriptions
                    if "descriptions" in format_info:
                        for desc in format_info["descriptions"]:
                            if desc not in result["format"]:
                                result["format"].append(desc)
            
            # Extract tracklist
            if "tracklist" in data:
                for track in data["tracklist"]:
                    track_info = {
                        "position": track.get("position", ""),
                        "title": track.get("title", ""),
                        "duration": track.get("duration", "")
                    }
                    result["tracklist"].append(track_info)
            
            # Extract images
            if "images" in data:
                for image in data["images"]:
                    if image.get("type") == "primary":
                        result["cover_url"] = image.get("uri", "")
                        result["thumb_url"] = image.get("uri150", "")
                        break
                
                # If no primary image found, use the first one
                if not result["cover_url"] and data["images"]:
                    result["cover_url"] = data["images"][0].get("uri", "")
                    result["thumb_url"] = data["images"][0].get("uri150", "")
            
            return result
        
        except requests.exceptions.RequestException as e:
            console.print(f"[red]Request Error: {str(e)}[/red]")
            return None
    
    def check_cover_exists(self, url):
        """
        Check if a cover image exists at the given URL.
        
        Args:
            url (str): URL of the cover image
            
        Returns:
            bool: True if the cover exists, False otherwise
        """
        if not url:
            return False
            
        try:
            # Use a timeout to avoid hanging on slow responses
            response = requests.head(url, headers=self.headers, timeout=2)
            
            # Check if the response is successful
            return response.status_code == 200
        except Exception as e:
            # Log the error but don't crash
            console.print(f"[dim]Cover check error for {url}: {str(e)}[/dim]")
            return False
