"""
OpenLibrary Service - Handles interaction with the Open Library API
"""

import requests
from rich.console import Console

console = Console()

class OpenLibraryService:
    """
    Service for interacting with the Open Library API.

    Provides methods for searching books and retrieving book details.
    """

    # API endpoints
    SEARCH_URL = "https://openlibrary.org/search.json"
    BOOK_URL = "https://openlibrary.org/api/books"
    COVER_URL = "https://covers.openlibrary.org/b"

    def __init__(self):
        """Initialize the OpenLibrary service."""
        self.headers = {
            "User-Agent": "Collection-Manager/1.0 (https://github.com/yourusername/collection-manager)"
        }

    def search_book(self, query, language=None, search_type="any"):
        """
        Search for books by query.

        Args:
            query (str): Search query (title, author name, or ISBN)
            language (str, optional): Preferred language for results. Defaults to None.
            search_type (str, optional): Type of search. Defaults to "any".
                Options: "title", "author", "isbn", "any"

        Returns:
            list: List of matching books
        """
        try:
            # Prepare search parameters
            params = {
                "q": query,
                "limit": 40,  # Get more results to ensure we have enough with covers
                "fields": "key,title,author_name,first_publish_year,cover_i,isbn,language,publisher,edition_count",
                "mode": "everything"
            }

            # Add language filter if specified
            if language:
                params["language"] = language

            # Modify query based on search type
            if search_type == "title":
                # For title search, we'll use both title and q parameters to maximize results
                params["title"] = query
            elif search_type == "author":
                # For author search, we'll use both author and q parameters to maximize results
                params["author"] = query
            elif search_type == "isbn":
                # Clean up ISBN (remove hyphens)
                clean_isbn = query.replace("-", "")
                params["isbn"] = clean_isbn
                params.pop("q", None)  # For ISBN, we don't need the q parameter
            elif search_type == "combined":
                # For combined search, we'll do a general search with q parameter
                # This allows searching for both title and author in one query
                # We'll also increase the limit to get more results
                params["limit"] = 60

            # Make the API request
            response = requests.get(
                self.SEARCH_URL,
                params=params,
                headers=self.headers
            )
            response.raise_for_status()

            data = response.json()

            if "docs" in data and data["docs"]:
                # Process and return the results
                results = []

                # First pass: separate books by language and cover availability
                polish_books_with_covers = []
                polish_books_without_covers = []
                other_books_with_covers = []
                other_books_without_covers = []

                for book in data["docs"]:
                    # Check if book has Polish language
                    is_polish = False
                    if "language" in book:
                        is_polish = "pol" in book["language"]

                    # Sort by language and cover availability
                    if is_polish:
                        if "cover_i" in book:
                            polish_books_with_covers.append(book)
                        else:
                            polish_books_without_covers.append(book)
                    else:
                        if "cover_i" in book:
                            other_books_with_covers.append(book)
                        else:
                            other_books_without_covers.append(book)

                # Process books in order of preference:
                # 1. Polish books with covers
                # 2. Other books with covers
                # 3. Polish books without covers
                # 4. Other books without covers
                for book in polish_books_with_covers:
                    results.append(self._process_search_result(book))

                for book in other_books_with_covers:
                    results.append(self._process_search_result(book))

                for book in polish_books_without_covers:
                    results.append(self._process_search_result(book))

                # Limit the number of books without covers
                for book in other_books_without_covers[:10]:  # Reduced limit for non-Polish books without covers
                    results.append(self._process_search_result(book))

                return results
            else:
                # If no results with the specified language, try without language restriction
                if language and search_type != "isbn":
                    console.print(f"[yellow]No books found in {language}. Trying without language restriction...[/yellow]")
                    return self.search_book(query, language=None, search_type=search_type)
                else:
                    console.print("[yellow]No books found matching that query.[/yellow]")
                    return []

        except requests.exceptions.RequestException as e:
            console.print(f"[red]Request Error: {str(e)}[/red]")
            return []

    def _process_search_result(self, book):
        """
        Process a book search result from the API.

        Args:
            book (dict): Book data from the API

        Returns:
            dict: Processed book data
        """
        # Extract basic information
        result = {
            "id": book.get("key", "").replace("/works/", ""),
            "title": book.get("title", "Unknown Title"),
            "authors": book.get("author_name", []),
            "first_publish_year": book.get("first_publish_year"),
            "cover_id": book.get("cover_i"),
            "isbn": book.get("isbn", []),
            "languages": book.get("language", []),
            "publishers": book.get("publisher", []),
            "edition_count": book.get("edition_count", 0)
        }

        # Dodaj informację o języku polskim w tytule, jeśli książka jest po polsku
        if "pol" in result["languages"]:
            result["title"] = f"{result['title']} [PL]"

        # Add cover URLs if available
        result["cover_urls"] = {}

        # Try to get cover by cover_id (best quality)
        if result["cover_id"]:
            result["cover_urls"] = {
                "small": f"{self.COVER_URL}/id/{result['cover_id']}-S.jpg",
                "medium": f"{self.COVER_URL}/id/{result['cover_id']}-M.jpg",
                "large": f"{self.COVER_URL}/id/{result['cover_id']}-L.jpg"
            }
            result["cover_url"] = result["cover_urls"]["medium"]  # Default cover

        # Try to get cover by ISBN if no cover_id is available or as a backup
        if (not result["cover_id"] or not self.check_cover_exists(result["cover_urls"].get("medium", ""))) and result["isbn"] and len(result["isbn"]) > 0:
            isbn = result["isbn"][0]
            isbn_cover_urls = {
                "small": f"{self.COVER_URL}/isbn/{isbn}-S.jpg",
                "medium": f"{self.COVER_URL}/isbn/{isbn}-M.jpg",
                "large": f"{self.COVER_URL}/isbn/{isbn}-L.jpg"
            }

            # Check if the ISBN cover exists
            if self.check_cover_exists(isbn_cover_urls["medium"]):
                result["cover_urls"] = isbn_cover_urls
                result["cover_url"] = isbn_cover_urls["medium"]

        # If we still don't have a valid cover, set to None
        if not result.get("cover_url") or not self.check_cover_exists(result["cover_url"]):
            result["cover_url"] = None

        return result

    def get_book_details(self, book_id):
        """
        Get detailed information about a book.

        Args:
            book_id (str): Open Library book ID

        Returns:
            dict: Book details
        """
        try:
            # First get the work details
            work_url = f"https://openlibrary.org/works/{book_id}.json"
            work_response = requests.get(work_url, headers=self.headers)
            work_response.raise_for_status()
            work_data = work_response.json()

            # Get all editions to find Polish version if available
            editions_url = f"https://openlibrary.org/works/{book_id}/editions.json?limit=20"
            editions_response = requests.get(editions_url, headers=self.headers)
            editions_response.raise_for_status()
            editions_data = editions_response.json()

            # Combine the data
            result = {
                "id": book_id,
                "title": work_data.get("title", "Unknown Title"),
                "authors": [],
                "description": None,
                "subjects": work_data.get("subjects", []),
                "first_publish_year": work_data.get("first_publish_date"),
                "cover_id": None,
                "isbn": [],
                "publishers": [],
                "page_count": None,
                "languages": [],
                "links": []
            }

            # Try to find Polish edition
            polish_edition = None
            if "entries" in editions_data and editions_data["entries"]:
                for edition in editions_data["entries"]:
                    # Check if this edition has Polish language
                    if "languages" in edition:
                        for lang in edition["languages"]:
                            if "key" in lang and "/languages/pol" in lang["key"]:
                                polish_edition = edition
                                break
                    if polish_edition:
                        break

                # If we found a Polish edition, use its title
                if polish_edition and "title" in polish_edition:
                    result["title"] = polish_edition.get("title", result["title"])
                    # Also use its cover if available
                    if "covers" in polish_edition and polish_edition["covers"]:
                        result["cover_id"] = polish_edition["covers"][0]

            # Extract description
            if "description" in work_data:
                if isinstance(work_data["description"], dict):
                    result["description"] = work_data["description"].get("value", "")
                else:
                    result["description"] = work_data["description"]

            # Get author information
            if "authors" in work_data:
                for author_ref in work_data["authors"]:
                    if "author" in author_ref and "key" in author_ref["author"]:
                        author_key = author_ref["author"]["key"]
                        author_url = f"https://openlibrary.org{author_key}.json"
                        try:
                            author_response = requests.get(author_url, headers=self.headers)
                            author_response.raise_for_status()
                            author_data = author_response.json()
                            result["authors"].append(author_data.get("name", "Unknown Author"))
                        except:
                            # If we can't get the author details, just use the key
                            result["authors"].append(author_key.split("/")[-1].replace("_", " ").title())

            # Get cover ID
            if "covers" in work_data and work_data["covers"]:
                result["cover_id"] = work_data["covers"][0]

            # Process edition data if available
            if "entries" in editions_data and editions_data["entries"]:
                # Use Polish edition if available, otherwise use the first one
                edition_to_use = polish_edition if polish_edition else editions_data["entries"][0]

                # Get ISBN
                if "isbn_13" in edition_to_use:
                    result["isbn"] = edition_to_use["isbn_13"]
                elif "isbn_10" in edition_to_use:
                    result["isbn"] = edition_to_use["isbn_10"]

                # Get publishers
                if "publishers" in edition_to_use:
                    result["publishers"] = edition_to_use["publishers"]

                # Get page count
                if "number_of_pages" in edition_to_use:
                    result["page_count"] = edition_to_use["number_of_pages"]

                # Get languages
                if "languages" in edition_to_use:
                    for lang in edition_to_use["languages"]:
                        if "key" in lang:
                            lang_key = lang["key"].split("/")[-1]
                            result["languages"].append(lang_key)

                # Get cover ID if not already set
                if not result["cover_id"] and "covers" in edition_to_use and edition_to_use["covers"]:
                    result["cover_id"] = edition_to_use["covers"][0]

            # Add cover URLs if available
            result["cover_urls"] = {}

            # Try to get cover by cover_id (best quality)
            if result["cover_id"]:
                result["cover_urls"] = {
                    "small": f"{self.COVER_URL}/id/{result['cover_id']}-S.jpg",
                    "medium": f"{self.COVER_URL}/id/{result['cover_id']}-M.jpg",
                    "large": f"{self.COVER_URL}/id/{result['cover_id']}-L.jpg"
                }
                result["cover_url"] = result["cover_urls"]["large"]  # Default to large cover for details

            # Try to get cover by ISBN if no cover_id is available or as a backup
            if (not result["cover_id"] or not self.check_cover_exists(result["cover_urls"].get("large", ""))) and result["isbn"] and len(result["isbn"]) > 0:
                isbn = result["isbn"][0]
                isbn_cover_urls = {
                    "small": f"{self.COVER_URL}/isbn/{isbn}-S.jpg",
                    "medium": f"{self.COVER_URL}/isbn/{isbn}-M.jpg",
                    "large": f"{self.COVER_URL}/isbn/{isbn}-L.jpg"
                }

                # Check if the ISBN cover exists
                if self.check_cover_exists(isbn_cover_urls["large"]):
                    result["cover_urls"] = isbn_cover_urls
                    result["cover_url"] = isbn_cover_urls["large"]

            # If we still don't have a valid cover, try with OLID
            if (not result.get("cover_url") or not self.check_cover_exists(result["cover_url"])) and book_id:
                olid_cover_urls = {
                    "small": f"{self.COVER_URL}/olid/OL{book_id}W-S.jpg",
                    "medium": f"{self.COVER_URL}/olid/OL{book_id}W-M.jpg",
                    "large": f"{self.COVER_URL}/olid/OL{book_id}W-L.jpg"
                }

                # Check if the OLID cover exists
                if self.check_cover_exists(olid_cover_urls["large"]):
                    result["cover_urls"] = olid_cover_urls
                    result["cover_url"] = olid_cover_urls["large"]

            # If we still don't have a valid cover, set to None
            if not result.get("cover_url") or not self.check_cover_exists(result["cover_url"]):
                result["cover_url"] = None

            # Add links
            result["links"] = [
                {
                    "title": "View on Open Library",
                    "url": f"https://openlibrary.org/works/{book_id}"
                }
            ]

            return result

        except requests.exceptions.RequestException as e:
            console.print(f"[red]Request Error: {str(e)}[/red]")
            return None

    def get_book_cover(self, book_id=None, isbn=None, size="M"):
        """
        Get the cover image URL for a book.

        Args:
            book_id (str, optional): Open Library book ID. Defaults to None.
            isbn (str, optional): ISBN of the book. Defaults to None.
            size (str, optional): Size of the cover image. Defaults to "M".
                Options: "S" (small), "M" (medium), "L" (large)

        Returns:
            str: URL of the book cover image
        """
        if not book_id and not isbn:
            return None

        # Validate size
        if size not in ["S", "M", "L"]:
            size = "M"  # Default to medium if invalid size

        if book_id:
            # First try to get the cover ID
            try:
                work_url = f"https://openlibrary.org/works/{book_id}.json"
                response = requests.get(work_url, headers=self.headers)
                response.raise_for_status()
                data = response.json()

                if "covers" in data and data["covers"]:
                    cover_id = data["covers"][0]
                    return f"{self.COVER_URL}/id/{cover_id}-{size}.jpg"
            except:
                pass

        if isbn:
            # Clean up ISBN (remove hyphens)
            clean_isbn = isbn.replace("-", "")
            return f"{self.COVER_URL}/isbn/{clean_isbn}-{size}.jpg"

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

            # Check if the response is successful and the image is not a placeholder
            # Open Library returns a small placeholder image for missing covers
            # A real cover image should be larger than 1000 bytes
            content_length = int(response.headers.get("Content-Length", 0))
            return response.status_code == 200 and content_length > 1000
        except Exception as e:
            # Log the error but don't crash
            console.print(f"[dim]Cover check error for {url}: {str(e)}[/dim]")
            return False
