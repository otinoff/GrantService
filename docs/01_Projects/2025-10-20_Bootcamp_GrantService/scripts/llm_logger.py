#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM Logger - Логирование всех запросов и ответов к/от LLM
Записывает первые 500 символов каждого блока для анализа
"""
import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

class LLMLogger:
    """Логгер для записи всех LLM взаимодействий"""

    def __init__(self, log_dir: str = None):
        if log_dir is None:
            log_dir = Path(__file__).parent.parent / "test_results" / "llm_logs"

        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Создаем файл для текущей сессии
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"llm_dialog_{timestamp}.jsonl"

        print(f"📝 LLM Logger initialized: {self.log_file}")

    def log_request(self, agent: str, stage: str, prompt: str, model: str = None, **kwargs):
        """
        Логировать LLM запрос

        Args:
            agent: Имя агента (researcher, writer, auditor)
            stage: Этап (planning, writing, quality_check)
            prompt: Промпт (первые 500 символов)
            model: Модель LLM
            **kwargs: Дополнительные параметры
        """
        entry = {
            "type": "request",
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "stage": stage,
            "model": model,
            "prompt_preview": prompt[:500] if prompt else "",
            "prompt_length": len(prompt) if prompt else 0,
            "kwargs": kwargs
        }

        self._write_entry(entry)

        # Консольный вывод
        print(f"\n{'='*80}")
        print(f"🔵 LLM REQUEST | {agent.upper()} | {stage}")
        print(f"{'='*80}")
        print(f"Model: {model}")
        print(f"Prompt length: {len(prompt) if prompt else 0} chars")
        print(f"\nPrompt preview (first 500 chars):")
        print(f"{'-'*80}")
        print(prompt[:500] if prompt else "(empty)")
        print(f"{'-'*80}\n")

    def log_response(self, agent: str, stage: str, response: str, success: bool = True, **kwargs):
        """
        Логировать LLM ответ

        Args:
            agent: Имя агента
            stage: Этап
            response: Ответ (первые 500 символов)
            success: Успех/ошибка
            **kwargs: Дополнительные параметры (tokens_used, etc.)
        """
        entry = {
            "type": "response",
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "stage": stage,
            "success": success,
            "response_preview": response[:500] if response else "",
            "response_length": len(response) if response else 0,
            "kwargs": kwargs
        }

        self._write_entry(entry)

        # Консольный вывод
        emoji = "✅" if success else "❌"
        print(f"\n{'='*80}")
        print(f"{emoji} LLM RESPONSE | {agent.upper()} | {stage}")
        print(f"{'='*80}")
        print(f"Success: {success}")
        print(f"Response length: {len(response) if response else 0} chars")
        if kwargs.get('tokens_used'):
            print(f"Tokens used: {kwargs['tokens_used']}")
        print(f"\nResponse preview (first 500 chars):")
        print(f"{'-'*80}")
        print(response[:500] if response else "(empty)")
        print(f"{'-'*80}\n")

    def log_error(self, agent: str, stage: str, error: str, **kwargs):
        """
        Логировать ошибку LLM

        Args:
            agent: Имя агента
            stage: Этап
            error: Текст ошибки
            **kwargs: Дополнительные параметры
        """
        entry = {
            "type": "error",
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "stage": stage,
            "error": str(error),
            "kwargs": kwargs
        }

        self._write_entry(entry)

        # Консольный вывод
        print(f"\n{'='*80}")
        print(f"❌ LLM ERROR | {agent.upper()} | {stage}")
        print(f"{'='*80}")
        print(f"Error: {error}")
        print(f"{'='*80}\n")

    def _write_entry(self, entry: dict):
        """Записать запись в файл"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    def get_summary(self):
        """Получить сводку по всем запросам в текущей сессии"""
        if not self.log_file.exists():
            return {}

        summary = {
            "requests": 0,
            "responses": 0,
            "errors": 0,
            "total_prompt_length": 0,
            "total_response_length": 0,
            "by_agent": {}
        }

        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                entry = json.loads(line)
                entry_type = entry['type']
                agent = entry['agent']

                if entry_type == 'request':
                    summary['requests'] += 1
                    summary['total_prompt_length'] += entry.get('prompt_length', 0)
                elif entry_type == 'response':
                    summary['responses'] += 1
                    summary['total_response_length'] += entry.get('response_length', 0)
                elif entry_type == 'error':
                    summary['errors'] += 1

                # Per-agent stats
                if agent not in summary['by_agent']:
                    summary['by_agent'][agent] = {
                        'requests': 0,
                        'responses': 0,
                        'errors': 0
                    }

                if entry_type == 'request':
                    summary['by_agent'][agent]['requests'] += 1
                elif entry_type == 'response':
                    summary['by_agent'][agent]['responses'] += 1
                elif entry_type == 'error':
                    summary['by_agent'][agent]['errors'] += 1

        return summary


# Global logger instance
_logger_instance = None

def get_llm_logger() -> LLMLogger:
    """Получить глобальный instance логгера"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = LLMLogger()
    return _logger_instance


if __name__ == "__main__":
    # Тест
    logger = LLMLogger()

    logger.log_request(
        agent="writer",
        stage="planning",
        prompt="Напиши план грантовой заявки на основе следующих данных: проект про стрельбу из лука...",
        model="GigaChat-2-Max"
    )

    logger.log_response(
        agent="writer",
        stage="planning",
        response="План грантовой заявки:\n1. Анализ целевой группы\n2. Обоснование актуальности...",
        success=True,
        tokens_used=250
    )

    logger.log_error(
        agent="researcher",
        stage="websearch",
        error="Connection timeout"
    )

    summary = logger.get_summary()
    print("\n" + "="*80)
    print("SUMMARY:")
    print("="*80)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
