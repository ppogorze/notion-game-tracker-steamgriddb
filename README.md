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
- **Anime Library Management:**
  - List all anime in your collection
  - Search your anime library
  - Edit existing anime (name, release year, status)
  - Delete anime from your collection

### General
- Interactive CLI interface

## Requirements

- Python 3.7+
- SteamGridDB API key (for games functionality)
- Notion integration token and database ID

## Installation

1. Create (free) Notion account and copy this [template](https://struktura.notion.site/Gry-1cfc923134f380a3b534dd19e5af239b?pvs=4)

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

3. **Notion Database ID**:
   - Open your Notion database
   - Copy the URL, which contains the database ID
   - The app will extract the ID from the URL

## Usage

Run the application:
```
python games.py  # For games collection
python anime.py  # For anime collection
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

## Examples

### Games
1. Run the games application: `python games.py`
2. Select "Settings" to configure your API keys and database ID
3. Select "Add Game" and enter a game name
4. Choose from the search results
5. The game will be added to your Notion database with proper icon and cover image

### Anime
1. Run the anime application: `python anime.py`
2. Select "Settings" to configure your Notion integration
3. Select "Add Anime" and enter an anime name
4. Choose from the search results
5. The anime will be added to your Notion database with proper cover image

## License

MIT License
