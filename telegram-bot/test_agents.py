#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование агентов с Perplexity и GigaChat
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from data.database import GrantServiceDatabase as Database
from agents.researcher_agent import ResearcherAgent
from agents.writer_agent import WriterAgent
from agents.auditor_agent import AuditorAgent

def test_agents():
    """Тестирование создания агентов"""
    print("🧪 Тестирование агентов GrantService")
    print("=" * 50)
    
    try:
        # Инициализируем базу данных
        db = Database()
        print("✅ База данных подключена")
        
        # Тестируем Researcher (Perplexity)
        print("\n🔍 Тестируем Researcher Agent (Perplexity)...")
        researcher = ResearcherAgent(db)
        if researcher.crewai_agent:
            print("✅ Researcher Agent создан с Perplexity")
        else:
            print("❌ Ошибка создания Researcher Agent")
        
        # Тестируем Writer (GigaChat)
        print("\n✍️ Тестируем Writer Agent (GigaChat)...")
        writer = WriterAgent(db)
        if writer.crewai_agent:
            print("✅ Writer Agent создан с GigaChat")
        else:
            print("❌ Ошибка создания Writer Agent")
        
        # Тестируем Auditor (GigaChat)
        print("\n🔍 Тестируем Auditor Agent (GigaChat)...")
        auditor = AuditorAgent(db)
        if auditor.crewai_agent:
            print("✅ Auditor Agent создан с GigaChat")
        else:
            print("❌ Ошибка создания Auditor Agent")
        
        print("\n" + "=" * 50)
        print("🎉 Тестирование завершено!")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_agents() 