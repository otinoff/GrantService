#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit Tests for File Generators - Iteration 52

Tests for generating human-readable text files from database records.

Author: Claude Code
Created: 2025-10-26
Version: 1.0.0
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.telegram_utils.file_generators import (
    generate_anketa_txt,
    generate_audit_txt,
    generate_grant_txt,
    generate_review_txt
)


class TestGenerateAnketaTxt:
    """Test anketa text file generation"""

    def test_basic_anketa(self):
        """Test: Generate basic anketa file"""

        # Arrange
        anketa_data = {
            'anketa_id': 'ANK123',
            'project_name': 'Школа юных предпринимателей',
            'answers_data': {
                'organization': 'НКО "Будущее"',
                'project_description': 'Образовательная программа для молодежи',
                'problem': 'Недостаток предпринимательских навыков',
                'budget': '500000'
            },
            'completed_at': '2025-10-26 14:30:00'
        }

        # Act
        result = generate_anketa_txt(anketa_data)

        # Assert
        assert 'ЗАПОЛНЕННАЯ АНКЕТА' in result
        assert 'ANK123' in result
        assert 'Школа юных предпринимателей' in result
        assert 'НКО "Будущее"' in result
        assert 'Образовательная программа' in result
        assert len(result) > 500  # Reasonable length

    def test_anketa_with_json_string_answers(self):
        """Test: Anketa with answers as JSON string"""

        # Arrange
        import json
        anketa_data = {
            'anketa_id': 'ANK456',
            'project_name': 'Test Project',
            'answers_data': json.dumps({
                'organization': 'Test Org',
                'budget': '100000'
            }),
            'completed_at': datetime.now()
        }

        # Act
        result = generate_anketa_txt(anketa_data)

        # Assert
        assert 'Test Org' in result
        assert '100000' in result

    def test_anketa_with_minimal_data(self):
        """Test: Anketa with minimal required fields"""

        # Arrange
        anketa_data = {
            'anketa_id': 'ANK789',
            'project_name': 'Minimal Project',
            'answers_data': {},
            'completed_at': datetime.now()
        }

        # Act
        result = generate_anketa_txt(anketa_data)

        # Assert
        assert 'ANK789' in result
        assert 'Minimal Project' in result
        assert 'ЗАПОЛНЕННАЯ АНКЕТА' in result

    def test_anketa_formatting(self):
        """Test: Anketa has proper formatting"""

        # Arrange
        anketa_data = {
            'anketa_id': 'ANK999',
            'project_name': 'Test',
            'answers_data': {'key': 'value'},
            'completed_at': datetime.now()
        }

        # Act
        result = generate_anketa_txt(anketa_data)

        # Assert
        assert '=' * 60 in result  # Header separator
        assert '-' * 60 in result  # Section separator
        assert 'ID анкеты:' in result
        assert 'Дата заполнения:' in result


class TestGenerateAuditTxt:
    """Test audit text file generation"""

    def test_basic_audit(self):
        """Test: Generate basic audit file"""

        # Arrange
        audit_data = {
            'id': 123,
            'completeness_score': 8,
            'clarity_score': 7,
            'feasibility_score': 9,
            'innovation_score': 6,
            'quality_score': 8,
            'average_score': 7.6,
            'approval_status': 'approved',
            'recommendations': {
                'problems': ['Problem 1', 'Problem 2'],
                'suggestions': ['Suggestion 1', 'Suggestion 2']
            },
            'auditor_llm_provider': 'GigaChat',
            'created_at': '2025-10-26 14:35:00'
        }

        # Act
        result = generate_audit_txt(audit_data)

        # Assert
        assert 'РЕЗУЛЬТАТЫ АУДИТА АНКЕТЫ' in result
        assert '7.6/10' in result
        assert 'ОДОБРЕНО' in result
        assert 'Problem 1' in result
        assert 'Suggestion 1' in result
        assert 'GigaChat' in result

    def test_audit_score_visualization(self):
        """Test: Audit contains score bars"""

        # Arrange
        audit_data = {
            'id': 456,
            'completeness_score': 10,
            'clarity_score': 5,
            'feasibility_score': 8,
            'innovation_score': 3,
            'quality_score': 7,
            'average_score': 6.6,
            'approval_status': 'approved',
            'recommendations': {},
            'auditor_llm_provider': 'Claude',
            'created_at': datetime.now()
        }

        # Act
        result = generate_audit_txt(audit_data)

        # Assert
        assert '█' in result  # Filled bar
        assert '░' in result  # Empty bar
        assert 'Полнота информации:' in result
        assert 'Ясность изложения:' in result

    def test_audit_status_labels(self):
        """Test: Audit status labels are correct"""

        statuses = [
            ('approved', '✅ ОДОБРЕНО'),
            ('needs_revision', '⚠️ ТРЕБУЕТСЯ ДОРАБОТКА'),
            ('rejected', '❌ ОТКЛОНЕНО'),
            ('pending', '⏳ ОЖИДАЕТ ПРОВЕРКИ')
        ]

        for status, expected_label in statuses:
            # Arrange
            audit_data = {
                'id': 999,
                'completeness_score': 5,
                'clarity_score': 5,
                'feasibility_score': 5,
                'innovation_score': 5,
                'quality_score': 5,
                'average_score': 5.0,
                'approval_status': status,
                'recommendations': {},
                'auditor_llm_provider': 'Test',
                'created_at': datetime.now()
            }

            # Act
            result = generate_audit_txt(audit_data)

            # Assert
            assert expected_label in result


class TestGenerateGrantTxt:
    """Test grant text file generation"""

    def test_basic_grant(self):
        """Test: Generate basic grant file"""

        # Arrange
        grant_data = {
            'id': 456,
            'grant_id': 'GNT456',
            'grant_title': 'Школа юных предпринимателей',
            'grant_content': 'Full grant content here...',
            'grant_sections': {
                'problem': 'The problem is...',
                'solution': 'The solution is...',
                'budget': 'Budget details...',
            },
            'llm_provider': 'GigaChat',
            'created_at': '2025-10-26 14:40:00'
        }

        # Act
        result = generate_grant_txt(grant_data)

        # Assert
        assert 'ГРАНТОВАЯ ЗАЯВКА' in result
        assert 'GNT456' in result
        assert 'Школа юных предпринимателей' in result
        assert 'The problem is...' in result
        assert 'The solution is...' in result

    def test_grant_sections_formatting(self):
        """Test: Grant sections are properly formatted"""

        # Arrange
        grant_data = {
            'id': 789,
            'grant_id': 'GNT789',
            'grant_title': 'Test Grant',
            'grant_content': 'Content',
            'grant_sections': {
                'problem': 'Problem text',
                'solution': 'Solution text',
                'impact': 'Impact text'
            },
            'llm_provider': 'Claude',
            'created_at': datetime.now()
        }

        # Act
        result = generate_grant_txt(grant_data)

        # Assert
        assert '=== ПРОБЛЕМА ===' in result
        assert '=== РЕШЕНИЕ ===' in result
        assert '=== ОЖИДАЕМЫЙ ЭФФЕКТ ===' in result

    def test_grant_with_only_content(self):
        """Test: Grant without sections uses full content"""

        # Arrange
        grant_data = {
            'id': 111,
            'grant_id': 'GNT111',
            'grant_title': 'Simple Grant',
            'grant_content': 'This is the full grant content without sections.',
            'grant_sections': {},
            'llm_provider': 'Test',
            'created_at': datetime.now()
        }

        # Act
        result = generate_grant_txt(grant_data)

        # Assert
        assert 'This is the full grant content' in result
        assert 'СОДЕРЖАНИЕ ЗАЯВКИ:' in result

    def test_grant_character_count(self):
        """Test: Grant includes character count"""

        # Arrange
        content = 'A' * 30000
        grant_data = {
            'id': 222,
            'grant_id': 'GNT222',
            'grant_title': 'Long Grant',
            'grant_content': content,
            'grant_sections': {},
            'llm_provider': 'Test',
            'created_at': datetime.now()
        }

        # Act
        result = generate_grant_txt(grant_data)

        # Assert
        assert 'Всего символов: 30000' in result


class TestGenerateReviewTxt:
    """Test review text file generation"""

    def test_basic_review(self):
        """Test: Generate basic review file"""

        # Arrange
        review_data = {
            'id': 456,
            'grant_id': 'GNT456',
            'review_score': 8,
            'review_feedback': 'Great grant! Well structured and clear.',
            'final_status': 'approved',
            'updated_at': '2025-10-26 14:45:00'
        }

        # Act
        result = generate_review_txt(review_data)

        # Assert
        assert 'РЕЗУЛЬТАТЫ РЕВЬЮ ГРАНТОВОЙ ЗАЯВКИ' in result
        assert 'GNT456' in result
        assert '8/10' in result
        assert 'ОДОБРЕНО' in result
        assert 'Great grant!' in result

    def test_review_score_visualization(self):
        """Test: Review contains score bar"""

        # Arrange
        review_data = {
            'id': 789,
            'grant_id': 'GNT789',
            'review_score': 7,
            'review_feedback': 'Good work',
            'final_status': 'approved',
            'updated_at': datetime.now()
        }

        # Act
        result = generate_review_txt(review_data)

        # Assert
        assert '█' * 7 in result  # 7 filled bars
        assert '░' * 3 in result  # 3 empty bars

    def test_review_with_json_feedback(self):
        """Test: Review with structured JSON feedback"""

        # Arrange
        import json
        feedback = json.dumps({
            'strengths': ['Good problem definition', 'Clear solution'],
            'weaknesses': ['Budget needs more detail'],
            'recommendations': ['Add timeline', 'Expand team section']
        })

        review_data = {
            'id': 999,
            'grant_id': 'GNT999',
            'review_score': 7,
            'review_feedback': feedback,
            'final_status': 'needs_revision',
            'updated_at': datetime.now()
        }

        # Act
        result = generate_review_txt(review_data)

        # Assert
        assert 'СИЛЬНЫЕ СТОРОНЫ:' in result
        assert 'Good problem definition' in result
        assert 'СЛАБЫЕ СТОРОНЫ:' in result
        assert 'Budget needs more detail' in result
        assert 'РЕКОМЕНДАЦИИ ПО УЛУЧШЕНИЮ:' in result
        assert 'Add timeline' in result

    def test_review_status_labels(self):
        """Test: Review status labels are correct"""

        statuses = [
            ('approved', '✅ ОДОБРЕНО'),
            ('needs_revision', '⚠️ ТРЕБУЕТСЯ ДОРАБОТКА'),
            ('rejected', '❌ ОТКЛОНЕНО'),
            ('pending', '⏳ ОЖИДАЕТ ПРОВЕРКИ')
        ]

        for status, expected_label in statuses:
            # Arrange
            review_data = {
                'id': 111,
                'grant_id': 'GNT111',
                'review_score': 5,
                'review_feedback': 'Feedback',
                'final_status': status,
                'updated_at': datetime.now()
            }

            # Act
            result = generate_review_txt(review_data)

            # Assert
            assert expected_label in result


# Integration tests (require database)
@pytest.mark.integration
class TestFileGeneratorsIntegration:
    """Integration tests with real database data"""

    @pytest.mark.skip(reason="Requires database connection")
    def test_generate_all_files_from_db(self, test_db):
        """Test: Generate all 4 files from real DB data"""

        # Get real anketa
        anketa = test_db.get_session(1)
        anketa_txt = generate_anketa_txt(anketa)
        assert len(anketa_txt) > 100

        # Get real audit
        audit = test_db.get_audit_result(1)
        audit_txt = generate_audit_txt(audit)
        assert len(audit_txt) > 100

        # Get real grant
        grant = test_db.get_grant(1)
        grant_txt = generate_grant_txt(grant)
        assert len(grant_txt) > 100

        # Get real review
        review = test_db.get_grant(1)  # Same table
        review_txt = generate_review_txt(review)
        assert len(review_txt) > 100


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
