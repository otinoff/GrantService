#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core module for GrantService
Provides centralized configuration and environment management
"""

from .paths import PathManager, get_path_manager
from .environment import Environment, get_environment, setup_environment
from .config import Config, get_config

# Initialize core components
paths = get_path_manager()
environment = get_environment()
config = get_config()

# Export main functions
def setup():
    """Setup the application environment"""
    environment.setup()
    return config, paths

__all__ = [
    'Config', 'Environment', 'PathManager',
    'config', 'paths', 'environment',
    'get_config', 'get_path_manager', 'get_environment',
    'setup', 'setup_environment'
]