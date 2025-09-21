#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Environment setup for GrantService
Manages sys.path and environment variables
"""

import sys
import os
from pathlib import Path
from typing import List, Optional
import logging

from .paths import get_path_manager


class Environment:
    """Environment configuration and setup"""
    
    def __init__(self):
        """Initialize environment manager"""
        self.paths = get_path_manager()
        self.logger = self._setup_logger()
        self._original_path = sys.path.copy()
        self._is_setup = False
    
    def _setup_logger(self) -> logging.Logger:
        """Setup basic logger"""
        logger = logging.getLogger('grantservice.core')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def setup(self, verbose: bool = False):
        """Setup the application environment"""
        if self._is_setup:
            if verbose:
                self.logger.info("Environment already setup")
            return
        
        if verbose:
            self.logger.info(f"Setting up environment for {self.paths.system}")
            self.logger.info(f"Base path: {self.paths.base_path}")
        
        # Setup Python path
        self._setup_python_path()
        
        # Setup environment variables
        self._setup_env_variables()
        
        # Ensure directories exist
        self.paths.ensure_directories()
        
        self._is_setup = True
        
        if verbose:
            self.logger.info("Environment setup complete")
    
    def _setup_python_path(self):
        """Setup Python path for imports"""
        # Paths to add in priority order
        paths_to_add = [
            self.paths.base_path,           # For 'data', 'config' imports
            self.paths.web_admin,            # For 'utils' imports
            self.paths.telegram_bot,         # For 'services', 'handlers' imports
            self.paths.agents,               # For 'agents' imports
        ]
        
        # Add paths to sys.path if not already there
        for path in paths_to_add:
            path_str = str(path)
            if path_str not in sys.path:
                sys.path.insert(0, path_str)
    
    def _setup_env_variables(self):
        """Setup environment variables"""
        # Set base path
        os.environ['GRANTSERVICE_BASE'] = str(self.paths.base_path)
        
        # Set component paths
        os.environ['GRANTSERVICE_WEB_ADMIN'] = str(self.paths.web_admin)
        os.environ['GRANTSERVICE_DATA'] = str(self.paths.data)
        os.environ['GRANTSERVICE_TELEGRAM_BOT'] = str(self.paths.telegram_bot)
        
        # Set database path
        os.environ['GRANTSERVICE_DB'] = str(self.paths.database_file)
        
        # Set OS info
        os.environ['GRANTSERVICE_OS'] = self.paths.system
        
        # Python path for subprocess calls
        os.environ['PYTHONPATH'] = os.pathsep.join([
            str(self.paths.base_path),
            str(self.paths.web_admin),
            os.environ.get('PYTHONPATH', '')
        ])
    
    def reset(self):
        """Reset environment to original state"""
        sys.path = self._original_path.copy()
        self._is_setup = False
        
        # Remove our environment variables
        env_vars = [
            'GRANTSERVICE_BASE',
            'GRANTSERVICE_WEB_ADMIN', 
            'GRANTSERVICE_DATA',
            'GRANTSERVICE_TELEGRAM_BOT',
            'GRANTSERVICE_DB',
            'GRANTSERVICE_OS'
        ]
        for var in env_vars:
            os.environ.pop(var, None)
    
    def get_import_paths(self) -> List[str]:
        """Get list of import paths"""
        return [
            str(self.paths.base_path),
            str(self.paths.web_admin),
            str(self.paths.telegram_bot),
            str(self.paths.agents)
        ]
    
    def print_debug_info(self):
        """Print debug information about environment"""
        print("=" * 60)
        print("GRANTSERVICE ENVIRONMENT DEBUG INFO")
        print("=" * 60)
        print(f"OS: {self.paths.system}")
        print(f"Base Path: {self.paths.base_path}")
        print(f"Web Admin: {self.paths.web_admin}")
        print(f"Data: {self.paths.data}")
        print(f"Telegram Bot: {self.paths.telegram_bot}")
        print("\nPython Path:")
        for i, path in enumerate(sys.path[:10]):
            print(f"  {i}: {path}")
        print("\nEnvironment Variables:")
        for key, value in os.environ.items():
            if 'GRANTSERVICE' in key:
                print(f"  {key}={value}")
        print("=" * 60)


# Singleton instance
_environment: Optional[Environment] = None


def get_environment() -> Environment:
    """Get or create the singleton Environment instance"""
    global _environment
    if _environment is None:
        _environment = Environment()
    return _environment


def setup_environment(verbose: bool = False):
    """Quick function to setup environment"""
    env = get_environment()
    env.setup(verbose=verbose)
    return env