#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест Auditor Agent - оценка сгенерированной заявки
Iteration 27 - проверяем заявку GA-20251023-42EC3885
"""
import sys
import os
from pathlib import Path
import asyncio
import json
import time
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Пути к проекту
project_root = Path(r"C:\SnowWhiteAI\GrantService")
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "agents"))
sys.path.insert(0, str(project_root / "shared"))
sys.path.insert(0, str(project_root / "web-admin"))

# Загрузка .env.local
env_file = Path(__file__).parent.parent / ".env.local"
if env_file.exists():
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# Настройки
ANKETA_ID = "#AN-20251012-Natalia_bruzzzz-001"
APPLICATION_FILE = Path(r"C:\SnowWhiteAI\GrantService\reports\GA-20251023-42EC3885.md")
ANKETA_FILE = Path(__file__).parent.parent / "test_data" / "natalia_anketa_20251012.json"

def log(message: str, emoji: str = "📌"):
    """Логирование"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{emoji} [{timestamp}] {message}", flush=True)

def load_application():
    """Загрузить сгенерированную заявку"""
    log(f"Загрузка заявки: {APPLICATION_FILE}", "📄")
    with open(APPLICATION_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    log(f"✅ Заявка загружена: {len(content)} символов", "")
    return content

def load_anketa():
    """Загрузить анкету"""
    log(f"Загрузка анкеты: {ANKETA_FILE}", "📋")
    with open(ANKETA_FILE, 'r', encoding='utf-8') as f:
        anketa = json.load(f)
    log(f"✅ Анкета загружена", "")
    return anketa

async def main():
    """Главная функция"""
    log("="*80, "")
    log("ТЕСТ AUDITOR AGENT - Оценка заявки", "🔍")
    log("="*80, "")

    start_time = time.time()

    # Загрузка данных
    application_text = load_application()
    anketa = load_anketa()

    # Настройка локальной БД
    log("Настройка подключения к ЛОКАЛЬНОЙ БД...", "🔌")
    os.environ['PGHOST'] = 'localhost'
    os.environ['PGPORT'] = '5432'
    os.environ['PGDATABASE'] = 'grantservice'
    os.environ['PGUSER'] = 'postgres'
    os.environ['PGPASSWORD'] = 'root'
    log("  ✅ БД: localhost:5432/grantservice", "")

    # Создание DB instance
    from data.database import get_db
    db = get_db()
    log(f"✅ Database instance created", "")
    log("", "")

    # AUDITOR
    try:
        log("ЗАПУСКАЕМ AUDITOR с GigaChat", "🔍")
        log("-" * 80, "")

        from auditor_agent import AuditorAgent

        log("Инициализация Auditor...", "")
        auditor = AuditorAgent(
            db=db,
            llm_provider='gigachat'  # Используем GigaChat для оценки
        )
        log("✅ Auditor инициализирован", "")

        input_data = {
            "anketa_id": ANKETA_ID,
            "application": application_text,  # Текст заявки
            "user_answers": anketa.get("interview_data", {}),
            "research_data": {},  # Нет research данных в этом тесте
            "selected_grant": {}
        }

        log("", "")
        log("🚀 Запускаем аудит через GigaChat...", "")
        log("   (анализ структуры, содержания, соответствия требованиям)", "")
        log("", "")

        result = await auditor.audit_application_async(input_data)

        duration = time.time() - start_time

        if result:
            log(f"✅ Auditor завершён за {duration:.1f} секунд", "")
            log("", "")
            log("="*80, "")
            log("📊 РЕЗУЛЬТАТЫ АУДИТА", "")
            log("="*80, "")
            log(f"   Status: {result.get('status')}", "")
            log(f"   Overall Score: {result.get('overall_score', 0)*100:.1f}%", "")
            log(f"   Completeness Score: {result.get('completeness_score', 0)}/10", "")
            log(f"   Quality Score: {result.get('quality_score', 0)}/10", "")
            log(f"   Compliance Score: {result.get('compliance_score', 0)}/10", "")
            log(f"   Readiness Status: {result.get('readiness_status')}", "")
            log(f"   Can Submit: {'✅ ДА' if result.get('can_submit') else '❌ НЕТ'}", "")
            log("", "")

            # Рекомендации
            recommendations = result.get('recommendations', [])
            if recommendations:
                log("📝 РЕКОМЕНДАЦИИ ПО УЛУЧШЕНИЮ:", "")
                log("-" * 80, "")
                for i, rec in enumerate(recommendations[:5], 1):  # Первые 5
                    log(f"   {i}. {rec}", "")
                if len(recommendations) > 5:
                    log(f"   ... и ещё {len(recommendations)-5} рекомендаций", "")
                log("", "")

            # Детальный анализ
            analysis = result.get('analysis', {})
            if analysis:
                log("📋 ДЕТАЛЬНЫЙ АНАЛИЗ:", "")
                log("-" * 80, "")

                structure = analysis.get('structure', {})
                if structure:
                    log(f"   📐 Структура (score: {structure.get('score', 0)*10:.1f}/10):", "")
                    for issue in structure.get('issues', [])[:3]:
                        log(f"      • {issue}", "")

                content = analysis.get('content', {})
                if content:
                    log(f"   📝 Содержание (score: {content.get('score', 0)*10:.1f}/10):", "")
                    for issue in content.get('issues', [])[:3]:
                        log(f"      • {issue}", "")

                compliance = analysis.get('compliance', {})
                if compliance:
                    log(f"   ✅ Соответствие требованиям (score: {compliance.get('score', 0)*10:.1f}/10):", "")
                    for issue in compliance.get('issues', [])[:3]:
                        log(f"      • {issue}", "")

                log("", "")

            # Сохраняем полный результат
            output_file = Path(__file__).parent.parent / "test_results" / f"audit_report_{ANKETA_ID.replace('#', '').replace('-', '_')}.json"
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            log(f"💾 Полный отчёт сохранён: {output_file}", "")

        else:
            log(f"❌ Auditor вернул None", "")

        log("", "")
        log("="*80, "")
        log("ПРОВЕРЬТЕ АДМИНКУ GIGACHAT!", "🎯")
        log("Должен быть дополнительный расход токенов", "")
        log("="*80, "")

    except Exception as e:
        log(f"❌ ОШИБКА Auditor: {e}", "")
        import traceback
        print("\n" + "="*80)
        print("TRACEBACK:")
        print("="*80)
        traceback.print_exc()
        print("="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
