-- Migration 008: Upgrade researcher_research JSONB structure and indexes
-- Created: 2025-10-08
-- Description: Enhance JSONB indexes and add detailed documentation for research_results structure
-- Purpose: Support 27 expert queries (block1: 10, block2: 10, block3: 7) for grant research

BEGIN;

-- ============================================================================
-- STEP 1: Verify table and column existence
-- ============================================================================

DO $$
BEGIN
    -- Check if table exists
    IF NOT EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name = 'researcher_research'
    ) THEN
        RAISE EXCEPTION 'Table researcher_research does not exist';
    END IF;

    -- Check if research_results column exists
    IF NOT EXISTS (
        SELECT FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'researcher_research'
        AND column_name = 'research_results'
    ) THEN
        RAISE EXCEPTION 'Column research_results does not exist';
    END IF;

    RAISE NOTICE 'Pre-flight checks passed: table and column exist';
END $$;


-- ============================================================================
-- STEP 2: Ensure research_results is JSONB type
-- ============================================================================

-- Check current type and convert if needed
DO $$
DECLARE
    current_type TEXT;
BEGIN
    SELECT data_type INTO current_type
    FROM information_schema.columns
    WHERE table_schema = 'public'
    AND table_name = 'researcher_research'
    AND column_name = 'research_results';

    IF current_type = 'text' THEN
        RAISE NOTICE 'Converting research_results from TEXT to JSONB...';
        ALTER TABLE researcher_research
        ALTER COLUMN research_results TYPE JSONB
        USING CASE
            WHEN research_results IS NULL THEN NULL::JSONB
            WHEN research_results = '' THEN NULL::JSONB
            ELSE research_results::JSONB
        END;
        RAISE NOTICE 'Conversion completed';
    ELSIF current_type = 'jsonb' THEN
        RAISE NOTICE 'research_results is already JSONB type, skipping conversion';
    ELSE
        RAISE EXCEPTION 'Unexpected type for research_results: %', current_type;
    END IF;
END $$;


-- ============================================================================
-- STEP 3: Create/Recreate optimized JSONB indexes
-- ============================================================================

-- Drop existing GIN index if exists (will be recreated with better name)
DROP INDEX IF EXISTS idx_research_results_gin;

-- Create comprehensive GIN index for JSONB operations
-- Supports: @>, @?, ?&, ? operators for fast JSONB queries
CREATE INDEX IF NOT EXISTS idx_researcher_results_gin
ON researcher_research USING gin(research_results jsonb_path_ops);

-- Create specific indexes for common queries
CREATE INDEX IF NOT EXISTS idx_researcher_status_completed
ON researcher_research(status, completed_at)
WHERE status = 'completed';

CREATE INDEX IF NOT EXISTS idx_researcher_anketa_status
ON researcher_research(anketa_id, status);

CREATE INDEX IF NOT EXISTS idx_researcher_completed_date
ON researcher_research(completed_at DESC)
WHERE completed_at IS NOT NULL;

-- Create index for metadata queries
CREATE INDEX IF NOT EXISTS idx_researcher_metadata_gin
ON researcher_research USING gin(metadata jsonb_path_ops);

-- Note: Indexes created successfully


-- ============================================================================
-- STEP 4: Add comprehensive table and column comments
-- ============================================================================

COMMENT ON TABLE researcher_research IS
'AI research results for grant applications using 27 expert queries
- Block 1 (10 queries): Problem analysis with official statistics
- Block 2 (10 queries): Geography and target audience analysis
- Block 3 (7 queries): Goals and tasks formulation
Total expected sources: 45+, Total expected quotes: 60+';

COMMENT ON COLUMN researcher_research.research_results IS
'JSONB structure containing 27 expert research queries results:

Structure:
{
  "block1_problem": {
    "summary": "Extended summary up to 30 sentences",
    "key_facts": [
      {
        "fact": "Description",
        "source": "rosstat.gov.ru/...",
        "date": "2024-03-15",
        "metric": 47,
        "unit": "institutions",
        "region_level": "subject"
      }
    ],
    "dynamics_table": {
      "indicators": [
        {
          "name": "Indicator name",
          "region": [values for 3 years],
          "russia": [values for 3 years],
          "leader": [values for 3 years],
          "years": [2022, 2023, 2024]
        }
      ]
    },
    "programs": [
      {
        "name": "National project name",
        "kpi": "Target KPI",
        "document": "Document name",
        "section": "Section reference",
        "url": "Link to document",
        "project_contribution": "How project helps"
      }
    ],
    "success_cases": [
      {
        "title": "Case title",
        "result": "Achieved result",
        "source": "Source URL",
        "quote": "Direct quote"
      }
    ],
    "damage_cases": [
      {
        "title": "Problem description",
        "indicator": "Metric",
        "consequence": "Negative impact",
        "source": "Source URL"
      }
    ],
    "queries_used": ["Query 1", "Query 2", ...]
  },

  "block2_geography": {
    "summary": "Summary up to 20 sentences",
    "key_facts": [...],
    "comparison_table": {
      "region": {...},
      "russia": {...},
      "leader": {...}
    },
    "target_audience": {
      "age_range": "6-17",
      "total_count": 85000,
      "affected_by_problem": 46750,
      "percentage": 55,
      "calculation_method": "Methodology"
    },
    "infrastructure": {
      "sports_schools": 47,
      "coaches": 320,
      "facilities": 150,
      "accessibility_gaps": "Description"
    },
    "scalability": [...],
    "queries_used": [...]
  },

  "block3_goals": {
    "summary": "Summary 5-7 sentences",
    "key_tasks": [
      {
        "task": "Task description",
        "activities": ["Activity 1", "Activity 2"],
        "kpi": {
          "name": "KPI name",
          "target": 5000,
          "unit": "people",
          "period": "12 months"
        }
      }
    ],
    "main_goal_variants": [
      {
        "variant": 1,
        "text": "SMART goal text",
        "smart_check": {
          "specific": true,
          "measurable": true,
          "achievable": true,
          "relevant": true,
          "timebound": true
        }
      }
    ],
    "queries_used": [...]
  },

  "metadata": {
    "total_queries": 27,
    "sources_count": 45,
    "quotes_count": 68,
    "blocks": {
      "block1": {"queries": 10, "sources": 18, "processing_time": 120},
      "block2": {"queries": 10, "sources": 20, "processing_time": 115},
      "block3": {"queries": 7, "sources": 7, "processing_time": 80}
    },
    "total_processing_time": 315,
    "llm_provider": "claude_code",
    "model": "sonnet-4.5",
    "tokens_used": 45000
  }
}

Query examples:
- block1_problem.key_facts @> ''[{"region_level": "subject"}]''
- research_results->''metadata''->''total_queries'' = ''27''
- research_results @? ''$.block1_problem.success_cases[*] ? (@.source like_regex "rosstat")''';

COMMENT ON COLUMN researcher_research.metadata IS
'Additional metadata about research execution:
- llm_provider: AI provider used (claude_code, gigachat, perplexity)
- model: Specific model version
- tokens_used: Total tokens consumed
- execution_time: Processing time in seconds
- query_statistics: Per-block query statistics
- error_logs: Any errors encountered during research';

COMMENT ON COLUMN researcher_research.status IS
'Research execution status:
- pending: Queued for execution
- processing: Currently executing 27 queries
- completed: All queries finished successfully
- error: Failed with errors (see metadata for details)';

-- Note: Documentation comments added successfully


-- ============================================================================
-- STEP 5: Add validation constraint for completed status
-- ============================================================================

-- Ensure completed status has research_results
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'check_completed_has_results'
    ) THEN
        ALTER TABLE researcher_research
        ADD CONSTRAINT check_completed_has_results
        CHECK (
            status != 'completed' OR
            (research_results IS NOT NULL AND research_results != 'null'::jsonb)
        );
        RAISE NOTICE 'Validation constraint added';
    ELSE
        RAISE NOTICE 'Validation constraint already exists';
    END IF;
END $$;


-- ============================================================================
-- STEP 6: Analyze table for query optimizer
-- ============================================================================

ANALYZE researcher_research;

-- Note: Table analysis completed


-- ============================================================================
-- STEP 7: Display migration summary
-- ============================================================================

DO $$
DECLARE
    total_records INTEGER;
    completed_records INTEGER;
    avg_sources INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_records FROM researcher_research;
    SELECT COUNT(*) INTO completed_records FROM researcher_research WHERE status = 'completed';

    RAISE NOTICE '========================================';
    RAISE NOTICE 'Migration 008 completed successfully';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Total research records: %', total_records;
    RAISE NOTICE 'Completed research records: %', completed_records;
    RAISE NOTICE 'JSONB indexes created: 5';
    RAISE NOTICE 'Documentation comments added: 4';
    RAISE NOTICE '========================================';
END $$;

COMMIT;


-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify JSONB type
SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'researcher_research'
AND column_name IN ('research_results', 'metadata')
ORDER BY column_name;

-- Verify indexes
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'researcher_research'
AND indexname LIKE '%researcher%'
ORDER BY indexname;

-- Display sample research_results structure (if data exists)
SELECT
    research_id,
    status,
    jsonb_typeof(research_results) as results_type,
    jsonb_object_keys(research_results) as top_level_keys
FROM researcher_research
WHERE research_results IS NOT NULL
LIMIT 1;
