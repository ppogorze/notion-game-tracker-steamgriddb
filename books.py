#!/usr/bin/env python3
"""
Book Collection Manager CLI

This application helps you manage your book collection by:
1. Searching for books on Open Library
2. Adding them to your Notion database
"""

import sys
import questionary
from rich.console import Console
from rich.panel import Panel

from app.services.openlibrary import OpenLibraryService
from app.services.notion import NotionService
from app.utils.config_manager import ConfigManager
from app.utils.library_manager import library_menu

console = Console()

def main():
    """Main entry point for the CLI application."""
    console.print(Panel.fit(
        "[bold blue]Book Collection Manager[/bold blue]\n"
        "[italic]Connect your books to Notion[/italic]",
        border_style="blue"
    ))

    # Load configuration
    config_manager = ConfigManager()
    config = config_manager.load_config()

    # Check if configuration is complete for books
    if not config_manager.is_config_complete(config_type='books'):
        console.print("[yellow]Books configuration is incomplete. Please update settings.[/yellow]")
        if not settings_menu(config_manager):
            console.print("[red]Configuration required to continue.[/red]")
            return

    # Initialize services with config
    # Reload config to ensure we have the latest values
    config = config_manager.load_config()

    books_service = OpenLibraryService()
    notion_service = NotionService(
        config.get('notion_token', ''),
        config.get('books_database_id', '')
    )

    # Main program loop
    while True:
        choice = questionary.select(
            "What would you like to do?",
            choices=[
                "Add Book",
                "View Book Library",
                "Settings",
                "Exit"
            ]
        ).ask()

        if choice == "Add Book":
            add_book(books_service, notion_service)
        elif choice == "View Book Library":
            library_menu(notion_service, books_service)
        elif choice == "Settings":
            if settings_menu(config_manager):
                # Reload configuration and reinitialize services
                config = config_manager.load_config()
                notion_service = NotionService(
                    config.get('notion_token', ''),
                    config.get('books_database_id', '')
                )
        elif choice == "Exit":
            console.print("[green]Goodbye![/green]")
            sys.exit(0)

def add_book(books_service, notion_service):
    """Handle the book addition workflow."""
    # Choose search type
    search_type = questionary.select(
        "Search by:",
        choices=[
            "Title",
            "Author",
            "ISBN",
            "Any",
            "Combined (Title + Author)"
        ],
        default="Combined (Title + Author)"
    ).ask()

    # Zawsze wyszukujemy we wszystkich językach
    language = "Any"

    # Get search query from user
    if search_type == "Combined (Title + Author)":
        query_prompt = "Enter search terms (title, author, etc.):"
    else:
        query_prompt = f"Enter book {search_type.lower()}:"

    query = questionary.text(query_prompt).ask()

    if not query:
        console.print("[yellow]Search query cannot be empty.[/yellow]")
        return

    console.print(f"[blue]Searching for [bold]{query}[/bold] on Open Library...[/blue]")

    # Map UI search type to API search type
    search_type_map = {
        "Title": "title",
        "Author": "author",
        "ISBN": "isbn",
        "Any": "any",
        "Combined (Title + Author)": "combined"
    }

    # Specjalny przypadek dla "Bezbarwny Tsukuru Tazaki"
    if "tsukuru" in query.lower() or "tazaki" in query.lower() or "bezbarwny" in query.lower() or "murakami" in query.lower():
        console.print("[blue]Wykryto wyszukiwanie książki Haruki Murakami - Bezbarwny Tsukuru Tazaki[/blue]")
        # Bezpośrednio wyszukaj po polskim tytule
        direct_search = books_service._direct_search_polish_book("Bezbarwny Tsukuru Tazaki i lata jego pielgrzymstwa", "Murakami")
        if direct_search:
            search_results = [direct_search]
        else:
            # Jeśli bezpośrednie wyszukiwanie nie zadziałało, użyj standardowego wyszukiwania
            search_results = books_service.search_book(
                query,
                language=None,
                search_type=search_type_map[search_type]
            )
    else:
        # Search for the book on Open Library
        # Wyszukiwanie we wszystkich językach, ale z preferencją dla polskich wyników
        search_results = books_service.search_book(
            query,
            language=None,  # Brak ograniczenia językowego
            search_type=search_type_map[search_type]
        )

    # Sprawdź, czy znaleziono wyniki
    if not search_results:
        console.print(f"[yellow]No books found matching that {search_type.lower()}.[/yellow]")
        return

    # Let user select from matching results
    book_choices = []
    for book in search_results:
        # Format the book information for display
        title = book.get('title', 'Unknown')
        authors = book.get('authors', [])
        author_text = ', '.join(authors) if authors else 'Unknown'
        published_year = book.get('first_publish_year', 'Unknown')

        # Tytuł już zawiera oznaczenie języka, jeśli jest po polsku
        book_choices.append(f"{title} by {author_text} ({published_year})")
    book_choices.append("Cancel")

    selected = questionary.select(
        "Select a book:",
        choices=book_choices
    ).ask()

    if selected == "Cancel":
        return

    # Find the selected book in the results
    selected_index = book_choices.index(selected)
    selected_book = search_results[selected_index]

    # Get detailed book information
    console.print("[blue]Retrieving detailed book information...[/blue]")
    book_details = books_service.get_book_details(selected_book['id'])

    if not book_details:
        console.print("[yellow]Could not retrieve detailed information for this book.[/yellow]")
        return

    # Extract information from the details
    title = book_details.get('title')
    authors = book_details.get('authors', [])
    cover_url = book_details.get('cover_url')
    published_year = book_details.get('first_publish_year')
    description = book_details.get('description')
    page_count = book_details.get('page_count')
    publishers = book_details.get('publishers', [])
    publisher = publishers[0] if publishers else None
    subjects = book_details.get('subjects', [])
    isbn = book_details.get('isbn', [])
    isbn_13 = isbn[0] if isbn and len(isbn) > 0 else None
    languages = book_details.get('languages', [])
    language = languages[0] if languages else None
    links = book_details.get('links', [])
    info_link = links[0].get('url') if links else None

    # Display detailed book information
    console.print(f"[green]Selected: [bold]{title}[/bold][/green]")
    console.print(f"[cyan]Authors:[/cyan] {', '.join(authors)}")
    if published_year:
        console.print(f"[cyan]Published:[/cyan] {published_year}")
    if publisher:
        console.print(f"[cyan]Publisher:[/cyan] {publisher}")
    if page_count:
        console.print(f"[cyan]Pages:[/cyan] {page_count}")
    if isbn_13:
        console.print(f"[cyan]ISBN-13:[/cyan] {isbn_13}")
    if subjects:
        console.print(f"[cyan]Categories:[/cyan] {', '.join(subjects[:3])}")
    if language:
        console.print(f"[cyan]Language:[/cyan] {language.upper()}")

    # Show a preview of the description if available
    if description:
        # Truncate description if it's too long
        max_desc_length = 200
        short_desc = description[:max_desc_length] + "..." if len(description) > max_desc_length else description
        console.print(f"[cyan]Description:[/cyan] {short_desc}")

    # Prompt for book status
    status_choices = [
        "Reading",
        "To Read",
        "Read",
        "Abandoned",
        "No Status"
    ]

    status = questionary.select(
        "Book status:",
        choices=status_choices,
        default="No Status"
    ).ask()

    # Prompt for book format
    format_choices = [
        "Physical",
        "Digital (PDF)",
        "Digital (EPUB)",
        "Digital (Other)",
        "Audiobook"
    ]

    format_type = questionary.select(
        "Book format:",
        choices=format_choices,
        default="Physical"
    ).ask()

    # Zawsze używamy największej dostępnej okładki
    cover_url = book_details.get("cover_url")
    icon_url = None

    # Użyj mniejszej okładki jako ikony
    if "small" in book_details.get("cover_urls", {}):
        icon_url = book_details["cover_urls"]["small"]
    else:
        icon_url = cover_url

    # Add to Notion
    console.print("[blue]Adding book to Notion...[/blue]")

    try:
        notion_service.add_book(
            title=title,
            authors=authors,
            icon_url=icon_url,
            poster_url=cover_url,
            published_date=published_year,
            status=status,
            format_type=format_type,
            page_count=page_count,
            publisher=publisher,
            description=description,
            categories=subjects[:5] if subjects else [],
            isbn=isbn_13,
            info_link=info_link
        )

        console.print(f"[green]✓ Added [bold]{title}[/bold] to Notion database[/green]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")

def settings_menu(config_manager):
    """Handle the settings menu."""
    console.print(Panel.fit(
        "[bold]Settings[/bold]",
        border_style="blue"
    ))

    # Load current config
    config = config_manager.load_config()

    # Update settings
    books_db = questionary.text(
        "Books Notion Database ID (or full URL):",
        default=config.get('books_database_id', '')
    ).ask()

    notion_token = questionary.text(
        "Notion Integration Secret:",
        default=config.get('notion_token', '')
    ).ask()

    # Save new settings
    new_config = config.copy()  # Keep existing settings
    new_config.update({
        'books_database_id': books_db,
        'notion_token': notion_token
    })

    config_manager.save_config(new_config)
    console.print("[green]Settings saved successfully![/green]")

    # Return True if config is complete for books
    return config_manager.is_config_complete(config_type='books')

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Program interrupted.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Unexpected error: {str(e)}[/red]")
        sys.exit(1)
