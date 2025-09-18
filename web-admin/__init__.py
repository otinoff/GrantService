"""
Web Admin Module for GrantService
"""

# Экспортируем необходимые компоненты
from .auth_pages import PageAuth, check_auth, check_role

__all__ = ['PageAuth', 'check_auth', 'check_role']