#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для работы с логами исследователя и Perplexity API
"""

import json
import sqlite3
from typing import List, Dict, Any
from .models import GrantServiceDatabase, get_kuzbass_time

class ResearcherLogger:
    def __init__(self, db: GrantServiceDatabase):
        self.db = db
    
    def log_researcher_query(self, user_id: int, session_id: int, query_text: str, 
                           perplexity_response: str = None, sources: list = None, 
                           usage_stats: dict = None, cost: float = 0.0, 
                           status: str = 'success', error_message: str = None,
                           credit_balance: float = 0.0) -> int:
        """Логирование запроса исследователя с балансом"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO researcher_logs 
                    (user_id, session_id, query_text, perplexity_response, sources, usage_stats, cost, status, error_message, credit_balance)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id, session_id, query_text, perplexity_response,
                    json.dumps(sources) if sources else None,
                    json.dumps(usage_stats) if usage_stats else None,
                    cost, status, error_message, credit_balance
                ))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            print(f"Ошибка логирования запроса исследователя: {e}")
            return 0
    
    def get_researcher_logs(self, user_id: int = None, session_id: int = None, 
                          limit: int = 100, offset: int = 0) -> list:
        """Получение логов исследователя"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM researcher_logs WHERE 1=1"
                params = []
                
                if user_id:
                    query += " AND user_id = ?"
                    params.append(user_id)
                
                if session_id:
                    query += " AND session_id = ?"
                    params.append(session_id)
                
                query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                logs = []
                for row in rows:
                    # Безопасная обработка JSON полей
                    try:
                        sources = json.loads(row[5]) if row[5] else []
                    except (json.JSONDecodeError, TypeError):
                        sources = []
                    
                    try:
                        usage_stats = json.loads(row[6]) if row[6] else {}
                    except (json.JSONDecodeError, TypeError):
                        usage_stats = {}
                    
                    log = {
                        'id': row[0],
                        'user_id': row[1],
                        'session_id': row[2],
                        'query_text': row[3],
                        'perplexity_response': row[4],
                        'sources': sources,
                        'usage_stats': usage_stats,
                        'cost': row[7],
                        'status': row[8],
                        'error_message': row[9],
                        'credit_balance': row[10] if len(row) > 10 else 0.0,
                        'created_at': row[11] if len(row) > 11 else row[10]
                    }
                    logs.append(log)
                
                return logs
        except Exception as e:
            print(f"Ошибка получения логов исследователя: {e}")
            return []
    
    def get_researcher_statistics(self, days: int = 30) -> dict:
        """Получение статистики работы исследователя"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Общая статистика
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_queries,
                        COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_queries,
                        SUM(cost) as total_cost,
                        AVG(cost) as avg_cost,
                        COUNT(DISTINCT user_id) as unique_users
                    FROM researcher_logs 
                    WHERE created_at >= datetime('now', '-{} days')
                '''.format(days))
                
                stats = cursor.fetchone()
                
                # Популярные запросы
                cursor.execute('''
                    SELECT query_text, COUNT(*) as count
                    FROM researcher_logs 
                    WHERE created_at >= datetime('now', '-{} days')
                    GROUP BY query_text 
                    ORDER BY count DESC 
                    LIMIT 10
                '''.format(days))
                
                popular_queries = cursor.fetchall()
                
                # Статистика по дням
                cursor.execute('''
                    SELECT 
                        DATE(created_at) as date,
                        COUNT(*) as queries,
                        SUM(cost) as cost
                    FROM researcher_logs 
                    WHERE created_at >= datetime('now', '-{} days')
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                '''.format(days))
                
                daily_stats = cursor.fetchall()
                
                return {
                    'total_queries': stats[0] or 0,
                    'successful_queries': stats[1] or 0,
                    'total_cost': stats[2] or 0.0,
                    'avg_cost': stats[3] or 0.0,
                    'unique_users': stats[4] or 0,
                    'success_rate': (stats[1] / stats[0] * 100) if stats[0] else 0,
                    'popular_queries': [{'query': q[0], 'count': q[1]} for q in popular_queries],
                    'daily_stats': [{'date': d[0], 'queries': d[1], 'cost': d[2]} for d in daily_stats]
                }
            
        except Exception as e:
            print(f"Ошибка получения статистики исследователя: {e}")
            return {}

    def get_latest_credit_balance(self) -> float:
        """Получить последний известный баланс из логов"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT credit_balance FROM researcher_logs 
                    WHERE credit_balance > 0 
                    ORDER BY created_at DESC 
                    LIMIT 1
                ''')
                result = cursor.fetchone()
                return result[0] if result else 0.0
        except Exception as e:
            print(f"Ошибка получения последнего баланса: {e}")
            return 0.0

    def update_credit_balance(self, balance: float) -> bool:
        """Обновить баланс в последнем логе"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE researcher_logs 
                    SET credit_balance = ? 
                    WHERE id = (SELECT MAX(id) FROM researcher_logs)
                ''', (balance,))
                conn.commit()
                return True
        except Exception as e:
            print(f"Ошибка обновления баланса: {e}")
            return False

    def update_all_credit_balances(self, balance: float) -> bool:
        """Обновить баланс во всех последних логах"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE researcher_logs 
                    SET credit_balance = ? 
                    WHERE credit_balance > 0
                ''', (balance,))
                conn.commit()
                return True
        except Exception as e:
            print(f"Ошибка обновления всех балансов: {e}")
            return False

# Глобальные функции для совместимости
def get_researcher_logs(limit: int = 100) -> List[Dict]:
    """Получить логи исследователя"""
    try:
        from . import db
        logger = ResearcherLogger(db)
        return logger.get_researcher_logs(limit=limit)
    except Exception as e:
        print(f"Ошибка получения логов исследователя: {e}")
        return []

def add_researcher_log(user_id: int, session_id: int, query_text: str, 
                      result: str = None, sources: str = None, 
                      usage_stats: str = None, cost: float = 0.0, 
                      status: str = 'success', error_message: str = None,
                      credit_balance: float = 0.0) -> int:
    """Добавить лог исследователя"""
    try:
        from . import db
        logger = ResearcherLogger(db)
        return logger.log_researcher_query(
            user_id=user_id,
            session_id=session_id,
            query_text=query_text,
            perplexity_response=result,
            sources=json.loads(sources) if sources else None,
            usage_stats=json.loads(usage_stats) if usage_stats else None,
            cost=cost,
            status=status,
            error_message=error_message,
            credit_balance=credit_balance
        )
    except Exception as e:
        print(f"Ошибка добавления лога исследователя: {e}")
        return 0

def get_latest_credit_balance() -> float:
    """Получить последний известный баланс"""
    try:
        from . import db
        logger = ResearcherLogger(db)
        return logger.get_latest_credit_balance()
    except Exception as e:
        print(f"Ошибка получения баланса: {e}")
        return 0.0

def update_latest_credit_balance(balance: float) -> bool:
    """Обновить баланс в последнем логе"""
    try:
        from . import db
        logger = ResearcherLogger(db)
        return logger.update_credit_balance(balance)
    except Exception as e:
        print(f"Ошибка обновления баланса: {e}")
        return False

def update_all_credit_balances(balance: float) -> bool:
    """Обновить баланс во всех логах"""
    try:
        from . import db
        logger = ResearcherLogger(db)
        return logger.update_all_credit_balances(balance)
    except Exception as e:
        print(f"Ошибка обновления всех балансов: {e}")
        return False

def update_input_tokens_by_model(model: str, tokens: int) -> bool:
    """Обновляет input_tokens для конкретной модели"""
    try:
        from . import db
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        # Находим запись с нужной моделью
        cursor.execute("""
            SELECT id, usage_stats FROM researcher_logs 
            WHERE query_text LIKE ? AND usage_stats LIKE ?
        """, (f'%{model}%', f'%"model": "{model}"%'))
        
        result = cursor.fetchone()
        if result:
            log_id, usage_stats_str = result
            
            # Парсим JSON
            try:
                usage_stats = json.loads(usage_stats_str) if isinstance(usage_stats_str, str) else usage_stats_str
            except (json.JSONDecodeError, TypeError):
                usage_stats = {}
            
            # Обновляем input_tokens
            usage_stats['input_tokens'] = tokens
            
            # Сохраняем обратно в JSON
            updated_usage_stats = json.dumps(usage_stats)
            
            cursor.execute("""
                UPDATE researcher_logs 
                SET usage_stats = ? 
                WHERE id = ?
            """, (updated_usage_stats, log_id))
            
            conn.commit()
            conn.close()
            print(f"✅ Обновлены input_tokens для {model}: {tokens}")
            return True
        else:
            print(f"❌ Не найдена запись для модели {model}")
            return False
    except Exception as e:
        print(f"❌ Ошибка обновления input_tokens для {model}: {e}")
        return False 