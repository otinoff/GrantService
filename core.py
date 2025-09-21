#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core module for GrantService Admin Panel
Cross-platform environment setup and path management
"""

import sys
import os
from pathlib import Path
import platform
from typing import Dict, Any, Optional


class PathManager:
    """Cross-platform path management"""
    
    def __init__(self, base_path: Optional[Path] = None):
        if base_path:
            self.base_path = Path(base_path).resolve()
        else:
            # Auto-detect base path
            self.base_path = Path(__file__).parent.resolve()
        
        self.system = platform.system()
        
        # Core directories
        self.web_admin = self.base_path / "web-admin"
        self.telegram_bot = self.base_path / "telegram-bot"
        self.data = self.base_path / "data"
        self.scripts = self.base_path / "scripts"
        
        # Key files
        self.main_app = self.web_admin / "app_main.py"
        self.home_page = self.web_admin / "pages" / "🏠_Главная.py"
        self.login_page = self.web_admin / "pages" / "🔐_Вход.py"
        self.constants_file = self.telegram_bot / "config" / "constants.py"
        
        # Database
        if self.system == "Windows":
            self.database_path = self.base_path / "data" / "grantservice.db"
        else:
            self.database_path = Path("/var/GrantService/data/grantservice.db")


class Config:
    """Configuration settings"""
    
    def __init__(self):
        # Streamlit settings
        self.streamlit_port = int(os.environ.get('STREAMLIT_PORT', '8501'))
        self.streamlit_host = os.environ.get('STREAMLIT_HOST', 'localhost')
        self.streamlit_headless = os.environ.get('STREAMLIT_HEADLESS', 'false').lower() == 'true'
        
        # Logging
        self.log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
        
        # Database
        self.database_url = os.environ.get('DATABASE_URL', '')


class Environment:
    """Environment setup and management"""
    
    def __init__(self, paths: PathManager, config: Config):
        self.paths = paths
        self.config = config
        self.setup_complete = False
    
    def setup_python_path(self, verbose: bool = False):
        """Setup Python path for imports"""
        paths_to_add = [
            str(self.paths.base_path),
            str(self.paths.web_admin),
            str(self.paths.telegram_bot),
            str(self.paths.data),
        ]
        
        for path in paths_to_add:
            if path not in sys.path:
                sys.path.insert(0, path)
                if verbose:
                    print(f"Added to Python path: {path}")
    
    def ensure_directories(self, verbose: bool = False):
        """Ensure required directories exist"""
        dirs_to_create = [
            self.paths.web_admin / "logs",
            self.paths.base_path / "logs",
            self.paths.data,
        ]
        
        for dir_path in dirs_to_create:
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                if verbose:
                    print(f"Created directory: {dir_path}")
    
    def check_critical_files(self, verbose: bool = False):
        """Check if critical files exist"""
        critical_files = [
            self.paths.constants_file,
            self.paths.web_admin / "utils" / "auth.py",
        ]
        
        missing_files = []
        for file_path in critical_files:
            if not file_path.exists():
                missing_files.append(str(file_path))
                if verbose:
                    print(f"Missing critical file: {file_path}")
        
        return missing_files
    
    def setup_environment_variables(self):
        """Setup environment variables"""
        # Set base path
        os.environ['GRANTSERVICE_BASE_PATH'] = str(self.paths.base_path)
        
        # Set database path
        os.environ['DATABASE_PATH'] = str(self.paths.database_path)
    
    def setup(self, verbose: bool = False):
        """Complete environment setup"""
        if verbose:
            print(f"Setting up environment for {self.paths.system}")
            print(f"Base path: {self.paths.base_path}")
        
        # Setup Python path
        self.setup_python_path(verbose)
        
        # Ensure directories exist
        self.ensure_directories(verbose)
        
        # Setup environment variables
        self.setup_environment_variables()
        
        # Check critical files
        missing_files = self.check_critical_files(verbose)
        
        if verbose:
            if missing_files:
                print(f"Warning: {len(missing_files)} critical files missing")
            else:
                print("All critical files found")
        
        self.setup_complete = True
        
        if verbose:
            print("Environment setup complete")
        
        return self
    
    def print_debug_info(self):
        """Print debug information"""
        print(f"System: {self.paths.system}")
        print(f"Base path: {self.paths.base_path}")
        print(f"Database path: {self.paths.database_path}")
        print(f"Streamlit config: {self.config.streamlit_host}:{self.config.streamlit_port}")
        print(f"Python path entries: {len([p for p in sys.path if str(self.paths.base_path) in p])}")


# Global instances
_path_manager = None
_config = None
_environment = None


def get_path_manager(base_path: Optional[Path] = None) -> PathManager:
    """Get or create global path manager"""
    global _path_manager
    if _path_manager is None:
        _path_manager = PathManager(base_path)
    return _path_manager


def get_config() -> Config:
    """Get or create global config"""
    global _config
    if _config is None:
        _config = Config()
    return _config


def setup_environment(verbose: bool = False, base_path: Optional[Path] = None) -> Environment:
    """Setup and return environment"""
    global _environment
    if _environment is None:
        paths = get_path_manager(base_path)
        config = get_config()
        _environment = Environment(paths, config)
        _environment.setup(verbose)
    return _environment


def get_environment() -> Optional[Environment]:
    """Get current environment (if setup)"""
    return _environment