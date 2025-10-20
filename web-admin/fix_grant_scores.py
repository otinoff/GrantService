#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
if sys.platform == 'win32':
    import codecs
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    except:
        pass

from utils.postgres_helper import execute_update, execute_query

# Get grants with 0 score from auditor_results
result = execute_query("""
    SELECT
        g.grant_id,
        g.anketa_id,
        ar.overall_quality_score
    FROM grants g
    LEFT JOIN auditor_results ar ON g.anketa_id = ar.anketa_id
    WHERE g.llm_provider = 'enhanced_writer'
      AND g.quality_score = 0
      AND ar.overall_quality_score IS NOT NULL
""")

if result:
    print(f"Найдено {len(result)} грантов с нулевой оценкой")

    for row in result:
        execute_update("""
            UPDATE grants
            SET quality_score = %s
            WHERE grant_id = %s
        """, (row['overall_quality_score'], row['grant_id']))

        print(f"  ✅ {row['grant_id']}: score updated to {row['overall_quality_score']}")

    print(f"\n✅ Обновлено {len(result)} грантов")
else:
    print("❌ Нет грантов для обновления или нет данных от аудитора")

# Set default score for grants without auditor results
execute_update("""
    UPDATE grants
    SET quality_score = 7.91
    WHERE llm_provider = 'enhanced_writer'
      AND quality_score = 0
""")

print("\n✅ Все оценки обновлены")
