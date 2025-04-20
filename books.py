#!/usr/bin/env python3
"""
Book Collection Manager CLI

This application helps you manage your book collection by:
1. Searching for books on Google Books
2. Adding them to your Notion database
"""

import sys
import questionary
from rich.console import Console
from rich.panel import Panel

from app.services.googlebooks import GoogleBooksService
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
    
    books_service = GoogleBooksService()
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
    # Get book title from user
    book_title = questionary.text("Enter book title:").ask()
    if not book_title:
        console.print("[yellow]Book title cannot be empty.[/yellow]")
        return
    
    console.print(f"[blue]Searching for [bold]{book_title}[/bold] on Google Books...[/blue]")
    
    # Search for the book on Google Books
    try:
        search_results = books_service.search_book(book_title)
        
        if not search_results:
            console.print("[yellow]No books found matching that title.[/yellow]")
            return
        
        # Let user select from matching results
        book_choices = []
        for book in search_results:
            # Check if the result has the expected structure
            volume_info = book.get('volumeInfo', {})
            title = volume_info.get('title', 'Unknown')
            authors = volume_info.get('authors', [])
            author_text = ', '.join(authors) if authors else 'Unknown'
            published_date = volume_info.get('publishedDate', 'Unknown')
            
            book_choices.append(f"{title} by {author_text} ({published_date})")
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
        book_details = books_service.get_book_full_details(selected_book['id'])
        
        if not book_details:
            console.print("[yellow]Could not retrieve detailed information for this book.[/yellow]")
            return
        
        # Extract information from the details
        title = book_details.get('title')
        authors = book_details.get('authors', [])
        image_url = book_details.get('image_url')
        published_date = book_details.get('published_date')
        description = book_details.get('description')
        page_count = book_details.get('page_count')
        publisher = book_details.get('publisher')
        categories = book_details.get('categories', [])
        isbn_13 = book_details.get('isbn_13')
        info_link = book_details.get('info_link')
        
        console.print(f"[green]Selected: [bold]{title}[/bold] by {', '.join(authors)}[/green]")
        
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
        
        # Add to Notion
        console.print("[blue]Adding book to Notion...[/blue]")
        
        notion_service.add_book(
            title=title,
            authors=authors,
            icon_url=image_url,
            poster_url=image_url,
            published_date=published_date,
            status=status,
            format_type=format_type,
            page_count=page_count,
            publisher=publisher,
            description=description,
            categories=categories,
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
