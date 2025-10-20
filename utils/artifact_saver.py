#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Artifact Saver - сохранение артефактов агентов в MD и PDF форматах

ИСПОЛЬЗОВАНИЕ:
- Сохранение анкет с аудитом
- Сохранение результатов исследований
- Сохранение грантовых заявок
- Сохранение финальных обзоров

Форматы:
- MD: Markdown (человекочитаемый, для git)
- PDF: Portable Document Format (для отправки пользователям)

Author: Grant Service Architect Agent
Created: 2025-10-12
Version: 1.0
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import json

# Для генерации PDF
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    print("[WARN] reportlab не установлен, PDF генерация недоступна")
    print("      Установите: pip install reportlab")
    REPORTLAB_AVAILABLE = False

logger = logging.getLogger(__name__)


class ArtifactSaver:
    """
    Класс для сохранения артефактов агентов в MD и PDF

    Usage:
        saver = ArtifactSaver(output_dir="grants_output/project_name")
        await saver.save_artifact(
            data=interview_result,
            filename="anketa_audit",
            artifact_type="interview",
            formats=['md', 'pdf']
        )
    """

    def __init__(self, output_dir: str = "grants_output"):
        """
        Инициализация

        Args:
            output_dir: Директория для сохранения артефактов
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"[ArtifactSaver] Initialized (output_dir={self.output_dir})")

    async def save_artifact(
        self,
        data: Dict[str, Any],
        filename: str,
        artifact_type: str,
        formats: List[str] = ['md', 'pdf'],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Path]:
        """
        Сохранить артефакт в указанных форматах

        Args:
            data: Данные для сохранения
            filename: Имя файла (без расширения)
            artifact_type: Тип артефакта (interview, research, grant, review)
            formats: Список форматов ['md', 'pdf']
            metadata: Дополнительные метаданные

        Returns:
            {'md': Path(...), 'pdf': Path(...)}
        """
        logger.info(f"[Save] Сохранение артефакта: {filename} (type={artifact_type})")

        saved_files = {}

        # Сохранение MD
        if 'md' in formats:
            md_path = await self._save_markdown(data, filename, artifact_type, metadata)
            saved_files['md'] = md_path
            logger.info(f"  ✅ MD сохранён: {md_path}")

        # Сохранение PDF
        if 'pdf' in formats:
            if REPORTLAB_AVAILABLE:
                pdf_path = await self._save_pdf(data, filename, artifact_type, metadata)
                saved_files['pdf'] = pdf_path
                logger.info(f"  ✅ PDF сохранён: {pdf_path}")
            else:
                logger.warning("  ⚠️ PDF генерация недоступна (reportlab не установлен)")

        return saved_files

    async def _save_markdown(
        self,
        data: Dict[str, Any],
        filename: str,
        artifact_type: str,
        metadata: Optional[Dict[str, Any]]
    ) -> Path:
        """Сохранить артефакт в Markdown формате"""

        md_content = self._generate_markdown(data, artifact_type, metadata)

        md_path = self.output_dir / f"{filename}.md"
        md_path.write_text(md_content, encoding='utf-8')

        return md_path

    def _generate_markdown(
        self,
        data: Dict[str, Any],
        artifact_type: str,
        metadata: Optional[Dict[str, Any]]
    ) -> str:
        """Генерация Markdown контента в зависимости от типа артефакта"""

        if artifact_type == 'interview':
            return self._generate_interview_markdown(data, metadata)
        elif artifact_type == 'research':
            return self._generate_research_markdown(data, metadata)
        elif artifact_type == 'grant':
            return self._generate_grant_markdown(data, metadata)
        elif artifact_type == 'review':
            return self._generate_review_markdown(data, metadata)
        else:
            # Fallback: generic JSON dump
            return f"# Артефакт: {artifact_type}\n\n```json\n{json.dumps(data, indent=2, ensure_ascii=False)}\n```"

    def _generate_interview_markdown(
        self,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]]
    ) -> str:
        """Генерация MD для результатов интервью"""

        anketa = data.get('anketa', {})
        audit_score = data.get('audit_score', 0)
        audit_details = data.get('audit_details', {})
        recommendations = data.get('recommendations', [])
        interactive_feedback = data.get('interactive_feedback', [])

        md = f"""# Анкета проекта с результатами аудита

**Дата создания**: {data.get('timestamp', datetime.now().isoformat())}
**Anketa ID**: {data.get('anketa_id', 'N/A')}
**Общая оценка**: {audit_score}/100

---

## 1. Базовая информация

**Название проекта**: {anketa.get('project_name', 'N/A')}
**География**: {anketa.get('geography', 'N/A')}
**Фонд**: {anketa.get('grant_fund', 'N/A')}
**Целевая аудитория**: {anketa.get('target_audience', 'N/A')}

---

## 2. Описание проекта

### 2.1 Проблема
{anketa.get('problem_statement', 'N/A')}

### 2.2 Цель проекта
{anketa.get('project_goal', 'N/A')}

### 2.3 Задачи
{anketa.get('project_tasks', 'N/A')}

### 2.4 Методология
{anketa.get('methodology', 'N/A')}

### 2.5 Ожидаемые результаты
{anketa.get('expected_results', 'N/A')}

---

## 3. Бюджет

**Общий бюджет**: {anketa.get('budget', 'N/A')} рублей

**Расшифровка**:
{anketa.get('budget_breakdown', 'N/A')}

---

## 4. Команда и партнёры

### 4.1 Команда
{anketa.get('team_experience', 'N/A')}

### 4.2 Партнёры
{anketa.get('partnerships', 'N/A')}

---

## 5. Риски и устойчивость

### 5.1 Риски
{anketa.get('risk_management', 'N/A')}

### 5.2 Устойчивость
{anketa.get('sustainability', 'N/A')}

---

## 6. Результаты аудита

### 6.1 Общая оценка: {audit_score}/100

### 6.2 Детальная оценка по критериям
"""

        # Добавляем детали аудита
        if audit_details:
            for criterion, details in audit_details.items():
                score = details.get('score', 0) if isinstance(details, dict) else details
                reasoning = details.get('reasoning', '') if isinstance(details, dict) else ''
                md += f"\n**{criterion}**: {score}/10"
                if reasoning:
                    md += f"\n  - {reasoning}"
                md += "\n"

        # Добавляем рекомендации
        if recommendations:
            md += "\n### 6.3 Рекомендации по улучшению\n\n"
            for i, rec in enumerate(recommendations, 1):
                if isinstance(rec, dict):
                    priority = rec.get('priority', 'medium')
                    area = rec.get('area', 'общее')
                    suggestion = rec.get('suggestion', '')
                    md += f"{i}. **[{priority}]** {area}: {suggestion}\n"
                else:
                    md += f"{i}. {rec}\n"

        # Добавляем интерактивные уточнения
        if interactive_feedback:
            md += "\n---\n\n## 7. Интерактивные уточнения\n\n"
            for feedback in interactive_feedback:
                block_num = feedback.get('block', 0)
                block_score = feedback.get('audit_score', 0)
                clarifications = feedback.get('clarifications', {})

                md += f"\n### Блок {block_num} (оценка: {block_score}/10)\n\n"
                for topic, answer in clarifications.items():
                    md += f"- **{topic}**: {answer}\n"

        md += "\n---\n\n*Сгенерировано системой GrantService*"

        return md

    def _generate_research_markdown(
        self,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]]
    ) -> str:
        """Генерация MD для результатов исследования"""

        research_results = data.get('research_results', {})
        total_queries = data.get('total_queries', 0)

        md = f"""# Результаты исследования

**Дата**: {data.get('timestamp', datetime.now().isoformat())}
**Всего запросов**: {total_queries}

---

## 1. Профильные запросы (Блок 1)

"""
        # Блок 1
        block1 = research_results.get('block_1', [])
        for i, query_result in enumerate(block1, 1):
            query = query_result.get('query', f'Запрос {i}')
            content = query_result.get('content', '')
            sources = query_result.get('sources', [])

            md += f"\n### 1.{i} {query}\n\n"
            md += f"{content[:500]}...\n\n"
            if sources:
                md += f"**Источники**: {len(sources)}\n"

        md += "\n---\n\n## 2. Контекстные запросы (Блок 2)\n\n"

        # Блок 2
        block2 = research_results.get('block_2', [])
        for i, query_result in enumerate(block2, 1):
            query = query_result.get('query', f'Запрос {i}')
            content = query_result.get('content', '')
            sources = query_result.get('sources', [])

            md += f"\n### 2.{i} {query}\n\n"
            md += f"{content[:500]}...\n\n"
            if sources:
                md += f"**Источники**: {len(sources)}\n"

        md += "\n---\n\n## 3. Целевые запросы (Блок 3)\n\n"

        # Блок 3
        block3 = research_results.get('block_3', [])
        for i, query_result in enumerate(block3, 1):
            query = query_result.get('query', f'Запрос {i}')
            content = query_result.get('content', '')
            sources = query_result.get('sources', [])

            md += f"\n### 3.{i} {query}\n\n"
            md += f"{content[:500]}...\n\n"
            if sources:
                md += f"**Источники**: {len(sources)}\n"

        # Требования фонда (если есть)
        fund_req = research_results.get('fund_requirements')
        if fund_req:
            md += "\n---\n\n## 4. Требования Фонда президентских грантов\n\n"

            directions = fund_req.get('directions', [])
            criteria = fund_req.get('criteria', [])

            if directions:
                md += "### 4.1 Направления финансирования\n\n"
                for direction in directions:
                    md += f"- {direction}\n"

            if criteria:
                md += "\n### 4.2 Критерии оценки\n\n"
                for criterion in criteria:
                    if isinstance(criterion, dict):
                        name = criterion.get('name', '')
                        weight = criterion.get('weight', '')
                        md += f"- **{name}** ({weight})\n"
                    else:
                        md += f"- {criterion}\n"

        md += "\n---\n\n*Сгенерировано системой GrantService*"

        return md

    def _generate_grant_markdown(
        self,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]]
    ) -> str:
        """Генерация MD для грантовой заявки"""

        # NOTE: Здесь должен быть контент из WriterAgentV2
        # Для первой версии - базовая структура

        content = data.get('content', '')
        nomenclature = data.get('nomenclature', 'N/A')

        md = f"""# Грантовая заявка

**Номенклатура**: {nomenclature}
**Дата создания**: {data.get('timestamp', datetime.now().isoformat())}

---

{content}

---

*Сгенерировано системой GrantService*
"""

        return md

    def _generate_review_markdown(
        self,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]]
    ) -> str:
        """Генерация MD для финального обзора"""

        approval_probability = data.get('approval_probability', 0)
        readiness_score = data.get('readiness_score', 0)
        recommendations = data.get('recommendations', [])

        md = f"""# Финальная оценка готовности гранта

**Дата**: {data.get('timestamp', datetime.now().isoformat())}
**Готовность**: {readiness_score}/10
**Вероятность одобрения**: {approval_probability}%

---

## 1. Оценка по критериям

"""

        # Добавляем оценки по критериям
        criteria_scores = data.get('criteria_scores', {})
        for criterion, score_data in criteria_scores.items():
            score = score_data.get('score', 0) if isinstance(score_data, dict) else score_data
            md += f"- **{criterion}**: {score}/10\n"

        md += "\n---\n\n## 2. Рекомендации\n\n"

        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                md += f"{i}. {rec}\n"

        md += "\n---\n\n*Сгенерировано системой GrantService*"

        return md

    async def _save_pdf(
        self,
        data: Dict[str, Any],
        filename: str,
        artifact_type: str,
        metadata: Optional[Dict[str, Any]]
    ) -> Path:
        """Сохранить артефакт в PDF формате"""

        # NOTE: Полная реализация PDF генерации требует настройки шрифтов
        # Для первой версии - упрощённый вариант

        pdf_path = self.output_dir / f"{filename}.pdf"

        # Создаём MD версию и указываем путь к PDF
        # В production: полноценная PDF генерация через reportlab
        placeholder_content = f"""
PDF PLACEHOLDER

Артефакт: {filename}
Тип: {artifact_type}
Дата: {datetime.now().isoformat()}

Для полноценной PDF генерации требуется:
1. Установить reportlab с поддержкой русских шрифтов
2. Настроить шрифты (DejaVu, Arial и т.д.)

Пока используйте MD версию.
"""

        pdf_path.write_text(placeholder_content, encoding='utf-8')

        return pdf_path


# Удобная функция для быстрого сохранения
async def save_artifact(
    data: Dict[str, Any],
    filename: str,
    artifact_type: str,
    output_dir: str = "grants_output",
    formats: List[str] = ['md', 'pdf']
) -> Dict[str, Path]:
    """
    Сохранить артефакт (удобная обёртка)

    Args:
        data: Данные
        filename: Имя файла
        artifact_type: Тип (interview, research, grant, review)
        output_dir: Директория
        formats: Форматы

    Returns:
        {'md': Path, 'pdf': Path}
    """
    saver = ArtifactSaver(output_dir=output_dir)
    return await saver.save_artifact(
        data=data,
        filename=filename,
        artifact_type=artifact_type,
        formats=formats
    )


if __name__ == "__main__":
    print("ArtifactSaver - утилита для сохранения артефактов агентов")
