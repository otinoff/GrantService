#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Конфигурация CrewAI для работы с UnifiedLLMClient и agent_router
Обновлено: Интеграция с agent_router для динамического выбора LLM провайдера
"""

import os
import sys
import asyncio
from pathlib import Path
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI

# Добавляем пути
sys.path.append('/var/GrantService/shared')
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from llm.unified_llm_client import UnifiedLLMClient
    from llm.config import AGENT_CONFIGS
    UNIFIED_CLIENT_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ UnifiedLLMClient недоступен: {e}")
    UNIFIED_CLIENT_AVAILABLE = False

# NEW: Import agent_router
try:
    from agent_router import get_agent_llm_client
    from data.database import GrantServiceDatabase
    AGENT_ROUTER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ agent_router недоступен: {e}")
    AGENT_ROUTER_AVAILABLE = False

def create_unified_llm(agent_type: str = "writer"):
    """
    Создание LLM через agent_router (читает настройки из БД)

    Args:
        agent_type: Тип агента (writer, auditor, planner, researcher)

    Returns:
        LLM client из agent_router или fallback на UnifiedLLMClient
    """
    # NEW: Приоритет agent_router (читает из ai_agent_settings)
    if AGENT_ROUTER_AVAILABLE:
        try:
            db = GrantServiceDatabase()
            llm_client = get_agent_llm_client(agent_type, db)
            print(f"✅ Using agent_router for {agent_type}: {type(llm_client).__name__}")

            # Возвращаем напрямую LLM клиент (уже настроен)
            return llm_client

        except Exception as e:
            print(f"⚠️ agent_router fallback: {e}")
            # Продолжаем к старой логике

    # FALLBACK: Старая логика через UnifiedLLMClient
    if not UNIFIED_CLIENT_AVAILABLE:
        raise ImportError("UnifiedLLMClient недоступен")

    config = AGENT_CONFIGS.get(agent_type, AGENT_CONFIGS["writer"])

    # Создаем UnifiedLLMClient
    client = UnifiedLLMClient(
        provider=config["provider"],
        model=config["model"],
        temperature=config["temperature"]
    )

    # Оборачиваем в LangChain совместимый интерфейс
    return ChatOpenAI(
        base_url="http://localhost:8000/v1",  # Заглушка для LangChain
        model="gpt-3.5-turbo",  # Заглушка для LangChain
        temperature=config["temperature"],
        max_tokens=config["max_tokens"]
    )

def create_agent_with_unified_llm(role: str, goal: str, backstory: str, system_message: str = "", agent_type: str = "writer"):
    """Создание агента с UnifiedLLMClient"""
    if not UNIFIED_CLIENT_AVAILABLE:
        raise ImportError("UnifiedLLMClient недоступен")
    
    llm = create_unified_llm(agent_type)
    
    return Agent(
        role=role,
        goal=goal,
        backstory=backstory,
        verbose=True,
        allow_delegation=False,
        system_message=system_message,
        llm=llm
    )

def create_task_with_unified_llm(description: str, agent, expected_output: str = "", context: list = None):
    """Создание задачи с UnifiedLLMClient"""
    return Task(
        description=description,
        agent=agent,
        expected_output=expected_output,
        context=context or []
    )

def create_crew_with_unified_llm(agents: list, tasks: list, agent_type: str = "writer"):
    """Создание команды с UnifiedLLMClient"""
    if not UNIFIED_CLIENT_AVAILABLE:
        raise ImportError("UnifiedLLMClient недоступен")
    
    llm = create_unified_llm(agent_type)
    
    return Crew(
        agents=agents,
        tasks=tasks,
        verbose=True,
        llm=llm
    )

# Функции для прямой работы с UnifiedLLMClient (без CrewAI)
async def generate_text_with_unified_llm(prompt: str, agent_type: str = "writer") -> str:
    """Прямая генерация текста через UnifiedLLMClient"""
    if not UNIFIED_CLIENT_AVAILABLE:
        raise ImportError("UnifiedLLMClient недоступен")
    
    config = AGENT_CONFIGS.get(agent_type, AGENT_CONFIGS["writer"])
    
    async with UnifiedLLMClient(
        provider=config["provider"],
        model=config["model"],
        temperature=config["temperature"]
    ) as client:
        return await client.generate_text(prompt, config["max_tokens"])

async def check_llm_connection(agent_type: str = "writer") -> bool:
    """Проверка подключения к LLM"""
    if not UNIFIED_CLIENT_AVAILABLE:
        return False
    
    config = AGENT_CONFIGS.get(agent_type, AGENT_CONFIGS["writer"])
    
    async with UnifiedLLMClient(
        provider=config["provider"],
        model=config["model"]
    ) as client:
        return await client.check_connection_async()

# Fallback функции для совместимости
def create_gigachat_llm():
    """Создание LLM для GigaChat (fallback)"""
    if UNIFIED_CLIENT_AVAILABLE:
        return create_unified_llm("writer")
    else:
        # Fallback на старую логику
        return ChatOpenAI(
            base_url="https://gigachat.devices.sberbank.ru/api/v1",
            model="GigaChat:latest",
            temperature=0.7,
            max_tokens=2000
        )

def create_agent_with_gigachat(role: str, goal: str, backstory: str, system_message: str = ""):
    """Создание агента с GigaChat (fallback)"""
    if UNIFIED_CLIENT_AVAILABLE:
        return create_agent_with_unified_llm(role, goal, backstory, system_message, "writer")
    else:
        # Fallback на старую логику
        return Agent(
            role=role,
            goal=goal,
            backstory=backstory,
            verbose=True,
            allow_delegation=False,
            system_message=system_message,
            llm=create_gigachat_llm()
        )

def create_task_with_gigachat(description: str, agent, expected_output: str = "", context: list = None):
    """Создание задачи с GigaChat (fallback)"""
    return Task(
        description=description,
        agent=agent,
        expected_output=expected_output,
        context=context or []
    )

def create_crew_with_gigachat(agents: list, tasks: list):
    """Создание команды с GigaChat (fallback)"""
    if UNIFIED_CLIENT_AVAILABLE:
        return create_crew_with_unified_llm(agents, tasks, "writer")
    else:
        # Fallback на старую логику
        return Crew(
            agents=agents,
            tasks=tasks,
            verbose=True,
            llm=create_gigachat_llm()
        ) 