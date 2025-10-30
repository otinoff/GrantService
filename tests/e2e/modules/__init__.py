"""
E2E Test Modules for GrantService

Модульное тестирование агентов - переиспользуемые компоненты
Iteration 66: E2E Test Suite

Architecture:
- Each module tests ONE production agent
- Modules are reusable building blocks
- Main E2E test assembles modules into workflow

Created: 2025-10-29
Based on: Iterations 54, 58, 60, 63, 65 (successful implementations)
"""

from .interviewer_module import InterviewerTestModule
from .auditor_module import AuditorTestModule
from .researcher_module import ResearcherTestModule
from .writer_module import WriterTestModule
from .reviewer_module import ReviewerTestModule

__all__ = [
    'InterviewerTestModule',
    'AuditorTestModule',
    'ResearcherTestModule',
    'WriterTestModule',
    'ReviewerTestModule',
]
