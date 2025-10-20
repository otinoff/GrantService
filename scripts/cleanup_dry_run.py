"""
Database Cleanup - DRY RUN (without actual deletion)
Показывает что будет удалено, но не удаляет
"""

from database_garbage_collection import cleanup_database

if __name__ == '__main__':
    print("\nZAPUSK DRY RUN - BEZ REALNOGO UDALENIYA\n")
    cleanup_database(dry_run=True)
