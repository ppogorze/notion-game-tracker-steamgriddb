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

    def search_book(self, query, language="pl", search_type="title"):
        """
        Search for books by title, author, or ISBN.

        Args:
            query (str): Search query (title, author name, or ISBN)
            language (str, optional): Preferred language for results. Defaults to "pl" (Polish).
            search_type (str, optional): Type of search. Defaults to "title".
                Options: "title", "author", "isbn", "any"

        Returns:
            list: List of matching books
        """
        try:
            # Modify the query based on search type
            search_query = query
            if search_type == "title":
                search_query = f"intitle:{query}"
            elif search_type == "author":
                search_query = f"inauthor:{query}"
            elif search_type == "isbn":
                # Clean up ISBN (remove hyphens)
                clean_isbn = query.replace("-", "")
                search_query = f"isbn:{clean_isbn}"
            # "any" type uses the query as-is

            # Search for books with the given query
            params = {
                "q": search_query,
                "maxResults": 15,  # Increased from 10 to get more results
                "orderBy": "relevance",  # Order by relevance to get best matches first
                "printType": "books"  # Only return books, not magazines or other content
            }

            # Add language restriction if specified
            if language:
                params["langRestrict"] = language

            response = requests.get(
                self.SEARCH_URL,
                params=params,
                headers=self.headers
            )
            response.raise_for_status()

            data = response.json()

            if "items" in data:
                return data["items"]
            else:
                # If no results in preferred language, try without language restriction
                if language and search_type != "isbn":  # Don't retry for ISBN searches
                    console.print(f"[yellow]No books found in {language}. Trying without language restriction...[/yellow]")
                    return self.search_book(query, language=None, search_type=search_type)
                else:
                    console.print("[yellow]No books found matching that query.[/yellow]")
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

        # Get image URLs
        if "imageLinks" in volume_info:
            image_links = volume_info["imageLinks"]

            # Store all available image sizes
            result["image_urls"] = {}
            for img_type in ["extraLarge", "large", "medium", "small", "thumbnail"]:
                if img_type in image_links:
                    # Fix the image URL protocol (Google Books sometimes returns http instead of https)
                    img_url = image_links[img_type]
                    if img_url.startswith("http://"):
                        img_url = "https://" + img_url[7:]

                    # Remove zoom parameters for higher quality
                    img_url = img_url.replace("&zoom=1", "")

                    result["image_urls"][img_type] = img_url

            # Set the main image URL to the largest available
            for img_type in ["extraLarge", "large", "medium", "small", "thumbnail"]:
                if img_type in result["image_urls"]:
                    result["image_url"] = result["image_urls"][img_type]
                    break

        # Get ISBNs
        if "industryIdentifiers" in volume_info:
            for identifier in volume_info["industryIdentifiers"]:
                if identifier.get("type") == "ISBN_13":
                    result["isbn_13"] = identifier.get("identifier")
                elif identifier.get("type") == "ISBN_10":
                    result["isbn_10"] = identifier.get("identifier")

        return result

    def get_book_cover(self, book_id, size="large"):
        """
        Get the cover image URL for a book in the specified size.

        Args:
            book_id (str): Google Books volume ID
            size (str, optional): Size of the cover image. Defaults to "large".
                Options: "extraLarge", "large", "medium", "small", "thumbnail"

        Returns:
            str: URL of the book cover image
        """
        book_details = self.get_book_full_details(book_id)

        if not book_details or "image_urls" not in book_details:
            return None

        # Try to get the requested size
        if size in book_details["image_urls"]:
            return book_details["image_urls"][size]

        # If requested size is not available, return the largest available
        if book_details["image_url"]:
            return book_details["image_url"]

        return None
