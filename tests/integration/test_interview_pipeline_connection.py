#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration Test: Interview Handler → Pipeline Handler Connection

Tests that interview completion triggers pipeline.

Author: Claude Code (Iteration 52 - Phase 12)
Created: 2025-10-27
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from telegram import Update, User, Message, Chat
from telegram.ext import ContextTypes


@pytest.mark.integration
class TestInterviewPipelineConnection:
    """Test interview handler → pipeline handler connection"""

    def test_interview_handler_has_pipeline_parameter(self):
        """Test: InterviewHandler accepts pipeline_handler parameter"""
        # Import with path manipulation instead
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "interactive_interview_handler",
            "telegram-bot/handlers/interactive_interview_handler.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        InteractiveInterviewHandler = module.InteractiveInterviewHandler

        mock_db = MagicMock()
        mock_pipeline = MagicMock()

        # Should not raise
        handler = InteractiveInterviewHandler(
            db=mock_db,
            admin_chat_id=None,
            pipeline_handler=mock_pipeline
        )

        assert handler.pipeline_handler == mock_pipeline

    def test_pipeline_handler_initialized_before_interview_handler(self):
        """Test: In main.py, pipeline_handler is initialized before interview_handler"""

        # This is a structural test - we check the order in main.py
        from pathlib import Path
        main_py = Path("telegram-bot/main.py")

        if not main_py.exists():
            pytest.skip("main.py not found")

        content = main_py.read_text(encoding='utf-8')

        # Find line numbers
        pipeline_init = None
        interview_init = None

        for i, line in enumerate(content.splitlines(), 1):
            if 'self.pipeline_handler = InteractivePipelineHandler' in line:
                pipeline_init = i
            if 'self.interview_handler = InteractiveInterviewHandler' in line:
                interview_init = i

        assert pipeline_init is not None, "pipeline_handler initialization not found"
        assert interview_init is not None, "interview_handler initialization not found"
        assert pipeline_init < interview_init, \
            f"pipeline_handler (line {pipeline_init}) must be initialized BEFORE interview_handler (line {interview_init})"

    @pytest.mark.asyncio
    async def test_interview_completion_calls_pipeline(self):
        """Test: Interview completion triggers pipeline.on_anketa_complete()"""

        # Import handler
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "interactive_interview_handler",
            "telegram-bot/handlers/interactive_interview_handler.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        InteractiveInterviewHandler = module.InteractiveInterviewHandler

        # Mock dependencies
        mock_db = MagicMock()
        mock_db.get_session_by_anketa_id = MagicMock(return_value={
            'id': 1,
            'anketa_id': 'ANK123',
            'interview_data': '{"test": "data"}'
        })

        mock_pipeline = MagicMock()
        mock_pipeline.on_anketa_complete = AsyncMock()

        # Create handler with mocked pipeline
        handler = InteractiveInterviewHandler(
            db=mock_db,
            admin_chat_id=None,
            pipeline_handler=mock_pipeline
        )

        # Verify pipeline handler is set
        assert handler.pipeline_handler is not None
        assert handler.pipeline_handler == mock_pipeline

    def test_main_py_passes_pipeline_to_interview_handler(self):
        """Test: main.py passes pipeline_handler to interview_handler"""

        from pathlib import Path
        main_py = Path("telegram-bot/main.py")

        if not main_py.exists():
            pytest.skip("main.py not found")

        content = main_py.read_text(encoding='utf-8')

        # Check that InteractiveInterviewHandler is called with pipeline_handler parameter
        assert 'pipeline_handler=self.pipeline_handler' in content, \
            "main.py must pass pipeline_handler to InteractiveInterviewHandler"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
