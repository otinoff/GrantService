#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Health Checker - Проверка доступности всех API провайдеров
Author: System Integrator
Date: 2025-10-11
"""

import asyncio
import aiohttp
import requests
import json
import logging
from typing import Dict, Any
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class APIHealthChecker:
    """Проверка здоровья всех API провайдеров"""

    def __init__(self):
        self.claude_code_url = os.getenv('CLAUDE_CODE_BASE_URL', 'http://178.236.17.55:8000')
        self.claude_code_key = os.getenv('CLAUDE_CODE_API_KEY', '1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732')
        self.perplexity_key = os.getenv('PERPLEXITY_API_KEY', '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')
        self.gigachat_key = os.getenv('GIGACHAT_API_KEY', '')

        self.results = {}

    def check_all(self) -> Dict[str, Any]:
        """
        Проверить все API синхронно

        Returns:
            {
                'claude_code': {'status': 'online', 'latency': 123, 'features': [...]},
                'perplexity': {'status': 'online', 'latency': 456},
                'gigachat': {'status': 'offline', 'error': '...'},
                'overall_status': 'operational'  # operational / degraded / offline
            }
        """
        self.results = {
            'checked_at': datetime.now().isoformat(),
            'providers': {}
        }

        # Check Claude Code
        logger.info("[CHECK] Claude Code API...")
        self.results['providers']['claude_code'] = self._check_claude_code()

        # Check Claude Code WebSearch
        logger.info("[CHECK] Claude Code WebSearch...")
        self.results['providers']['websearch'] = self._check_websearch()

        # Check Perplexity
        logger.info("[CHECK] Perplexity API...")
        self.results['providers']['perplexity'] = self._check_perplexity()

        # Check GigaChat
        logger.info("[CHECK] GigaChat API...")
        self.results['providers']['gigachat'] = self._check_gigachat()

        # Determine overall status
        self.results['overall_status'] = self._determine_overall_status()

        return self.results

    def _check_claude_code(self) -> Dict[str, Any]:
        """Проверка Claude Code API"""
        try:
            start = datetime.now()
            response = requests.get(
                f"{self.claude_code_url}/health",
                timeout=5
            )
            latency = (datetime.now() - start).total_seconds() * 1000

            if response.status_code == 200:
                data = response.json()
                return {
                    'status': 'online',
                    'status_code': 200,
                    'latency_ms': round(latency, 2),
                    'features': data.get('features', []),
                    'active_sessions': data.get('active_sessions', 0),
                    'version': data.get('claude_version', 'unknown'),
                    'message': 'Healthy'
                }
            else:
                return {
                    'status': 'degraded',
                    'status_code': response.status_code,
                    'latency_ms': round(latency, 2),
                    'message': f'Status {response.status_code}'
                }

        except requests.exceptions.Timeout:
            return {
                'status': 'offline',
                'status_code': 0,
                'message': 'Timeout after 5s',
                'error': 'Connection timeout'
            }
        except Exception as e:
            return {
                'status': 'offline',
                'status_code': 0,
                'message': str(e),
                'error': type(e).__name__
            }

    def _check_websearch(self) -> Dict[str, Any]:
        """Проверка WebSearch endpoint"""
        try:
            start = datetime.now()
            response = requests.post(
                f"{self.claude_code_url}/websearch",
                headers={
                    'Authorization': f'Bearer {self.claude_code_key}',
                    'Content-Type': 'application/json'
                },
                json={'query': 'test', 'max_results': 1},
                timeout=10
            )
            latency = (datetime.now() - start).total_seconds() * 1000

            if response.status_code == 200:
                return {
                    'status': 'online',
                    'status_code': 200,
                    'latency_ms': round(latency, 2),
                    'message': 'WebSearch operational'
                }
            elif response.status_code == 500:
                # WebSearch 500 - недоступен на сервере
                return {
                    'status': 'unavailable',
                    'status_code': 500,
                    'latency_ms': round(latency, 2),
                    'message': 'WebSearch not available (geographical restriction)',
                    'error': 'Claude Code WebSearch недоступен на сервере. Используйте Perplexity.'
                }
            else:
                return {
                    'status': 'degraded',
                    'status_code': response.status_code,
                    'latency_ms': round(latency, 2),
                    'message': f'Status {response.status_code}'
                }

        except requests.exceptions.Timeout:
            return {
                'status': 'offline',
                'status_code': 0,
                'message': 'Timeout after 10s',
                'error': 'Connection timeout'
            }
        except Exception as e:
            return {
                'status': 'offline',
                'status_code': 0,
                'message': str(e),
                'error': type(e).__name__
            }

    def _check_perplexity(self) -> Dict[str, Any]:
        """Проверка Perplexity API"""
        try:
            start = datetime.now()
            response = requests.post(
                'https://api.perplexity.ai/chat/completions',
                headers={
                    'Authorization': f'Bearer {self.perplexity_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'sonar',
                    'messages': [{'role': 'user', 'content': 'test'}],
                    'max_tokens': 10
                },
                timeout=10
            )
            latency = (datetime.now() - start).total_seconds() * 1000

            if response.status_code == 200:
                return {
                    'status': 'online',
                    'status_code': 200,
                    'latency_ms': round(latency, 2),
                    'message': 'Perplexity operational'
                }
            elif response.status_code == 401:
                return {
                    'status': 'error',
                    'status_code': 401,
                    'latency_ms': round(latency, 2),
                    'message': 'Invalid API key',
                    'error': 'Authentication failed'
                }
            else:
                return {
                    'status': 'degraded',
                    'status_code': response.status_code,
                    'latency_ms': round(latency, 2),
                    'message': f'Status {response.status_code}'
                }

        except requests.exceptions.Timeout:
            return {
                'status': 'offline',
                'status_code': 0,
                'message': 'Timeout after 10s',
                'error': 'Connection timeout'
            }
        except Exception as e:
            return {
                'status': 'offline',
                'status_code': 0,
                'message': str(e),
                'error': type(e).__name__
            }

    def _check_gigachat(self) -> Dict[str, Any]:
        """Проверка GigaChat API"""
        if not self.gigachat_key:
            return {
                'status': 'not_configured',
                'status_code': 0,
                'message': 'API key not configured',
                'error': 'Missing GIGACHAT_API_KEY'
            }

        try:
            # GigaChat требует получения токена сначала
            # Пропускаем полноценную проверку, возвращаем configured
            return {
                'status': 'configured',
                'status_code': 0,
                'message': 'API key present (not tested)',
                'note': 'GigaChat authentication not tested in health check'
            }

        except Exception as e:
            return {
                'status': 'error',
                'status_code': 0,
                'message': str(e),
                'error': type(e).__name__
            }

    def _determine_overall_status(self) -> str:
        """Определить общий статус системы"""
        providers = self.results['providers']

        # Критические сервисы
        claude_code = providers.get('claude_code', {}).get('status', 'offline')
        perplexity = providers.get('perplexity', {}).get('status', 'offline')

        # Если Claude Code и Perplexity работают - всё хорошо
        if claude_code == 'online' and perplexity == 'online':
            return 'operational'

        # Если хотя бы один работает - частично работает
        if claude_code in ['online', 'degraded'] or perplexity in ['online', 'degraded']:
            return 'degraded'

        # Иначе - не работает
        return 'offline'

    def get_recommendations(self) -> Dict[str, Any]:
        """Получить рекомендации по использованию API"""
        providers = self.results.get('providers', {})

        recommendations = {
            'researcher_agent': 'unknown',
            'writer_agent': 'unknown',
            'websearch': 'unknown',
            'actions': []
        }

        # Researcher Agent
        perplexity_status = providers.get('perplexity', {}).get('status')
        websearch_status = providers.get('websearch', {}).get('status')

        if perplexity_status == 'online':
            recommendations['researcher_agent'] = 'perplexity'
            recommendations['websearch'] = 'perplexity'
            recommendations['actions'].append({
                'priority': 'high',
                'message': 'Используйте Perplexity для WebSearch (Claude Code WebSearch недоступен)'
            })
        elif websearch_status == 'online':
            recommendations['researcher_agent'] = 'claude_code'
            recommendations['websearch'] = 'claude_code'
        else:
            recommendations['researcher_agent'] = 'none'
            recommendations['websearch'] = 'none'
            recommendations['actions'].append({
                'priority': 'critical',
                'message': 'КРИТИЧНО: Нет доступных провайдеров для WebSearch!'
            })

        # Writer Agent
        claude_code_status = providers.get('claude_code', {}).get('status')
        gigachat_status = providers.get('gigachat', {}).get('status')

        if claude_code_status == 'online':
            recommendations['writer_agent'] = 'claude_code'
        elif gigachat_status in ['online', 'configured']:
            recommendations['writer_agent'] = 'gigachat'
        else:
            recommendations['writer_agent'] = 'claude_code'  # Fallback
            recommendations['actions'].append({
                'priority': 'medium',
                'message': 'Writer Agent может работать нестабильно'
            })

        # Проверка Claude Code WebSearch
        if websearch_status == 'unavailable':
            recommendations['actions'].append({
                'priority': 'info',
                'message': 'Claude Code WebSearch недоступен из-за географических ограничений. Настроен Perplexity в качестве замены.'
            })

        return recommendations


def check_api_health() -> Dict[str, Any]:
    """
    Простая функция для быстрой проверки API

    Usage:
        from shared.api_health_checker import check_api_health

        result = check_api_health()
        if result['overall_status'] == 'operational':
            print("All systems operational")
    """
    checker = APIHealthChecker()
    return checker.check_all()


def print_api_status():
    """Вывести статус API в консоль (для отладки)"""
    checker = APIHealthChecker()
    results = checker.check_all()

    print("=" * 80)
    print("API HEALTH CHECK REPORT")
    print("=" * 80)
    print(f"Checked at: {results['checked_at']}")
    print(f"Overall Status: {results['overall_status'].upper()}")
    print()

    for provider_name, provider_data in results['providers'].items():
        status = provider_data.get('status', 'unknown')
        status_icon = {
            'online': '[OK]',
            'degraded': '[WARN]',
            'offline': '[ERROR]',
            'unavailable': '[UNAVAIL]',
            'not_configured': '[NOT_CONF]',
            'configured': '[CONF]',
            'error': '[ERROR]'
        }.get(status, '[?]')

        print(f"{status_icon} {provider_name.upper()}")
        print(f"     Status: {status}")

        if 'latency_ms' in provider_data:
            print(f"     Latency: {provider_data['latency_ms']}ms")

        if 'message' in provider_data:
            print(f"     Message: {provider_data['message']}")

        if 'error' in provider_data:
            print(f"     Error: {provider_data['error']}")

        print()

    # Recommendations
    recommendations = checker.get_recommendations()
    print("-" * 80)
    print("RECOMMENDATIONS")
    print("-" * 80)
    print(f"Researcher Agent: Use {recommendations['researcher_agent'].upper()}")
    print(f"Writer Agent: Use {recommendations['writer_agent'].upper()}")
    print(f"WebSearch: Use {recommendations['websearch'].upper()}")

    if recommendations['actions']:
        print()
        print("Actions:")
        for action in recommendations['actions']:
            priority_icon = {
                'critical': '[!!!]',
                'high': '[!!]',
                'medium': '[!]',
                'info': '[i]'
            }.get(action['priority'], '[?]')
            print(f"  {priority_icon} {action['message']}")

    print("=" * 80)


if __name__ == "__main__":
    # Тестовый запуск
    print_api_status()
