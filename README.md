![Screenshot](images/screenshot.png)

[Watch video](https://github.com/ppogorze/notion-game-tracker-steamgriddb/raw/main/images/video.mp4)

# Collection Manager

A Python CLI application to manage your game and anime collections by connecting to Notion.

## Features

### Games
- Search for games on SteamGridDB
- Add games to your Notion database automatically
- Set games with proper icons and cover images
- **Game Library Management:**
  - List all games in your collection
  - Search your game library
  - Edit existing games (name, release year, icons, and covers)
  - Delete games from your collection

### Anime
- Search for anime on MyAnimeList (via Jikan API)
- Add anime to your Notion database automatically
- Set anime with proper cover images
- Track anime with detailed information:
  - Studio
  - Number of episodes
  - Number of seasons
  - Airing status
  - Plot synopsis
  - Links to MyAnimeList
- **Anime Library Management:**
  - List all anime in your collection
  - Search your anime library
  - Edit existing anime
  - Delete anime from your collection

### Books
- Search for books on Google Books
- Add books to your Notion database automatically
- Set books with proper cover images
- Track books with detailed information:
  - Authors
  - Publisher
  - Publication date
  - Page count
  - Format (physical/digital)
  - Description
  - Categories/genres
  - ISBN
- **Book Library Management:**
  - List all books in your collection
  - Search your book library
  - Edit existing books
  - Delete books from your collection

### General
- Interactive CLI interface

## Requirements

- Python 3.7+
- SteamGridDB API key (for games functionality)
- Notion integration token
- Three separate Notion databases (one for games, one for anime, one for books)

## Installation

1. Create (free) Notion account and create three databases with the following structures:

   ### Games Database
   - **Name** (title): Game title
   - **Wydano** (number): Release year
   - **Status** (multi-select): Game status (Chcę zagrać, Przestałem grać, W trakcie, Ukończone)
   - **Platforma** (select): Game platform (PC, PS4, PS5, Switch, etc.)

   ### Anime Database
   - **Name** (title): Anime title
   - **Wydano** (number): Release year
   - **Status** (multi-select): Anime status (Watching, To Watch, Watched, Abandoned)
   - **Studio** (select): Animation studio
   - **Episodes** (number): Number of episodes
   - **Seasons** (number): Number of seasons
   - **Airing** (select): Airing status (Airing, Finished Airing, etc.)
   - **Synopsis** (rich text): Plot description
   - **MAL** (url): MyAnimeList URL
   - **AniDB** (url): AniDB URL

   ### Books Database
   - **Name** (title): Book title
   - **Authors** (rich text): Book authors
   - **Published** (rich text): Publication date
   - **Status** (multi-select): Reading status (Reading, To Read, Read, Abandoned)
   - **Format** (select): Book format (Physical, Digital (PDF), Digital (EPUB), etc.)
   - **Pages** (number): Number of pages
   - **Publisher** (rich text): Book publisher
   - **Description** (rich text): Book description
   - **Categories** (multi-select): Book categories/genres
   - **ISBN** (rich text): ISBN number
   - **Info** (url): Link to more information

2. Clone the repository:
```
git clone https://github.com/yourusername/game-collection-manager.git
cd game-collection-manager
```

3. Install dependencies:
```
pip install notion-client questionary rich requests
```

## Configuration

Before using the application, you need to set up your API keys:

1. **SteamGridDB API Key**:
   - Create an account at [SteamGridDB](https://www.steamgriddb.com/)
   - Go to your profile and generate an API key

2. **Notion Integration**:
   - Go to [Notion Integrations](https://www.notion.so/my-integrations)
   - Create a new integration and copy the secret token
   - Share your database with the integration

3. **Notion Database IDs**:
   - Open your Games Notion database
   - Copy the URL, which contains the database ID
   - The app will extract the ID from the URL
   - Repeat for your Anime Notion database

## Usage

Run the application:
```
python games.py  # For games collection
python anime.py  # For anime collection
python books.py  # For books collection
```

Each application provides the following options:

### Games Application
1. **Add Game**: Search for a game and add it to your Notion database
2. **View Game Library**: Manage your existing game collection
   - List all games with pagination
   - Search for specific games
   - Edit game information and assets
   - Delete games from your collection
3. **Settings**: Configure your API keys and database ID

### Anime Application
1. **Add Anime**: Search for an anime and add it to your Notion database
2. **View Anime Library**: Manage your existing anime collection
   - List all anime with pagination
   - Search for specific anime
   - Edit anime information
   - Delete anime from your collection
3. **Settings**: Configure your API keys and database ID

### Books Application
1. **Add Book**: Search for a book and add it to your Notion database
2. **View Book Library**: Manage your existing book collection
   - List all books with pagination
   - Search for specific books
   - Edit book information
   - Delete books from your collection
3. **Settings**: Configure your API keys and database ID

## Examples

### Games
1. Run the games application: `python games.py`
2. Select "Settings" to configure your API keys and games database ID
3. Select "Add Game" and enter a game name
4. Choose from the search results
5. The game will be added to your Notion database with proper icon and cover image

### Anime
1. Run the anime application: `python anime.py`
2. Select "Settings" to configure your Notion integration and anime database ID
3. Select "Add Anime" and enter an anime name
4. Choose from the search results
5. Select the anime status (Watching, To Watch, etc.)
6. The anime will be added to your Notion database with all details

### Books
1. Run the books application: `python books.py`
2. Select "Settings" to configure your Notion integration and books database ID
3. Select "Add Book" and enter a book title
4. Choose from the search results
5. Select the book status (Reading, To Read, etc.) and format (Physical, Digital, etc.)
6. The book will be added to your Notion database with all details

## License

MIT License
