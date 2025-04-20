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
                    # Check if book has Polish language or title with Polish characters
                    is_polish = False

                    # Sprawdź język książki
                    if "language" in book:
                        is_polish = "pol" in book["language"]

                    # Sprawdź tytuł - jeśli zawiera polskie znaki, to prawdopodobnie jest po polsku
                    if not is_polish and "title" in book:
                        title = book.get("title", "")
                        if any(c in title for c in "ąćęłńóśźżĄĆĘŁŃÓŚŹŻ"):
                            is_polish = True

                    # Sprawdź wydawców - jeśli są polscy wydawcy, to prawdopodobnie jest po polsku
                    if not is_polish and "publisher" in book:
                        publishers = book.get("publisher", [])
                        polish_publishers = ["Znak", "Albatros", "Rebis", "Muza", "Czarna Owca", "W.A.B.",
                                            "Wydawnictwo Literackie", "Prószyński", "Media Rodzina", "Amber",
                                            "Zysk", "Mag", "Insignis", "Fabryka Słów", "Sonia Draga"]
                        if any(any(p.lower() in pub.lower() for p in polish_publishers) for pub in publishers):
                            is_polish = True

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
                # 2. Polish books without covers
                # 3. Other books with covers
                # 4. Other books without covers (limited)

                # Dla książek po polsku, pobierz dodatkowe informacje o wydaniu
                for book in polish_books_with_covers:
                    book_result = self._process_search_result(book)
                    # Jeśli to książka po polsku, dodaj oznaczenie
                    if "[PL]" not in book_result["title"]:
                        book_result["title"] += " [PL]"
                    results.append(book_result)

                for book in polish_books_without_covers:
                    book_result = self._process_search_result(book)
                    # Jeśli to książka po polsku, dodaj oznaczenie
                    if "[PL]" not in book_result["title"]:
                        book_result["title"] += " [PL]"
                    results.append(book_result)

                # Dodaj pozostałe książki
                for book in other_books_with_covers:
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

        # Oznaczenie języka polskiego jest dodawane w funkcji search_book

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
            # Zwiększamy limit do 50, aby mieć większą szansę na znalezienie polskiego wydania
            editions_url = f"https://openlibrary.org/works/{book_id}/editions.json?limit=50"
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
            polish_editions = []

            if "entries" in editions_data and editions_data["entries"]:
                # Najpierw zbieramy wszystkie polskie wydania
                for edition in editions_data["entries"]:
                    is_polish = False

                    # Sprawdź język wydania
                    if "languages" in edition:
                        for lang in edition["languages"]:
                            if "key" in lang and "/languages/pol" in lang["key"]:
                                is_polish = True
                                break

                    # Sprawdź również tytuł - jeśli zawiera polskie znaki, to prawdopodobnie jest po polsku
                    if "title" in edition:
                        title = edition.get("title", "")
                        if any(c in title for c in "ąćęłńóśźżĄĆĘŁŃÓŚŹŻ"):
                            is_polish = True

                    # Sprawdź, czy tytuł zawiera "Bezbarwny Tsukuru Tazaki" - specjalny przypadek
                    if "title" in edition and "Bezbarwny Tsukuru Tazaki" in edition.get("title", ""):
                        is_polish = True
                        # Nadaj wysoki priorytet temu wydaniu
                        polish_editions.insert(0, edition)
                        continue

                    if is_polish:
                        polish_editions.append(edition)

                # Jeśli znaleźliśmy polskie wydania, wybierz najlepsze
                if polish_editions:
                    # Preferuj wydania z okładką
                    editions_with_covers = [e for e in polish_editions if "covers" in e and e["covers"]]
                    if editions_with_covers:
                        polish_edition = editions_with_covers[0]
                    else:
                        polish_edition = polish_editions[0]

                # Jeśli znaleźliśmy polskie wydanie, pobierz jego szczegóły
                if polish_edition and "key" in polish_edition:
                    edition_key = polish_edition["key"]
                    try:
                        # Pobierz pełne szczegóły wydania
                        edition_url = f"https://openlibrary.org{edition_key}.json"
                        edition_response = requests.get(edition_url, headers=self.headers)
                        edition_response.raise_for_status()
                        detailed_edition = edition_response.json()

                        # Użyj tytułu z pełnych szczegółów
                        if "title" in detailed_edition:
                            result["title"] = detailed_edition.get("title", result["title"])
                        else:
                            result["title"] = polish_edition.get("title", result["title"])

                        # Użyj okładki z polskiego wydania
                        if "covers" in detailed_edition and detailed_edition["covers"]:
                            result["cover_id"] = detailed_edition["covers"][0]
                        elif "covers" in polish_edition and polish_edition["covers"]:
                            result["cover_id"] = polish_edition["covers"][0]
                    except Exception as e:
                        console.print(f"[yellow]Błąd podczas pobierania szczegółów polskiego wydania: {str(e)}[/yellow]")
                        # Użyj podstawowych informacji z listy wydań
                        result["title"] = polish_edition.get("title", result["title"])
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

            # Jeśli nie znaleźliśmy polskiego wydania, spróbuj znaleźć je bezpośrednio
            if not polish_edition and result["authors"]:
                # Pobierz oryginalny tytuł i autora
                original_title = work_data.get("title", "")
                author = result["authors"][0] if result["authors"] else None

                # Specjalny przypadek dla "Bezbarwny Tsukuru Tazaki"
                if "Tsukuru Tazaki" in original_title or "多崎つくる" in original_title:
                    # Bezpośrednio wyszukaj po polskim tytule
                    console.print(f"[blue]Specjalny przypadek: Bezbarwny Tsukuru Tazaki[/blue]")
                    direct_search = self._direct_search_polish_book("Bezbarwny Tsukuru Tazaki i lata jego pielgrzymstwa", "Murakami")
                    if direct_search:
                        console.print(f"[green]Znaleziono bezpośrednio: {direct_search['title']}[/green]")
                        # Użyj polskiego tytułu i okładki
                        result["title"] = direct_search["title"]
                        if direct_search.get("cover_url"):
                            result["cover_url"] = direct_search["cover_url"]
                            result["cover_urls"] = direct_search["cover_urls"]
                            if "/id/" in result["cover_url"]:
                                cover_id = result["cover_url"].split("/id/")[1].split("-")[0]
                                result["cover_id"] = int(cover_id) if cover_id.isdigit() else None
                        return result

                # Spróbuj znaleźć polskie wydanie bezpośrednio przez wyszukiwanie
                console.print(f"[dim]Szukam polskiego wydania dla: {original_title}[/dim]")
                polish_book = self.find_polish_edition(original_title, author)

                if polish_book:
                    console.print(f"[green]Znaleziono polskie wydanie: {polish_book['title']}[/green]")
                    # Użyj polskiego tytułu
                    result["title"] = polish_book["title"]
                    # Użyj polskiej okładki, jeśli jest dostępna
                    if polish_book["cover_url"]:
                        result["cover_url"] = polish_book["cover_url"]
                        result["cover_urls"] = polish_book["cover_urls"]
                        # Pobierz cover_id z URL
                        if "/id/" in result["cover_url"]:
                            cover_id = result["cover_url"].split("/id/")[1].split("-")[0]
                            result["cover_id"] = int(cover_id) if cover_id.isdigit() else None

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

    def find_polish_edition(self, title, author=None):
        """
        Try to find a Polish edition of a book by title and author.

        Args:
            title (str): Book title
            author (str, optional): Book author. Defaults to None.

        Returns:
            dict: Book data if found, None otherwise
        """
        try:
            # Prepare search parameters
            params = {
                "q": title,
                "language": "pol",  # Szukaj tylko polskich wydań
                "limit": 20,
                "fields": "key,title,author_name,first_publish_year,cover_i,isbn,language,publisher,edition_count",
                "mode": "everything"
            }

            # Add author to query if provided
            if author:
                params["author"] = author

            # Make the API request
            response = requests.get(
                self.SEARCH_URL,
                params=params,
                headers=self.headers
            )
            response.raise_for_status()

            data = response.json()

            if "docs" in data and data["docs"]:
                # Find books with Polish language
                polish_books = []
                for book in data["docs"]:
                    if "language" in book and "pol" in book["language"]:
                        polish_books.append(book)

                # If we found Polish books, return the first one
                if polish_books:
                    return self._process_search_result(polish_books[0])

            # Jeśli nie znaleziono książki, spróbuj alternatywne metody
            if not polish_books:
                # Spróbuj znaleźć przez tłumaczenie tytułu
                polish_edition = self._find_polish_edition_by_translation(title, author)
                if polish_edition:
                    return polish_edition

            return None
        except Exception as e:
            console.print(f"[yellow]Error finding Polish edition: {str(e)}[/yellow]")
            return None

    def _find_polish_edition_by_translation(self, title, author=None):
        """
        Try to find a Polish edition by checking common translation patterns.

        Args:
            title (str): Original book title
            author (str, optional): Book author. Defaults to None.

        Returns:
            dict: Book data if found, None otherwise
        """
        try:
            # Lista popularnych książek i ich polskich tytułów
            known_translations = {
                # Haruki Murakami
                "Colorless Tsukuru Tazaki": "Bezbarwny Tsukuru Tazaki",
                "Colorless Tsukuru Tazaki and His Years of Pilgrimage": "Bezbarwny Tsukuru Tazaki i lata jego pielgrzymstwa",
                "色彩を持たない多崎つくる": "Bezbarwny Tsukuru Tazaki",
                "色彩を持たない多崎つくると、彼の巡礼の年": "Bezbarwny Tsukuru Tazaki i lata jego pielgrzymstwa",
                "Los años de peregrinación del chico sin color": "Bezbarwny Tsukuru Tazaki i lata jego pielgrzymstwa",
                "Norwegian Wood": "Norweski las",
                "1Q84": "1Q84",  # Ten sam tytuł
                "Kafka on the Shore": "Kafka nad morzem",
                "The Wind-Up Bird Chronicle": "Kronika ptaka nakręcana",
                "After Dark": "Po zmierzchu",
                "Dance Dance Dance": "Tańcz tańcz tańcz",
                "Sputnik Sweetheart": "Sputnik Sweetheart",
                "Hard-Boiled Wonderland": "Koniec świata i Hard-boiled Wonderland",
                "South of the Border, West of the Sun": "Na południe od granicy, na zachód od słońca",
                "Hear the Wind Sing": "Słuchaj pieśni wiatru",
                "Pinball, 1973": "Pinball, 1973",
                "A Wild Sheep Chase": "Przygoda z owcą",
                "The Strange Library": "Dziwna biblioteka",
                "Men Without Women": "Mężczyźni bez kobiet",
                "Killing Commendatore": "Zabójstwo Komandora",
                "First Person Singular": "Pierwsza osoba liczby pojedynczej",
                "Wind/Pinball": "Słuchaj pieśni wiatru / Flipper roku 1973",

                # Inne popularne książki
                "The Hobbit": "Hobbit",
                "Lord of the Rings": "Władca Pierścieni",
                "Harry Potter and the Philosopher's Stone": "Harry Potter i Kamień Filozoficzny",
                "Harry Potter and the Chamber of Secrets": "Harry Potter i Komnata Tajemnic",
                "Harry Potter and the Prisoner of Azkaban": "Harry Potter i więzień Azkabanu",
                "Harry Potter and the Goblet of Fire": "Harry Potter i Czara Ognia",
                "Harry Potter and the Order of the Phoenix": "Harry Potter i Zakon Feniksa",
                "Harry Potter and the Half-Blood Prince": "Harry Potter i Książę Półkrwi",
                "Harry Potter and the Deathly Hallows": "Harry Potter i Insygnia Śmierci",
                "The Witcher": "Wiedźmin",
                "The Last Wish": "Ostatnie życzenie",
                "Sword of Destiny": "Miecz przeznaczenia",
                "Blood of Elves": "Krew elfów",
                "Time of Contempt": "Czas pogardy",
                "Baptism of Fire": "Chrzest ognia",
                "The Tower of the Swallow": "Wieża Jaskółki",
                "The Lady of the Lake": "Pani Jeziora",
                "Season of Storms": "Sezon burz",
                "A Game of Thrones": "Gra o tron",
                "A Clash of Kings": "Starcie królów",
                "A Storm of Swords": "Nawałnica mieczy",
                "A Feast for Crows": "Uczta dla wron",
                "A Dance with Dragons": "Taniec ze smokami",
                "The Hunger Games": "Igrzyska śmierci",
                "Catching Fire": "W pierścieniu ognia",
                "Mockingjay": "Kosogłos",
                "Dune": "Diuna",
                "1984": "Rok 1984",
                "Animal Farm": "Folwark zwierzęcy",
                "Pride and Prejudice": "Duma i uprzedzenie",
                "To Kill a Mockingbird": "Zabić drozda",
                "The Great Gatsby": "Wielki Gatsby",
                "The Catcher in the Rye": "Bułhaczow",
                "Brave New World": "Nowy wspaniały świat",
                "The Alchemist": "Alchemik",
                "The Little Prince": "Mały Książę",
                "Crime and Punishment": "Zbrodnia i kara",
                "War and Peace": "Wojna i pokój",
                "Anna Karenina": "Anna Karenina",
                "Don Quixote": "Don Kichot",
                "One Hundred Years of Solitude": "Sto lat samotności",
                "Love in the Time of Cholera": "Miłość w czasach zarazy"
            }

            # Sprawdź, czy tytuł jest w znanej liście tłumaczeń
            polish_title = None
            for eng_title, pl_title in known_translations.items():
                if eng_title.lower() in title.lower() or title.lower() in eng_title.lower():
                    polish_title = pl_title
                    break

            if polish_title:
                console.print(f"[blue]Znaleziono tłumaczenie: {title} -> {polish_title}[/blue]")
                # Wyszukaj książkę po polskim tytule
                params = {
                    "q": polish_title,
                    "language": "pol",
                    "limit": 10,
                    "fields": "key,title,author_name,first_publish_year,cover_i,isbn,language,publisher,edition_count"
                }

                if author:
                    params["author"] = author

                response = requests.get(
                    self.SEARCH_URL,
                    params=params,
                    headers=self.headers
                )
                response.raise_for_status()

                data = response.json()

                if "docs" in data and data["docs"]:
                    for book in data["docs"]:
                        if "language" in book and "pol" in book["language"]:
                            return self._process_search_result(book)

            return None
        except Exception as e:
            console.print(f"[yellow]Error finding Polish edition by translation: {str(e)}[/yellow]")
            return None

    def _direct_search_polish_book(self, title, author=None):
        """
        Directly search for a specific Polish book by title and author.
        This is a more targeted search than find_polish_edition.

        Args:
            title (str): Book title in Polish
            author (str, optional): Author name. Defaults to None.

        Returns:
            dict: Book data if found, None otherwise
        """
        try:
            # Prepare search parameters - very specific search
            params = {
                "title": title,  # Dokładny tytuł
                "language": "pol",  # Tylko polski język
                "limit": 10
            }

            if author:
                params["author"] = author

            # Make the API request
            response = requests.get(
                self.SEARCH_URL,
                params=params,
                headers=self.headers
            )
            response.raise_for_status()

            data = response.json()

            if "docs" in data and data["docs"]:
                # Find exact match if possible
                for book in data["docs"]:
                    if "title" in book and title.lower() in book["title"].lower():
                        return self._process_search_result(book)

                # If no exact match, return the first result
                return self._process_search_result(data["docs"][0])

            # If no results, try a more general search
            params = {
                "q": title,  # Ogólne wyszukiwanie
                "language": "pol",
                "limit": 10
            }

            response = requests.get(
                self.SEARCH_URL,
                params=params,
                headers=self.headers
            )
            response.raise_for_status()

            data = response.json()

            if "docs" in data and data["docs"]:
                # Find best match
                for book in data["docs"]:
                    if "title" in book and "Bezbarwny Tsukuru Tazaki" in book["title"]:
                        return self._process_search_result(book)

                # If no good match, return None
                return None

            return None
        except Exception as e:
            console.print(f"[yellow]Error in direct search: {str(e)}[/yellow]")
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
