#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Конфигурация CrewAI для работы с Perplexity API (Researcher) и GigaChat API (Writer, Auditor)
"""

import os
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI

# Настройки Perplexity (для Researcher)
PERPLEXITY_API_KEY = "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"
PERPLEXITY_BASE_URL = "https://api.perplexity.ai"

# Настройки GigaChat (для Writer и Auditor)
GIGACHAT_API_KEY = os.getenv('GIGACHAT_API_KEY')
GIGACHAT_BASE_URL = "http://localhost:8000/v1"  # gpt2giga прокси

def create_perplexity_llm():
    """Создание LLM для Perplexity (Researcher) - sonar для быстрых исследований"""
    return ChatOpenAI(
        api_key=PERPLEXITY_API_KEY,
        base_url=PERPLEXITY_BASE_URL,
        model="sonar",  # Используем простую модель
        temperature=0.2,  # Низкая температура для точности
        max_tokens=2000,  # Ограничиваем токены
        streaming=False
    )

def create_gigachat_llm():
    """Создание LLM для GigaChat (Writer, Auditor)"""
    return ChatOpenAI(
        api_key="dummy-key",  # Любой ключ, так как gpt2giga его игнорирует
        base_url=GIGACHAT_BASE_URL,
        model="gpt-3.5-turbo",  # Любое название, gpt2giga перенаправит на GigaChat
        temperature=0.7,
        max_tokens=2000,
        streaming=False
    )

def create_agent_with_perplexity(role: str, goal: str, backstory: str, system_message: str = ""):
    """Создание агента с Perplexity (для Researcher)"""
    return Agent(
        role=role,
        goal=goal,
        backstory=backstory,
        verbose=True,
        allow_delegation=False,
        system_message=system_message,
        llm=create_perplexity_llm()
    )

def create_agent_with_gigachat(role: str, goal: str, backstory: str, system_message: str = ""):
    """Создание агента с GigaChat (для Writer и Auditor)"""
    return Agent(
        role=role,
        goal=goal,
        backstory=backstory,
        verbose=True,
        allow_delegation=False,
        system_message=system_message,
        llm=create_gigachat_llm()
    )

def create_task_with_perplexity(description: str, agent, expected_output: str = "", context: list = None):
    """Создание задачи с Perplexity"""
    return Task(
        description=description,
        agent=agent,
        expected_output=expected_output,
        context=context or []
    )

def create_task_with_gigachat(description: str, agent, expected_output: str = "", context: list = None):
    """Создание задачи с GigaChat"""
    return Task(
        description=description,
        agent=agent,
        expected_output=expected_output,
        context=context or []
    )

def create_crew_with_gigachat(agents: list, tasks: list):
    """Создание команды с GigaChat (основной LLM для команды)"""
    return Crew(
        agents=agents,
        tasks=tasks,
        verbose=True,
        llm=create_gigachat_llm()
    ) 