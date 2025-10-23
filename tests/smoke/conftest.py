"""
Conftest for smoke tests - минимальная конфигурация

Smoke tests не требуют фикстур из основного conftest.py,
поэтому создаём пустой conftest чтобы pytest не загружал родительский.
"""

import pytest


# Empty conftest to prevent pytest from loading parent conftest.py
# Smoke tests are standalone and don't need database fixtures
