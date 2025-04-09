"""
Config Manager - Manages application settings
"""

import os
import json
from pathlib import Path

class ConfigManager:
    """
    Configuration manager for the application.
    Handles loading, saving, and validating configuration settings.
    """
    
    def __init__(self, config_file=None):
        """
        Initialize the configuration manager.
        
        Args:
            config_file (str, optional): Path to the configuration file.
                                        Defaults to ./config/config.json.
        """
        if config_file is None:
            # Default config path is in the config directory
            self.config_dir = Path('config')
            self.config_file = self.config_dir / 'config.json'
        else:
            self.config_file = Path(config_file)
            self.config_dir = self.config_file.parent
        
        # Create config directory if it doesn't exist
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def load_config(self):
        """
        Load configuration from the config file.
        
        Returns:
            dict: Configuration settings
        """
        if not self.config_file.exists():
            # Return empty config if file doesn't exist
            return {}
        
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            # Return empty config if file is invalid or doesn't exist
            return {}
    
    def save_config(self, config):
        """
        Save configuration to the config file.
        
        Args:
            config (dict): Configuration settings to save
        """
        # Create config directory if it doesn't exist
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def is_config_complete(self):
        """
        Check if all required configuration settings are present.
        
        Returns:
            bool: True if all required settings are present, False otherwise
        """
        config = self.load_config()
        
        # Check if all required settings are present and not empty
        required_settings = [
            'notion_database_id',
            'notion_token',
            'steamgriddb_api_key'
        ]
        
        for setting in required_settings:
            if setting not in config or not config[setting]:
                return False
        
        return True
    
    def extract_notion_db_id(self, url_or_id):
        """
        Extract the Notion database ID from a URL or direct ID.
        
        Args:
            url_or_id (str): Notion database URL or ID
            
        Returns:
            str: Extracted database ID
        """
        # If it's a URL, extract the ID
        if url_or_id.startswith('https://www.notion.so/'):
            # Extract the ID from the URL
            # URL format: https://www.notion.so/{workspace}/{database_id}?v={view_id}
            # or https://www.notion.so/{workspace}/{page_title}-{database_id}
            
            # Get the last part of the URL path (before any query parameters)
            path = url_or_id.split('?')[0]
            path_parts = path.rstrip('/').split('/')
            last_part = path_parts[-1]
            
            # The ID is either the entire last part,
            # or the last 32 characters of the last part
            # (if the URL includes the page title)
            if '-' in last_part:
                # URL includes page title: extract ID from the end
                id_part = last_part.split('-')[-1]
                return id_part
            else:
                # URL is direct to the database
                return last_part
        
        # If it's already just the ID, return it directly
        return url_or_id
