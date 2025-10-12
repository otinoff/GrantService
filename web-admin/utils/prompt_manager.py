#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prompt Manager - система управления промптами для AI-агентов
=============================================================

Функции для работы с таблицей ai_agent_prompts:
- Получение промптов
- Сохранение промптов
- Версионирование
- Статистика использования
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from utils.postgres_helper import execute_query, execute_update
from utils.logger import setup_logger

logger = setup_logger('prompt_manager')


# =============================================================================
# Получение промптов
# =============================================================================

def get_agent_prompts(agent_name: str, prompt_type: Optional[str] = None) -> List[Dict]:
    """
    Получить все промпты для агента

    Args:
        agent_name: Имя агента ('auditor', 'planner', 'writer', etc.)
        prompt_type: Тип промпта (опционально, для фильтрации)

    Returns:
        List[Dict]: Список промптов
    """
    query = """
        SELECT
            id, agent_name, prompt_type, prompt_key,
            prompt_text, prompt_description,
            variables, example_output,
            llm_provider, model, temperature, max_tokens,
            version, is_active, is_default,
            usage_count, last_used_at, avg_score,
            created_at, updated_at
        FROM ai_agent_prompts
        WHERE agent_name = %s
    """

    params = [agent_name]

    if prompt_type:
        query += " AND prompt_type = %s"
        params.append(prompt_type)

    query += " ORDER BY is_default DESC, prompt_type, version DESC"

    try:
        result = execute_query(query, tuple(params))
        return result if result else []
    except Exception as e:
        logger.error(f"Error fetching prompts for {agent_name}: {e}")
        return []


def get_prompt_by_key(prompt_key: str) -> Optional[Dict]:
    """
    Получить промпт по ключу

    Args:
        prompt_key: Уникальный ключ промпта

    Returns:
        Dict или None
    """
    query = """
        SELECT *
        FROM ai_agent_prompts
        WHERE prompt_key = %s AND is_active = TRUE
    """

    try:
        result = execute_query(query, (prompt_key,))
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Error fetching prompt {prompt_key}: {e}")
        return None


def get_default_prompt(agent_name: str, prompt_type: str) -> Optional[Dict]:
    """
    Получить промпт по умолчанию

    Args:
        agent_name: Имя агента
        prompt_type: Тип промпта

    Returns:
        Dict или None
    """
    query = """
        SELECT *
        FROM ai_agent_prompts
        WHERE agent_name = %s
          AND prompt_type = %s
          AND is_default = TRUE
          AND is_active = TRUE
        LIMIT 1
    """

    try:
        result = execute_query(query, (agent_name, prompt_type))
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Error fetching default prompt for {agent_name}/{prompt_type}: {e}")
        return None


# =============================================================================
# Сохранение и обновление промптов
# =============================================================================

def save_prompt(
    agent_name: str,
    prompt_type: str,
    prompt_text: str,
    prompt_key: Optional[str] = None,
    description: Optional[str] = None,
    variables: Optional[Dict] = None,
    llm_provider: str = 'gigachat',
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4000,
    is_default: bool = False,
    updated_by: str = 'admin'
) -> Optional[int]:
    """
    Сохранить новый промпт или обновить существующий

    Returns:
        int: ID промпта или None при ошибке
    """
    # Генерируем ключ если не передан
    if not prompt_key:
        prompt_key = f"{agent_name}_{prompt_type}"

    # Проверяем существует ли промпт
    existing = get_prompt_by_key(prompt_key)

    if existing:
        # Обновляем существующий (увеличиваем версию)
        query = """
            UPDATE ai_agent_prompts
            SET prompt_text = %s,
                prompt_description = %s,
                variables = %s,
                llm_provider = %s,
                model = %s,
                temperature = %s,
                max_tokens = %s,
                is_default = %s,
                version = version + 1,
                updated_at = NOW(),
                updated_by = %s
            WHERE prompt_key = %s
            RETURNING id
        """

        params = (
            prompt_text, description,
            json.dumps(variables) if variables else None,
            llm_provider, model, temperature, max_tokens,
            is_default, updated_by, prompt_key
        )
    else:
        # Создаем новый
        query = """
            INSERT INTO ai_agent_prompts (
                agent_name, prompt_type, prompt_key,
                prompt_text, prompt_description, variables,
                llm_provider, model, temperature, max_tokens,
                is_default, created_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """

        params = (
            agent_name, prompt_type, prompt_key,
            prompt_text, description,
            json.dumps(variables) if variables else None,
            llm_provider, model, temperature, max_tokens,
            is_default, updated_by
        )

    try:
        result = execute_query(query, params)
        prompt_id = result[0]['id'] if result else None

        logger.info(f"Prompt {prompt_key} saved successfully (ID: {prompt_id})")
        return prompt_id
    except Exception as e:
        logger.error(f"Error saving prompt {prompt_key}: {e}")
        return None


def set_default_prompt(prompt_key: str) -> bool:
    """
    Установить промпт как промпт по умолчанию (снимает флаг с других)

    Args:
        prompt_key: Ключ промпта

    Returns:
        bool: Успешность операции
    """
    # Получаем промпт
    prompt = get_prompt_by_key(prompt_key)
    if not prompt:
        logger.error(f"Prompt {prompt_key} not found")
        return False

    agent_name = prompt['agent_name']
    prompt_type = prompt['prompt_type']

    try:
        # Снимаем флаг default с других промптов этого типа
        execute_update("""
            UPDATE ai_agent_prompts
            SET is_default = FALSE
            WHERE agent_name = %s AND prompt_type = %s
        """, (agent_name, prompt_type))

        # Устанавливаем флаг для выбранного
        execute_update("""
            UPDATE ai_agent_prompts
            SET is_default = TRUE, updated_at = NOW()
            WHERE prompt_key = %s
        """, (prompt_key,))

        logger.info(f"Set {prompt_key} as default for {agent_name}/{prompt_type}")
        return True
    except Exception as e:
        logger.error(f"Error setting default prompt: {e}")
        return False


# =============================================================================
# Статистика и версионирование
# =============================================================================

def increment_usage(prompt_key: str, score: Optional[float] = None) -> None:
    """
    Увеличить счетчик использования промпта

    Args:
        prompt_key: Ключ промпта
        score: Оценка результата (опционально)
    """
    update_score = ""
    params = [prompt_key]

    if score is not None:
        # Обновляем среднюю оценку
        update_score = ", avg_score = COALESCE((avg_score * usage_count + %s) / (usage_count + 1), %s)"
        params = [score, score, prompt_key]

    query = f"""
        UPDATE ai_agent_prompts
        SET usage_count = usage_count + 1,
            last_used_at = NOW()
            {update_score}
        WHERE prompt_key = %s
    """

    try:
        execute_update(query, tuple(params))
    except Exception as e:
        logger.error(f"Error incrementing usage for {prompt_key}: {e}")


def get_prompt_history(prompt_key: str, limit: int = 10) -> List[Dict]:
    """
    Получить историю версий промпта

    Args:
        prompt_key: Ключ промпта
        limit: Количество версий

    Returns:
        List[Dict]: История версий
    """
    # Note: В текущей реализации history не сохраняется
    # Для полноценного версионирования нужна отдельная таблица ai_agent_prompts_history
    query = """
        SELECT version, updated_at, updated_by
        FROM ai_agent_prompts
        WHERE prompt_key = %s
        ORDER BY version DESC
        LIMIT %s
    """

    try:
        result = execute_query(query, (prompt_key, limit))
        return result if result else []
    except Exception as e:
        logger.error(f"Error fetching prompt history: {e}")
        return []


# =============================================================================
# Вспомогательные функции
# =============================================================================

def format_prompt(prompt_text: str, variables: Dict[str, Any]) -> str:
    """
    Подставить переменные в промпт

    Args:
        prompt_text: Текст промпта с плейсхолдерами {var_name}
        variables: Словарь со значениями переменных

    Returns:
        str: Промпт с подставленными значениями
    """
    try:
        return prompt_text.format(**variables)
    except KeyError as e:
        logger.error(f"Missing variable in prompt: {e}")
        return prompt_text
    except Exception as e:
        logger.error(f"Error formatting prompt: {e}")
        return prompt_text


def validate_prompt_variables(prompt_text: str, expected_vars: List[str]) -> List[str]:
    """
    Проверить что все переменные присутствуют в промпте

    Args:
        prompt_text: Текст промпта
        expected_vars: Ожидаемые переменные

    Returns:
        List[str]: Список отсутствующих переменных
    """
    import re

    # Находим все плейсхолдеры {var_name}
    found_vars = set(re.findall(r'\{(\w+)\}', prompt_text))

    # Проверяем отсутствующие
    missing = [var for var in expected_vars if var not in found_vars]

    return missing


# =============================================================================
# DatabasePromptManager - новый менеджер для agent_prompts (Migration 010)
# =============================================================================

class DatabasePromptManager:
    """
    Менеджер промптов для работы с новой таблицей agent_prompts

    Особенности:
    - Работает с agent_prompts (после миграции 010)
    - Кеширование в памяти (TTL 5 минут)
    - Поддержка всех 5 агентов
    - Форматирование с переменными
    """

    def __init__(self, cache_ttl_seconds: int = 300):
        """
        Инициализация менеджера

        Args:
            cache_ttl_seconds: Время жизни кеша в секундах (по умолчанию 5 минут)
        """
        self._cache: Dict[str, Any] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl_seconds = cache_ttl_seconds

        logger.info("DatabasePromptManager initialized")

    def _is_cache_valid(self) -> bool:
        """Проверить актуальность кеша"""
        if not self._cache_timestamp:
            return False

        age = (datetime.now() - self._cache_timestamp).total_seconds()
        return age < self._cache_ttl_seconds

    def _load_prompts_from_db(self) -> List[Dict[str, Any]]:
        """
        Загрузить все активные промпты из БД

        Returns:
            List[Dict]: Список промптов
        """
        query = """
            SELECT
                ap.id,
                ap.name,
                ap.description,
                ap.prompt_template,
                ap.agent_type,
                ap.prompt_type,
                ap.category_id,
                ap.variables,
                ap.max_tokens,
                ap.temperature,
                ap.order_index,
                ap.is_active,
                ap.priority,
                pc.name as category_name
            FROM agent_prompts ap
            LEFT JOIN prompt_categories pc ON ap.category_id = pc.id
            WHERE ap.is_active = true
            ORDER BY ap.agent_type, ap.prompt_type, ap.order_index
        """

        try:
            prompts = execute_query(query)
            logger.info(f"Loaded {len(prompts)} prompts from agent_prompts table")
            return prompts if prompts else []
        except Exception as e:
            logger.error(f"Error loading prompts from DB: {e}")
            return []

    def reload_cache(self) -> None:
        """Принудительная перезагрузка кеша из БД"""
        logger.info("Reloading prompts cache...")

        prompts = self._load_prompts_from_db()

        # Очищаем старый кеш
        self._cache = {}

        # Строим индекс: agent_type -> prompt_type -> List[prompt]
        for prompt in prompts:
            agent_type = prompt.get('agent_type', 'unknown')
            prompt_type = prompt.get('prompt_type', 'unknown')

            if agent_type not in self._cache:
                self._cache[agent_type] = {}

            if prompt_type not in self._cache[agent_type]:
                self._cache[agent_type][prompt_type] = []

            self._cache[agent_type][prompt_type].append(prompt)

        self._cache_timestamp = datetime.now()

        logger.info(f"Cache reloaded: {len(self._cache)} agent types, {len(prompts)} total prompts")

    def get_prompt(
        self,
        agent_type: str,
        prompt_type: str,
        variables: Optional[Dict[str, Any]] = None,
        order_index: Optional[int] = None
    ) -> Optional[str]:
        """
        Получить промпт по типу агента и типу промпта

        Args:
            agent_type: Тип агента (interviewer, auditor, researcher_v2, writer_v2, reviewer)
            prompt_type: Тип промпта (goal, backstory, fallback_question, block1_query, etc.)
            variables: Словарь переменных для форматирования
            order_index: Индекс промпта (для списков вопросов)

        Returns:
            str: Отформатированный промпт или None

        Example:
            >>> pm = DatabasePromptManager()
            >>> goal = pm.get_prompt('interviewer', 'goal')
            >>> question_5 = pm.get_prompt('interviewer', 'fallback_question', order_index=5)
        """
        # Проверяем кеш
        if not self._is_cache_valid():
            self.reload_cache()

        # Получаем промпты
        prompts = self._cache.get(agent_type, {}).get(prompt_type, [])

        if not prompts:
            logger.warning(f"No prompts found for {agent_type}/{prompt_type}")
            return None

        # Выбираем нужный промпт
        if order_index is not None:
            matching = [p for p in prompts if p.get('order_index') == order_index]
            if not matching:
                logger.warning(f"No prompt with order_index={order_index} for {agent_type}/{prompt_type}")
                return None
            prompt = matching[0]
        else:
            prompt = prompts[0]

        # Получаем шаблон
        template = prompt.get('prompt_template', '')

        # Форматируем с переменными
        if variables:
            try:
                return template.format(**variables)
            except KeyError as e:
                logger.error(f"Missing variable {e} in prompt {agent_type}/{prompt_type}")
                return template

        return template

    def get_all_prompts(
        self,
        agent_type: str,
        prompt_type: str
    ) -> List[Dict[str, Any]]:
        """
        Получить все промпты для агента и типа

        Args:
            agent_type: Тип агента
            prompt_type: Тип промпта

        Returns:
            List[Dict]: Список промптов с метаданными
        """
        if not self._is_cache_valid():
            self.reload_cache()

        prompts = self._cache.get(agent_type, {}).get(prompt_type, [])
        return sorted(prompts, key=lambda p: p.get('order_index', 0))

    def get_researcher_queries(self, block: int) -> List[str]:
        """
        Получить запросы Researcher V2 для блока

        Args:
            block: Номер блока (1, 2, 3)

        Returns:
            List[str]: Список шаблонов запросов
        """
        prompt_type = f'block{block}_query'
        prompts = self.get_all_prompts('researcher_v2', prompt_type)
        return [p['prompt_template'] for p in prompts]

    def get_writer_stage_prompt(
        self,
        stage: int,
        variables: Dict[str, Any]
    ) -> Optional[str]:
        """
        Получить промпт Writer V2 для стадии

        Args:
            stage: Номер стадии (1 = planning, 2 = writing)
            variables: Переменные для подстановки

        Returns:
            str: Отформатированный промпт
        """
        prompt_type = f'stage{stage}_planning' if stage == 1 else f'stage{stage}_writing'
        return self.get_prompt('writer_v2', prompt_type, variables)

    def get_agent_config(self, agent_type: str) -> Dict[str, str]:
        """
        Получить goal и backstory агента

        Args:
            agent_type: Тип агента

        Returns:
            Dict: {'goal': '...', 'backstory': '...'}
        """
        goal = self.get_prompt(agent_type, 'goal')
        backstory = self.get_prompt(agent_type, 'backstory')

        return {
            'goal': goal or '',
            'backstory': backstory or ''
        }

    def get_stats(self) -> Dict[str, Any]:
        """
        Получить статистику по промптам

        Returns:
            Dict: Статистика кеша
        """
        if not self._is_cache_valid():
            self.reload_cache()

        total_prompts = sum(
            len(prompts)
            for agent_prompts in self._cache.values()
            for prompts in agent_prompts.values()
        )

        agent_counts = {
            agent_type: sum(len(p) for p in prompts.values())
            for agent_type, prompts in self._cache.items()
        }

        return {
            'total_prompts': total_prompts,
            'agent_types': len(self._cache),
            'agent_counts': agent_counts,
            'cache_age_seconds': (datetime.now() - self._cache_timestamp).total_seconds() if self._cache_timestamp else 0,
            'cache_valid': self._is_cache_valid()
        }


# Глобальный экземпляр для использования в приложении
_global_db_manager: Optional[DatabasePromptManager] = None


def get_database_prompt_manager(force_new: bool = False) -> DatabasePromptManager:
    """
    Получить глобальный экземпляр DatabasePromptManager (singleton)

    Args:
        force_new: Создать новый экземпляр

    Returns:
        DatabasePromptManager: Глобальный менеджер промптов
    """
    global _global_db_manager

    if force_new or _global_db_manager is None:
        _global_db_manager = DatabasePromptManager()

    return _global_db_manager
