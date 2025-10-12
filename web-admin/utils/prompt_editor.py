#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PromptEditor UI Component - компонент для редактирования промптов в Streamlit
Поддерживает редактирование всех промптов из БД с валидацией и сохранением
"""
import streamlit as st
from typing import Dict, List, Any, Optional
import re
import logging
from datetime import datetime

from utils.prompt_manager import DatabasePromptManager, get_database_prompt_manager
from utils.postgres_helper import execute_query, execute_update

logger = logging.getLogger(__name__)


class PromptEditor:
    """UI компонент для редактирования промптов"""

    def __init__(self, db_connection):
        """
        Args:
            db_connection: подключение к БД для сохранения изменений
        """
        self.db = db_connection
        self.prompt_manager = get_database_prompt_manager()

    def render_agent_prompts_editor(self, agent_type: str) -> None:
        """
        Отрисовать редактор промптов для конкретного агента

        Args:
            agent_type: тип агента (interviewer, auditor, researcher_v2, writer_v2, reviewer)
        """
        st.subheader(f"Промпты агента: {agent_type}")

        # Загружаем все промпты агента
        agent_prompts = self._load_agent_prompts(agent_type)

        if not agent_prompts:
            st.warning(f"Промпты для агента '{agent_type}' не найдены в БД")
            return

        # Группируем промпты по типам
        prompts_by_type = {}
        for prompt in agent_prompts:
            prompt_type = prompt.get('prompt_type', 'unknown')
            if prompt_type not in prompts_by_type:
                prompts_by_type[prompt_type] = []
            prompts_by_type[prompt_type].append(prompt)

        # Табы для разных типов промптов
        tabs = st.tabs(list(prompts_by_type.keys()))

        for tab, (prompt_type, prompts) in zip(tabs, prompts_by_type.items()):
            with tab:
                self._render_prompt_type_editor(agent_type, prompt_type, prompts)

    def _render_prompt_type_editor(self, agent_type: str, prompt_type: str, prompts: List[Dict]) -> None:
        """
        Отрисовать редактор для конкретного типа промптов

        Args:
            agent_type: тип агента
            prompt_type: тип промпта (goal, backstory, query, etc.)
            prompts: список промптов данного типа
        """
        st.markdown(f"**Тип промпта:** `{prompt_type}`")
        st.markdown(f"**Количество:** {len(prompts)}")

        # Если промптов много (например, queries), показываем их списком с возможностью редактирования по одному
        if len(prompts) > 1:
            # Селектор для выбора конкретного промпта
            prompt_options = [f"{p.get('name', 'Unnamed')} (order: {p.get('order_index', 'N/A')})" for p in prompts]
            selected_index = st.selectbox(
                "Выберите промпт для редактирования:",
                range(len(prompts)),
                format_func=lambda i: prompt_options[i],
                key=f"select_{agent_type}_{prompt_type}"
            )
            selected_prompt = prompts[selected_index]
            self._render_single_prompt_editor(selected_prompt)
        else:
            # Единичный промпт - показываем сразу
            self._render_single_prompt_editor(prompts[0])

    def _render_single_prompt_editor(self, prompt: Dict) -> None:
        """
        Отрисовать редактор для одного промпта

        Args:
            prompt: данные промпта из БД
        """
        prompt_id = prompt.get('id')
        prompt_name = prompt.get('name', 'Unnamed Prompt')
        prompt_template = prompt.get('prompt_template', '')
        variables = prompt.get('variables', {})
        is_active = prompt.get('is_active', True)
        max_tokens = prompt.get('max_tokens')
        temperature = prompt.get('temperature')

        st.markdown(f"### {prompt_name}")
        st.markdown(f"**ID:** `{prompt_id}` | **Активен:** {'✅' if is_active else '❌'}")

        # Информация о переменных
        if variables:
            with st.expander("📝 Доступные переменные"):
                st.json(variables)
                st.info("Используйте переменные в формате {VARIABLE_NAME}")

        # Редактор промпта
        col1, col2 = st.columns([3, 1])

        with col1:
            new_prompt_template = st.text_area(
                "Текст промпта:",
                value=prompt_template,
                height=300,
                key=f"prompt_text_{prompt_id}",
                help="Используйте {PLACEHOLDER} для переменных"
            )

        with col2:
            # Метаданные
            new_is_active = st.checkbox(
                "Активен",
                value=is_active,
                key=f"active_{prompt_id}"
            )

            new_max_tokens = st.number_input(
                "Max tokens",
                value=max_tokens if max_tokens else 1000,
                min_value=100,
                max_value=8000,
                step=100,
                key=f"tokens_{prompt_id}"
            )

            new_temperature = st.number_input(
                "Temperature",
                value=temperature if temperature else 0.7,
                min_value=0.0,
                max_value=1.0,
                step=0.1,
                key=f"temp_{prompt_id}"
            )

        # Валидация
        validation_errors = self._validate_prompt(new_prompt_template, variables)

        if validation_errors:
            st.error("Ошибки валидации:")
            for error in validation_errors:
                st.markdown(f"- {error}")

        # Кнопки действий
        col_save, col_reset, col_preview = st.columns(3)

        with col_save:
            if st.button("💾 Сохранить", key=f"save_{prompt_id}", disabled=bool(validation_errors)):
                success = self._save_prompt(
                    prompt_id=prompt_id,
                    prompt_template=new_prompt_template,
                    is_active=new_is_active,
                    max_tokens=new_max_tokens,
                    temperature=new_temperature
                )
                if success:
                    st.success("✅ Промпт сохранен!")
                    # Сбрасываем кеш PromptManager
                    self.prompt_manager.reload_cache()
                    st.rerun()
                else:
                    st.error("❌ Ошибка сохранения!")

        with col_reset:
            if st.button("🔄 Сбросить", key=f"reset_{prompt_id}"):
                st.rerun()

        with col_preview:
            if st.button("👁️ Предпросмотр", key=f"preview_{prompt_id}"):
                self._show_prompt_preview(new_prompt_template, variables)

    def _validate_prompt(self, prompt_template: str, variables: Dict) -> List[str]:
        """
        Валидация промпта

        Args:
            prompt_template: текст промпта
            variables: ожидаемые переменные

        Returns:
            список ошибок валидации (пустой если ок)
        """
        errors = []

        # 1. Проверка минимальной длины
        if len(prompt_template.strip()) < 10:
            errors.append("Промпт слишком короткий (минимум 10 символов)")

        # 2. Проверка использования переменных (если они объявлены)
        if variables:
            # Извлекаем все {PLACEHOLDER} из промпта
            used_placeholders = set(re.findall(r'\{([A-Z_]+)\}', prompt_template))

            # Проверяем, что все объявленные переменные используются
            declared_vars = set(variables.keys())
            unused_vars = declared_vars - used_placeholders

            if unused_vars:
                errors.append(f"Неиспользуемые переменные: {', '.join(unused_vars)}")

        # 3. Проверка на незакрытые скобки
        if prompt_template.count('{') != prompt_template.count('}'):
            errors.append("Несовпадение открывающих и закрывающих скобок {}")

        return errors

    def _save_prompt(self, prompt_id: int, prompt_template: str, is_active: bool,
                     max_tokens: int, temperature: float) -> bool:
        """
        Сохранить изменения промпта в БД

        Args:
            prompt_id: ID промпта
            prompt_template: новый текст промпта
            is_active: активен ли промпт
            max_tokens: макс токенов
            temperature: температура

        Returns:
            True если успешно
        """
        try:
            query = """
                UPDATE agent_prompts
                SET prompt_template = %s,
                    is_active = %s,
                    max_tokens = %s,
                    temperature = %s,
                    updated_at = NOW()
                WHERE id = %s
            """

            execute_update(query, (
                prompt_template,
                is_active,
                max_tokens,
                temperature,
                prompt_id
            ))

            logger.info(f"✅ Промпт {prompt_id} обновлен в БД")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка сохранения промпта {prompt_id}: {e}")
            return False

    def _show_prompt_preview(self, prompt_template: str, variables: Dict) -> None:
        """
        Показать предпросмотр промпта с подставленными переменными

        Args:
            prompt_template: текст промпта
            variables: переменные для подстановки
        """
        st.markdown("### 👁️ Предпросмотр промпта")

        # Создаем примерные значения переменных
        example_values = self._generate_example_values(variables)

        try:
            preview_text = prompt_template.format(**example_values)
            st.code(preview_text, language="text")

            st.info(f"Длина: {len(preview_text)} символов")

        except KeyError as e:
            st.error(f"Отсутствует переменная: {e}")
        except Exception as e:
            st.error(f"Ошибка предпросмотра: {e}")

    def _generate_example_values(self, variables: Dict) -> Dict[str, str]:
        """
        Сгенерировать примерные значения для переменных

        Args:
            variables: объявленные переменные

        Returns:
            словарь с примерными значениями
        """
        example_values = {}

        for var_name, var_info in variables.items():
            # Проверяем, есть ли пример в метаданных
            if isinstance(var_info, dict):
                example_values[var_name] = var_info.get('example', f'[Пример {var_name}]')
            else:
                # Генерируем пример на основе имени
                if 'ПРОБЛЕМА' in var_name:
                    example_values[var_name] = 'Недостаток спортивной инфраструктуры'
                elif 'РЕГИОН' in var_name:
                    example_values[var_name] = 'Московская область'
                elif 'БЮДЖЕТ' in var_name:
                    example_values[var_name] = '1,000,000'
                elif 'СРОК' in var_name:
                    example_values[var_name] = '12'
                else:
                    example_values[var_name] = f'[{var_name}]'

        return example_values

    def _load_agent_prompts(self, agent_type: str) -> List[Dict]:
        """
        Загрузить все промпты агента из БД

        Args:
            agent_type: тип агента

        Returns:
            список промптов
        """
        try:
            query = """
                SELECT
                    id, name, prompt_type, prompt_template,
                    variables, is_active, order_index,
                    max_tokens, temperature, category_id,
                    created_at, updated_at
                FROM agent_prompts
                WHERE agent_type = %s
                ORDER BY prompt_type, order_index NULLS LAST, id
            """

            results = execute_query(query, (agent_type,))

            if not results:
                return []

            prompts = []
            for row in results:
                prompts.append({
                    'id': row['id'],
                    'name': row['name'],
                    'prompt_type': row['prompt_type'],
                    'prompt_template': row['prompt_template'],
                    'variables': row['variables'] if row['variables'] else {},
                    'is_active': row['is_active'],
                    'order_index': row['order_index'],
                    'max_tokens': row['max_tokens'],
                    'temperature': row['temperature'],
                    'category_id': row['category_id'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                })

            logger.info(f"✅ Загружено {len(prompts)} промптов для агента {agent_type}")
            return prompts

        except Exception as e:
            logger.error(f"❌ Ошибка загрузки промптов для {agent_type}: {e}")
            return []

    def render_bulk_operations(self) -> None:
        """Отрисовать панель массовых операций"""
        st.markdown("### 🔧 Массовые операции")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🔄 Сбросить кеш промптов"):
                self.prompt_manager.reload_cache()
                st.success("✅ Кеш сброшен!")

        with col2:
            if st.button("📊 Статистика промптов"):
                stats = self.prompt_manager.get_stats()
                st.json(stats)

        with col3:
            if st.button("🧪 Тест подключения к БД"):
                try:
                    test_result = execute_query("SELECT COUNT(*) as cnt FROM agent_prompts")
                    if test_result:
                        st.success(f"✅ БД доступна. Промптов: {test_result[0]['cnt']}")
                    else:
                        st.error("❌ БД недоступна")
                except Exception as e:
                    st.error(f"❌ Ошибка: {e}")

    def render_prompt_search(self) -> Optional[str]:
        """
        Отрисовать поиск по промптам

        Returns:
            поисковый запрос или None
        """
        st.markdown("### 🔍 Поиск по промптам")

        search_query = st.text_input(
            "Введите ключевое слово:",
            placeholder="Например: SMART, цитата, таблица...",
            key="prompt_search"
        )

        if search_query and len(search_query) >= 3:
            results = self._search_prompts(search_query)

            if results:
                st.success(f"Найдено: {len(results)} промптов")

                for result in results[:10]:  # Показываем первые 10
                    with st.expander(f"{result['agent_type']} - {result['name']}"):
                        st.markdown(f"**Тип:** {result['prompt_type']}")
                        st.code(result['prompt_template'][:200] + "...", language="text")

                        if st.button(f"Редактировать", key=f"edit_search_{result['id']}"):
                            return result['agent_type']
            else:
                st.info("Ничего не найдено")

        return None

    def _search_prompts(self, query: str) -> List[Dict]:
        """
        Поиск промптов по ключевому слову

        Args:
            query: поисковый запрос

        Returns:
            список найденных промптов
        """
        try:
            sql_query = """
                SELECT
                    id, agent_type, name, prompt_type, prompt_template
                FROM agent_prompts
                WHERE
                    prompt_template ILIKE %s
                    OR name ILIKE %s
                    OR prompt_type ILIKE %s
                ORDER BY agent_type, prompt_type
                LIMIT 50
            """

            search_pattern = f"%{query}%"
            results = execute_query(sql_query, (search_pattern, search_pattern, search_pattern))

            return results if results else []

        except Exception as e:
            logger.error(f"❌ Ошибка поиска: {e}")
            return []
