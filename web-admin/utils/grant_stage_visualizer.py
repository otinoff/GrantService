#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Grant Stage Visualizer - визуализация прогресса грантовой заявки через этапы

Создает визуальный timeline для отображения текущего состояния заявки в Streamlit UI
"""

import streamlit as st
from typing import Dict, List, Any


class GrantStageVisualizer:
    """Визуализатор этапов грантовой заявки для Streamlit"""

    # Определение этапов
    STAGES = [
        {
            'key': 'interview',
            'name': 'Интервью',
            'emoji': '📝',
            'description': 'Сбор информации о проекте (24 вопроса)'
        },
        {
            'key': 'auditor',
            'name': 'Аудит',
            'emoji': '🔍',
            'description': 'Оценка качества и реализуемости проекта'
        },
        {
            'key': 'researcher',
            'name': 'Исследование',
            'emoji': '📊',
            'description': 'Анализ рынка и конкурентов'
        },
        {
            'key': 'planner',
            'name': 'Планирование',
            'emoji': '📋',
            'description': 'Структурирование заявки'
        },
        {
            'key': 'writer',
            'name': 'Написание',
            'emoji': '✍️',
            'description': 'Генерация финального текста гранта'
        }
    ]

    # Emoji для статусов
    STATUS_EMOJI = {
        'completed': '✅',
        'pending': '⏳',
        'in_progress': '🔄',
        'error': '❌'
    }

    def __init__(self, lifecycle_data: Dict[str, Any]):
        """
        Инициализация визуализатора

        Args:
            lifecycle_data: Данные жизненного цикла от GrantLifecycleManager
        """
        self.data = lifecycle_data
        self.current_stage = lifecycle_data.get('current_stage')
        self.progress = lifecycle_data.get('progress', 0)
        self.artifacts = lifecycle_data.get('artifacts', {})

    def render_timeline(self):
        """Отрисовать timeline в Streamlit"""

        st.markdown("### 📊 Прогресс заявки")

        # Progress bar
        st.progress(self.progress / 100, text=f"Завершено: {self.progress:.0f}%")

        st.markdown("---")

        # Timeline как колонки
        cols = st.columns(len(self.STAGES))

        for idx, stage in enumerate(self.STAGES):
            stage_key = stage['key']
            artifact = self.artifacts.get(stage_key, {})
            status = artifact.get('status', 'pending')

            with cols[idx]:
                # Emoji статуса
                status_emoji = self.STATUS_EMOJI.get(status, '⏳')

                # Определить цвет
                if status == 'completed':
                    color = 'green'
                elif stage_key == self.current_stage:
                    color = 'orange'
                else:
                    color = 'gray'

                # Отрисовка этапа
                st.markdown(f"""
                <div style="text-align: center; padding: 10px; border-radius: 10px;
                            background-color: rgba(128, 128, 128, 0.1);">
                    <div style="font-size: 2em;">{stage['emoji']}</div>
                    <div style="font-size: 1.2em; font-weight: bold; color: {color};">
                        {stage['name']}
                    </div>
                    <div style="font-size: 1.5em;">{status_emoji}</div>
                    <div style="font-size: 0.8em; color: gray;">
                        {stage['description']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Стрелка между этапами
                if idx < len(self.STAGES) - 1:
                    st.markdown("""
                    <div style="text-align: center; font-size: 2em; margin-top: -10px;">
                        →
                    </div>
                    """, unsafe_allow_html=True)

    def render_stage_cards(self):
        """Отрисовать карточки артефактов для каждого этапа"""

        st.markdown("### 📂 Артефакты заявки")
        st.markdown("---")

        for stage in self.STAGES:
            stage_key = stage['key']
            artifact = self.artifacts.get(stage_key, {})
            status = artifact.get('status', 'pending')

            # Expander для каждого этапа
            with st.expander(f"{stage['emoji']} {stage['name']} ({self.STATUS_EMOJI.get(status, '⏳')})",
                            expanded=(status == 'completed')):

                if status == 'completed':
                    self._render_artifact_content(stage_key, artifact)
                elif status == 'in_progress':
                    st.info(f"⏳ Этап '{stage['name']}' в процессе выполнения...")
                elif status == 'error':
                    st.error(f"❌ Ошибка при выполнении этапа '{stage['name']}'")
                else:
                    st.warning(f"⏳ Этап '{stage['name']}' еще не начат")

    def _render_artifact_content(self, stage_key: str, artifact: Dict[str, Any]):
        """Отрисовать содержимое артефакта"""

        if stage_key == 'interview':
            # Анкета
            questions = artifact.get('data', [])
            st.metric("Всего вопросов", len(questions))
            st.caption(f"Завершено: {artifact.get('completed_at', 'N/A')}")

            if questions:
                with st.container():
                    for qa in questions[:5]:  # Показываем первые 5
                        st.markdown(f"**Q{qa.get('question_id', '?')}:** {qa.get('question_text', '')}")
                        st.markdown(f"**A:** {qa.get('answer', '')}")
                        st.markdown("---")

                    if len(questions) > 5:
                        st.caption(f"... и еще {len(questions) - 5} вопросов")

        elif stage_key == 'auditor':
            # Аудит
            col1, col2 = st.columns(2)
            with col1:
                score = artifact.get('score', 0)
                st.metric("Оценка качества", f"{score}/10")
            with col2:
                st.caption(f"Завершено: {artifact.get('completed_at', 'N/A')}")

            if artifact.get('analysis'):
                st.markdown("**Детальный анализ:**")
                st.text_area("", value=str(artifact.get('analysis', '')), height=150, key=f"audit_analysis_{artifact.get('completed_at')}", disabled=True)

            if artifact.get('recommendations'):
                st.markdown("**Рекомендации:**")
                st.text_area("", value=str(artifact.get('recommendations', '')), height=100, key=f"audit_rec_{artifact.get('completed_at')}", disabled=True)

        elif stage_key == 'researcher':
            # Исследование
            st.caption(f"Завершено: {artifact.get('completed_at', 'N/A')}")

            tabs = st.tabs(["Основное содержание", "Анализ рынка", "Конкуренты", "Источники"])

            with tabs[0]:
                if artifact.get('content'):
                    st.text_area("", value=str(artifact.get('content', '')), height=200, key=f"research_content_{artifact.get('completed_at')}", disabled=True)

            with tabs[1]:
                if artifact.get('market'):
                    st.text_area("", value=str(artifact.get('market', '')), height=200, key=f"research_market_{artifact.get('completed_at')}", disabled=True)

            with tabs[2]:
                if artifact.get('competitors'):
                    st.text_area("", value=str(artifact.get('competitors', '')), height=200, key=f"research_comp_{artifact.get('completed_at')}", disabled=True)

            with tabs[3]:
                if artifact.get('sources'):
                    st.text_area("", value=str(artifact.get('sources', '')), height=150, key=f"research_sources_{artifact.get('completed_at')}", disabled=True)

        elif stage_key == 'planner':
            # Планирование
            st.caption(f"Завершено: {artifact.get('completed_at', 'N/A')}")

            if artifact.get('structure'):
                st.markdown("**Структура заявки:**")
                st.text_area("", value=str(artifact.get('structure', '')), height=150, key=f"planner_struct_{artifact.get('completed_at')}", disabled=True)

            if artifact.get('sections'):
                st.markdown("**Секции:**")
                sections = artifact.get('sections', [])
                if isinstance(sections, list):
                    for i, section in enumerate(sections, 1):
                        st.markdown(f"{i}. {section}")
                else:
                    st.text(str(sections))

        elif stage_key == 'writer':
            # Финальный грант
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Оценка качества", f"{artifact.get('quality_score', 0)}/10")
            with col2:
                st.metric("LLM", artifact.get('llm_provider', 'N/A'))
            with col3:
                st.metric("Модель", artifact.get('model', 'N/A'))

            st.markdown(f"**Название:** {artifact.get('title', 'N/A')}")
            st.markdown(f"**ID:** {artifact.get('grant_id', 'N/A')}")
            st.caption(f"Завершено: {artifact.get('completed_at', 'N/A')}")

            # Секции гранта
            sections = artifact.get('sections', [])
            if sections:
                st.markdown("**Секции гранта:**")
                for section in sections:
                    if isinstance(section, dict):
                        with st.expander(f"📄 {section.get('title', 'Без названия')}"):
                            st.markdown(section.get('content', ''))

            # Полный текст
            if artifact.get('content'):
                st.markdown("---")
                st.markdown("**Полный текст гранта:**")
                st.text_area("", value=artifact.get('content', ''), height=400, key=f"grant_full_{artifact.get('completed_at')}", disabled=True)

    def get_stage_summary(self) -> str:
        """Получить краткую текстовую сводку по этапам"""
        completed = sum(1 for stage in self.STAGES if self.artifacts.get(stage['key'], {}).get('status') == 'completed')
        total = len(self.STAGES)

        return f"Завершено {completed} из {total} этапов ({self.progress:.0f}%)"


def render_grant_lifecycle(lifecycle_data: Dict[str, Any]):
    """
    Отрисовать полный жизненный цикл грантовой заявки в Streamlit

    Args:
        lifecycle_data: Данные от GrantLifecycleManager.get_all_artifacts()
    """
    visualizer = GrantStageVisualizer(lifecycle_data)

    # Timeline
    visualizer.render_timeline()

    st.markdown("---")

    # Карточки артефактов
    visualizer.render_stage_cards()
