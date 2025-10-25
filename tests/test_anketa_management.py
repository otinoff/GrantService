#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Iteration 35 - Anketa Management

Unit tests for:
- Database methods (get_user_anketas, delete_anketa, get_audit_by_session_id, get_audit_by_anketa_id)
- AnketaManagementHandler functionality
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'telegram-bot'))

import pytest
from unittest.mock import Mock, MagicMock, patch
from data.database.models import GrantServiceDatabase


class TestDatabaseMethods:
    """Unit tests for database methods"""

    def test_get_user_anketas_method_exists(self):
        """Check that get_user_anketas method exists"""
        db = GrantServiceDatabase()
        assert hasattr(db, 'get_user_anketas')
        assert callable(db.get_user_anketas)

    def test_delete_anketa_method_exists(self):
        """Check that delete_anketa method exists"""
        db = GrantServiceDatabase()
        assert hasattr(db, 'delete_anketa')
        assert callable(db.delete_anketa)

    def test_get_audit_by_session_id_method_exists(self):
        """Check that get_audit_by_session_id method exists"""
        db = GrantServiceDatabase()
        assert hasattr(db, 'get_audit_by_session_id')
        assert callable(db.get_audit_by_session_id)

    def test_get_audit_by_anketa_id_method_exists(self):
        """Check that get_audit_by_anketa_id method exists"""
        db = GrantServiceDatabase()
        assert hasattr(db, 'get_audit_by_anketa_id')
        assert callable(db.get_audit_by_anketa_id)


class TestGrantHandlerAuditIntegration:
    """Tests for audit integration in GrantHandler"""

    def test_grant_handler_has_check_or_run_audit(self):
        """Check that GrantHandler has _check_or_run_audit method"""
        from handlers.grant_handler import GrantHandler

        # Mock database
        mock_db = Mock()
        handler = GrantHandler(db=mock_db)

        assert hasattr(handler, '_check_or_run_audit')
        assert callable(handler._check_or_run_audit)


class TestAnketaManagementHandler:
    """Tests for AnketaManagementHandler"""

    def test_handler_initialization(self):
        """Test that AnketaManagementHandler can be initialized"""
        from handlers.anketa_management_handler import AnketaManagementHandler

        # Mock database
        mock_db = Mock()
        handler = AnketaManagementHandler(db=mock_db)

        assert handler is not None
        assert handler.db == mock_db

    def test_handler_has_my_anketas(self):
        """Check that handler has my_anketas method"""
        from handlers.anketa_management_handler import AnketaManagementHandler

        mock_db = Mock()
        handler = AnketaManagementHandler(db=mock_db)

        assert hasattr(handler, 'my_anketas')
        assert callable(handler.my_anketas)

    def test_handler_has_delete_anketa(self):
        """Check that handler has delete_anketa method"""
        from handlers.anketa_management_handler import AnketaManagementHandler

        mock_db = Mock()
        handler = AnketaManagementHandler(db=mock_db)

        assert hasattr(handler, 'delete_anketa')
        assert callable(handler.delete_anketa)

    def test_handler_has_audit_anketa(self):
        """Check that handler has audit_anketa method"""
        from handlers.anketa_management_handler import AnketaManagementHandler

        mock_db = Mock()
        handler = AnketaManagementHandler(db=mock_db)

        assert hasattr(handler, 'audit_anketa')
        assert callable(handler.audit_anketa)

    def test_handler_has_callback_handler(self):
        """Check that handler has callback_handler method"""
        from handlers.anketa_management_handler import AnketaManagementHandler

        mock_db = Mock()
        handler = AnketaManagementHandler(db=mock_db)

        assert hasattr(handler, 'callback_handler')
        assert callable(handler.callback_handler)


# ========== MANUAL TESTING CHECKLIST ==========
"""
MANUAL TESTING CHECKLIST (To be executed locally before deploy):

1. Database Methods:
   [ ] Test get_user_anketas() returns empty list for user with no anketas
   [ ] Test get_user_anketas() returns anketas with audit data
   [ ] Test delete_anketa() blocks deletion of anketa owned by different user
   [ ] Test delete_anketa() successfully deletes owned anketa
   [ ] Test get_audit_by_session_id() returns None for non-existent session
   [ ] Test get_audit_by_session_id() returns audit data
   [ ] Test get_audit_by_anketa_id() works with JOIN

2. Commands:
   [ ] /my_anketas shows message for user with no anketas
   [ ] /my_anketas displays list with audit scores
   [ ] /delete_anketa shows selection UI
   [ ] /delete_anketa requires confirmation
   [ ] /delete_anketa actually deletes anketa
   [ ] /audit_anketa shows selection UI
   [ ] /audit_anketa runs AuditorAgent
   [ ] /audit_anketa displays formatted results

3. Integration:
   [ ] /generate_grant checks audit
   [ ] /generate_grant blocks if status = 'rejected'
   [ ] /generate_grant warns if status = 'needs_revision'
   [ ] /generate_grant proceeds if status = 'approved'
   [ ] Audit result is cached (no re-run)

4. Edge Cases:
   [ ] No anketas - proper message displayed
   [ ] Multiple anketas - pagination needed?
   [ ] Delete in-progress anketa - should block or allow?
   [ ] Audit while generating - should block?
   [ ] Re-audit - creates new or updates existing?
   [ ] Delete audited anketa - cascade works?

5. Error Handling:
   [ ] All database errors caught and logged
   [ ] User receives clear error messages
   [ ] No crashes from invalid input

6. UI/UX:
   [ ] All buttons work
   [ ] Callback handlers respond correctly
   [ ] Messages are clear and helpful
   [ ] Emoji display correctly (or use text fallback)
"""

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
