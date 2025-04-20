"""
Google Books Service - Handles interaction with the Google Books API
"""

import requests
from rich.console import Console

console = Console()

class GoogleBooksService:
    """
    Service for interacting with the Google Books API.
    
    Provides methods for searching books and retrieving book details.
    """
    
    # API URLs
    BASE_URL = "https://www.googleapis.com/books/v1"
    SEARCH_URL = f"{BASE_URL}/volumes"
    
    def __init__(self):
        """
        Initialize the Google Books service.
        """
        self.headers = {}
    
    def search_book(self, book_title):
        """
        Search for books by title.
        
        Args:
            book_title (str): Title of the book to search for
            
        Returns:
            list: List of matching books
        """
        try:
            # Search for books with the given title
            response = requests.get(
                self.SEARCH_URL,
                params={"q": book_title, "maxResults": 10},
                headers=self.headers
            )
            response.raise_for_status()
            
            data = response.json()
            
            if "items" in data:
                return data["items"]
            else:
                console.print("[yellow]No books found matching that title.[/yellow]")
                return []
        
        except requests.exceptions.RequestException as e:
            console.print(f"[red]Request Error: {str(e)}[/red]")
            return []
    
    def get_book_details(self, book_id):
        """
        Get detailed information about a book.
        
        Args:
            book_id (str): Google Books volume ID
            
        Returns:
            dict: Book details
        """
        try:
            response = requests.get(
                f"{self.SEARCH_URL}/{book_id}",
                headers=self.headers
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Print debug info about the data structure
            console.print(f"[dim]Debug: Retrieved data for book ID {book_id}[/dim]")
            return data
        
        except requests.exceptions.RequestException as e:
            console.print(f"[red]Request Error when fetching book details: {str(e)}[/red]")
            return None
    
    def get_book_full_details(self, book_id):
        """
        Get comprehensive details about a book.
        
        Args:
            book_id (str): Google Books volume ID
            
        Returns:
            dict: Comprehensive book details
        """
        book_data = self.get_book_details(book_id)
        
        if not book_data:
            return None
            
        # Extract relevant information
        result = {
            "title": None,
            "authors": [],
            "publisher": None,
            "published_date": None,
            "description": None,
            "page_count": None,
            "categories": [],
            "image_url": None,
            "language": None,
            "preview_link": None,
            "info_link": None,
            "isbn_13": None,
            "isbn_10": None
        }
        
        # Extract volume info
        volume_info = book_data.get("volumeInfo", {})
        
        # Basic information
        result["title"] = volume_info.get("title")
        result["authors"] = volume_info.get("authors", [])
        result["publisher"] = volume_info.get("publisher")
        result["published_date"] = volume_info.get("publishedDate")
        result["description"] = volume_info.get("description")
        result["page_count"] = volume_info.get("pageCount")
        result["categories"] = volume_info.get("categories", [])
        result["language"] = volume_info.get("language")
        result["preview_link"] = volume_info.get("previewLink")
        result["info_link"] = volume_info.get("infoLink")
        
        # Get image URL
        if "imageLinks" in volume_info:
            image_links = volume_info["imageLinks"]
            # Try to get the largest available image
            for img_type in ["extraLarge", "large", "medium", "small", "thumbnail"]:
                if img_type in image_links:
                    result["image_url"] = image_links[img_type]
                    break
        
        # Get ISBNs
        if "industryIdentifiers" in volume_info:
            for identifier in volume_info["industryIdentifiers"]:
                if identifier.get("type") == "ISBN_13":
                    result["isbn_13"] = identifier.get("identifier")
                elif identifier.get("type") == "ISBN_10":
                    result["isbn_10"] = identifier.get("identifier")
        
        return result
