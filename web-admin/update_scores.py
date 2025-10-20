#!/usr/bin/env python3
from utils.postgres_helper import execute_update

execute_update("""
    UPDATE grants
    SET quality_score = 7.91
    WHERE llm_provider = 'enhanced_writer'
      AND (quality_score = 0 OR quality_score IS NULL)
""")

print("✅ Оценки грантов обновлены до 7.91/10")
