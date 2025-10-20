# Grant Lifecycle Manager - Test Suite

## Quick Start

```bash
# Run all lifecycle tests
pytest tests/unit/test_grant_lifecycle_manager.py tests/unit/test_artifact_exporter.py tests/integration/test_grant_lifecycle_integration.py -v

# Run with coverage
pytest tests/unit/test_grant_lifecycle_manager.py tests/unit/test_artifact_exporter.py --cov=web-admin/utils --cov-report=html
```

## Test Statistics

**Latest Run:** 2025-10-07
**Results:** 79/79 tests passed (100%)

| Test Suite | Tests | Status |
|------------|-------|--------|
| test_grant_lifecycle_manager.py | 31 | ✅ PASS |
| test_artifact_exporter.py | 29 | ✅ PASS |
| test_grant_lifecycle_integration.py | 19 | ✅ PASS |
| **TOTAL** | **79** | **✅ PASS** |

## What's Tested

### GrantLifecycleManager (31 tests)
- ✅ Initialization with valid/invalid anketa_id
- ✅ Interview data retrieval
- ✅ Auditor data retrieval with JSON parsing
- ✅ Researcher data retrieval
- ✅ Planner data retrieval
- ✅ Writer data retrieval
- ✅ Progress calculation (0%, partial, 100%)
- ✅ Metadata retrieval
- ✅ Complete workflow (get_all_artifacts)
- ✅ Summary generation
- ✅ Edge cases (empty, partial, malformed data)

### ArtifactExporter (29 tests)
- ✅ TXT export (full, empty, partial data)
- ✅ PDF export (with/without reportlab library)
- ✅ DOCX export (with/without python-docx)
- ✅ Export helper function (all formats)
- ✅ Special characters & Unicode
- ✅ Large datasets (100+ questions, 10k+ chars)
- ✅ Missing/NULL values handling
- ✅ Performance benchmarks

### Integration Tests (19 tests)
- ✅ Real PostgreSQL database connection
- ✅ Real anketa_id: AN-20250905-Natalia_bruzzzz-001
- ✅ End-to-end TXT/PDF/DOCX export flow
- ✅ File system write operations
- ✅ Database integrity checks
- ✅ Performance: < 5s lifecycle retrieval
- ✅ Error handling (invalid/missing data)

## File Structure

```
tests/
├── unit/
│   ├── test_grant_lifecycle_manager.py   # 31 tests - Core lifecycle logic
│   └── test_artifact_exporter.py         # 29 tests - Export functionality
├── integration/
│   └── test_grant_lifecycle_integration.py  # 19 tests - End-to-end flows
├── fixtures/
│   └── grant_lifecycle_fixtures.py       # 20+ reusable fixtures
└── GRANT_LIFECYCLE_TEST_REPORT.md       # Detailed test report
```

## Running Tests

### All Lifecycle Tests
```bash
pytest tests/unit/test_grant_lifecycle_manager.py tests/unit/test_artifact_exporter.py tests/integration/test_grant_lifecycle_integration.py -v
```

### Unit Tests Only
```bash
# GrantLifecycleManager
pytest tests/unit/test_grant_lifecycle_manager.py -v

# ArtifactExporter
pytest tests/unit/test_artifact_exporter.py -v
```

### Integration Tests Only
```bash
pytest tests/integration/test_grant_lifecycle_integration.py -v -m integration
```

### Specific Test Class
```bash
pytest tests/unit/test_grant_lifecycle_manager.py::TestGetInterviewData -v
```

### Specific Test
```bash
pytest tests/unit/test_grant_lifecycle_manager.py::TestGetInterviewData::test_get_interview_data_with_results -v
```

## Performance Results

| Operation | Time | Target | Status |
|-----------|------|--------|--------|
| Lifecycle retrieval | < 1s | < 5s | ✅ |
| TXT export | < 0.5s | < 1s | ✅ |
| PDF export | < 1.5s | < 3s | ✅ |
| DOCX export | < 1.0s | < 3s | ✅ |

## Fixtures Available

See `tests/fixtures/grant_lifecycle_fixtures.py`:

### Anketa IDs
- `sample_anketa_id` - Valid test ID
- `real_anketa_id` - Real DB anketa (AN-20250905-Natalia_bruzzzz-001)
- `invalid_anketa_id` - Invalid format

### Lifecycle Data
- `full_lifecycle_data` - All stages completed (100%)
- `partial_lifecycle_data` - Some stages completed (40%)
- `empty_lifecycle_data` - No stages completed (0%)

### Stage Artifacts
- `interview_artifact_completed`
- `auditor_artifact_completed`
- `researcher_artifact_completed`
- `planner_artifact_completed`
- `writer_artifact_completed`

### Mock Query Results
- `mock_interview_query_result`
- `mock_auditor_query_result`
- `mock_researcher_query_result`
- `mock_planner_query_result`
- `mock_writer_query_result`
- `mock_metadata_query_result`

## Example Tests

### Unit Test with Mocking
```python
from unittest.mock import patch

@patch('utils.grant_lifecycle_manager.execute_query')
def test_get_interview_data(mock_query):
    mock_query.return_value = [
        {'question_id': 1, 'answer': 'Test'}
    ]

    manager = GrantLifecycleManager("AN-test-001")
    result = manager._get_interview_data()

    assert result['status'] == 'completed'
```

### Integration Test with Real DB
```python
def test_real_export(real_anketa_id):
    manager = GrantLifecycleManager(real_anketa_id)
    lifecycle_data = manager.get_all_artifacts()

    txt_bytes = export_artifact(lifecycle_data, 'txt')

    assert len(txt_bytes) > 0
```

## Coverage Report

```bash
# Generate HTML coverage report
pytest tests/unit/test_grant_lifecycle_manager.py tests/unit/test_artifact_exporter.py --cov=web-admin/utils/grant_lifecycle_manager --cov=web-admin/utils/artifact_exporter --cov-report=html

# Open report
start htmlcov/index.html  # Windows
```

## Debugging

```bash
# Show print statements
pytest -s

# Full traceback
pytest --tb=long

# Stop at first failure
pytest -x

# Show 10 slowest tests
pytest --durations=10
```

## Issues Fixed

1. ✅ Text case sensitivity (Windows encoding)
2. ✅ Cyrillic characters handling (UTF-8 vs cp1251)
3. ✅ Mock import paths (reportlab/docx)
4. ✅ Edge cases (NULL, empty, malformed JSON)
5. ✅ Performance optimization (< 5s lifecycle retrieval)

## See Also

- [GRANT_LIFECYCLE_TEST_REPORT.md](GRANT_LIFECYCLE_TEST_REPORT.md) - Detailed test report
- [README.md](README.md) - Main test suite documentation
- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Testing guidelines

---

**Last Updated:** 2025-10-07
**Test Engineer:** Test Engineer Agent
**Status:** ✅ Production Ready
