#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Path management for GrantService
Cross-platform path handling for Windows and Linux
"""

import os
import platform
from pathlib import Path
from typing import Optional


class PathManager:
    """Centralized path management for the application"""
    
    def __init__(self):
        """Initialize path manager with OS detection"""
        self.system = platform.system()
        self.is_windows = self.system == 'Windows'
        self.is_linux = self.system == 'Linux'
        
        # Determine base path based on OS and environment
        self._determine_base_path()
        self._setup_paths()
    
    def _determine_base_path(self):
        """Determine the base path for the application"""
        # First check environment variable
        env_base = os.environ.get('GRANTSERVICE_BASE')
        if env_base:
            self.base_path = Path(env_base).resolve()
            return
        
        # Try to find base path relative to this file
        # core/paths.py is in GrantService/core/
        current_file = Path(__file__).resolve()
        potential_base = current_file.parent.parent  # Go up to GrantService
        
        # Verify we're in the right place by checking for key directories
        if (potential_base / 'web-admin').exists() and \
           (potential_base / 'data').exists():
            self.base_path = potential_base
        else:
            # Fallback to OS-specific defaults
            if self.is_windows:
                # Try common Windows paths
                paths_to_try = [
                    Path(r'C:\SnowWhiteAI\GrantService'),
                    Path.cwd() / 'GrantService',
                    Path.cwd()
                ]
                for path in paths_to_try:
                    if path.exists() and (path / 'web-admin').exists():
                        self.base_path = path
                        break
                else:
                    # Last resort - current directory
                    self.base_path = Path.cwd()
            else:
                # Linux/Unix paths
                paths_to_try = [
                    Path('/var/GrantService'),
                    Path.home() / 'GrantService',
                    Path.cwd() / 'GrantService',
                    Path.cwd()
                ]
                for path in paths_to_try:
                    if path.exists() and (path / 'web-admin').exists():
                        self.base_path = path
                        break
                else:
                    self.base_path = Path.cwd()
    
    def _setup_paths(self):
        """Setup all application paths"""
        self.base_path = self.base_path.resolve()
        
        # Main directories
        self.web_admin = self.base_path / 'web-admin'
        self.pages = self.web_admin / 'pages'
        self.utils = self.web_admin / 'utils'
        self.logs = self.web_admin / 'logs'
        
        self.data = self.base_path / 'data'
        self.database_file = self.data / 'grant_service.db'
        
        self.telegram_bot = self.base_path / 'telegram-bot'
        self.bot_config = self.telegram_bot / 'config'
        self.bot_handlers = self.telegram_bot / 'handlers'
        self.bot_services = self.telegram_bot / 'services'
        
        self.agents = self.base_path / 'agents'
        self.scripts = self.base_path / 'scripts'
        
        # Core directory (this module)
        self.core = self.base_path / 'core'
        
        # Config files
        self.env_file = self.base_path / '.env'
        self.constants_file = self.bot_config / 'constants.py'
        self.auth_config_file = self.bot_config / 'auth_config.py'
        
        # Special pages
        self.login_page = self.pages / '🔐_Вход.py'
        self.home_page = self.pages / '🏠_Главная.py'
        self.main_app = self.web_admin / 'GrantService.py'  # Main app file
    
    def get_path(self, name: str) -> Path:
        """Get a path by name"""
        return getattr(self, name, None)
    
    def ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [
            self.web_admin,
            self.pages,
            self.utils,
            self.logs,
            self.data,
            self.telegram_bot,
            self.bot_config,
            self.bot_handlers,
            self.bot_services,
            self.core
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def __str__(self) -> str:
        """String representation"""
        return f"PathManager(base={self.base_path}, os={self.system})"
    
    def __repr__(self) -> str:
        """Detailed representation"""
        paths_info = [
            f"PathManager(",
            f"  system={self.system}",
            f"  base_path={self.base_path}",
            f"  web_admin={self.web_admin}",
            f"  data={self.data}",
            f"  telegram_bot={self.telegram_bot}",
            ")"
        ]
        return "\n".join(paths_info)


# Singleton instance
_path_manager: Optional[PathManager] = None


def get_path_manager() -> PathManager:
    """Get or create the singleton PathManager instance"""
    global _path_manager
    if _path_manager is None:
        _path_manager = PathManager()
    return _path_manager