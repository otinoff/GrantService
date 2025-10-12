#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование агентов с Perplexity и GigaChat
Обновлено: Интеграция с agent_router для динамического выбора LLM провайдера
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from data.database import GrantServiceDatabase as Database
sys.path.append('/var/GrantService/agents')
sys.path.append('/var/GrantService')
from agents.researcher_agent import ResearcherAgent
from agents.writer_agent import WriterAgent
from agents.auditor_agent import AuditorAgent

# NEW: Import agent_router for dynamic LLM provider selection
from agent_router import get_agent_llm_client

def test_agents():
    """Тестирование создания агентов с agent_router интеграцией"""
    print("🧪 Тестирование агентов GrantService (с agent_router)")
    print("=" * 50)

    try:
        # Инициализируем базу данных
        db = Database()
        print("✅ База данных подключена")

        # NEW: Используем agent_router для получения LLM клиентов
        print("\n🔀 Получаем LLM провайдеров через agent_router...")

        # Тестируем Researcher
        print("\n🔍 Тестируем Researcher Agent...")
        try:
            researcher_llm = get_agent_llm_client('researcher', db)
            print(f"   ✅ LLM провайдер: {type(researcher_llm).__name__}")
            researcher = ResearcherAgent(db)
            if researcher.crewai_agent:
                print("   ✅ Researcher Agent создан успешно")
            else:
                print("   ⚠️ Researcher Agent создан без crewai_agent")
        except Exception as e:
            print(f"   ❌ Ошибка создания Researcher: {e}")

        # Тестируем Writer
        print("\n✍️ Тестируем Writer Agent...")
        try:
            writer_llm = get_agent_llm_client('writer', db)
            print(f"   ✅ LLM провайдер: {type(writer_llm).__name__}")
            writer = WriterAgent(db)
            if writer.crewai_agent:
                print("   ✅ Writer Agent создан успешно")
            else:
                print("   ⚠️ Writer Agent создан без crewai_agent")
        except Exception as e:
            print(f"   ❌ Ошибка создания Writer: {e}")

        # Тестируем Auditor
        print("\n🔍 Тестируем Auditor Agent...")
        try:
            auditor_llm = get_agent_llm_client('auditor', db)
            print(f"   ✅ LLM провайдер: {type(auditor_llm).__name__}")
            auditor = AuditorAgent(db)
            if auditor.crewai_agent:
                print("   ✅ Auditor Agent создан успешно")
            else:
                print("   ⚠️ Auditor Agent создан без crewai_agent")
        except Exception as e:
            print(f"   ❌ Ошибка создания Auditor: {e}")

        # Дополнительная информация
        print("\n" + "=" * 50)
        print("📋 Информация о провайдерах:")
        print(f"   🔍 Researcher: {type(researcher_llm).__name__ if 'researcher_llm' in locals() else 'N/A'}")
        print(f"   ✍️ Writer: {type(writer_llm).__name__ if 'writer_llm' in locals() else 'N/A'}")
        print(f"   🔍 Auditor: {type(auditor_llm).__name__ if 'auditor_llm' in locals() else 'N/A'}")

        print("\n" + "=" * 50)
        print("🎉 Тестирование завершено!")
        print("💡 Провайдеры читаются из таблицы ai_agent_settings")

    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_agents() 