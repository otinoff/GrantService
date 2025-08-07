#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест редактирования баланса Perplexity API
"""

import sys
import os

# Добавляем путь к модулям
sys.path.append('/var/GrantService')

from data.database import get_latest_credit_balance, update_latest_credit_balance, update_all_credit_balances

def test_balance_edit():
    """Тест редактирования баланса"""
    print("🔍 Тестирование редактирования баланса Perplexity API")
    print("=" * 50)
    
    # Получаем текущий баланс
    current_balance = get_latest_credit_balance()
    print(f"💰 Текущий баланс: ${current_balance:.6f} USD")
    
    # Тестируем обновление баланса
    new_balance = 0.747174  # Актуальный баланс из скрина
    
    print(f"\n📝 Обновляем баланс на: ${new_balance:.6f} USD")
    
    # Обновляем последний лог
    if update_latest_credit_balance(new_balance):
        print("✅ Баланс в последнем логе обновлен")
    else:
        print("❌ Ошибка обновления баланса в последнем логе")
    
    # Обновляем все логи
    if update_all_credit_balances(new_balance):
        print("✅ Баланс во всех логах обновлен")
    else:
        print("❌ Ошибка обновления баланса во всех логах")
    
    # Проверяем результат
    updated_balance = get_latest_credit_balance()
    print(f"\n💰 Обновленный баланс: ${updated_balance:.6f} USD")
    
    if abs(updated_balance - new_balance) < 0.000001:
        print("✅ Баланс успешно обновлен!")
    else:
        print("❌ Баланс не обновился корректно")
    
    print("\n✅ Тест завершен!")

if __name__ == "__main__":
    test_balance_edit() 