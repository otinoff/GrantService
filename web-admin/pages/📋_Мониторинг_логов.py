#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Страница мониторинга логов для GrantService Admin Panel
Отображение, анализ и управление логами системы
"""

import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime, timedelta
import re
from pathlib import Path

import streamlit as st
import sys
import os

# Добавляем путь к проекту
sys.path.append('/var/GrantService')

# Проверка авторизации
from web_admin.utils.auth import is_user_authorized

if not is_user_authorized():
    # Импортируем страницу входа
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "login_page", 
        "/var/GrantService/web-admin/pages/🔐_Вход.py"
    )
    login_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(login_module)
    login_module.show_login_page()
    st.stop()
# Добавляем путь к проекту
sys.path.append('/var/GrantService')

from utils.logger import setup_logger, get_log_stats

# Инициализация логгера
logger = setup_logger('log_monitoring')

st.title("📋 Мониторинг логов")

# === СТАТИСТИКА ЛОГОВ ===
st.subheader("📊 Статистика логов")

log_stats = get_log_stats()

if 'error' in log_stats:
    st.error(f"❌ Ошибка получения статистики: {log_stats['error']}")
else:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Папка логов", "📁")
        st.code(log_stats['log_directory'])
    
    with col2:
        st.metric("Файлов логов", len(log_stats['files']))
    
    with col3:
        total_size_mb = log_stats['total_size'] / (1024 * 1024)
        st.metric("Общий размер", f"{total_size_mb:.1f} MB")
    
    with col4:
        if log_stats['last_modified']:
            st.metric("Последнее обновление", 
                     log_stats['last_modified'].strftime('%H:%M:%S'))

# === ФАЙЛЫ ЛОГОВ ===
st.subheader("📁 Файлы логов")

if log_stats['files']:
    # Создаем DataFrame для отображения
    df_files = pd.DataFrame(log_stats['files'])
    df_files['size_mb'] = (df_files['size'] / (1024 * 1024)).round(2)
    df_files = df_files.sort_values('modified', ascending=False)
    
    # Отображаем таблицу файлов
    st.dataframe(
        df_files[['name', 'size_mb', 'modified']].rename(columns={
            'name': 'Файл',
            'size_mb': 'Размер (MB)',
            'modified': 'Изменен'
        }),
        use_container_width=True
    )
    
    # === ПРОСМОТР ЛОГОВ ===
    st.subheader("🔍 Просмотр логов")
    
    # Выбор файла для просмотра
    log_files = [f['name'] for f in log_stats['files']]
    selected_file = st.selectbox("Выберите файл лога:", log_files)
    
    if selected_file:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Настройки просмотра
            lines_count = st.slider("Количество последних строк:", 10, 1000, 100)
            
        with col2:
            # Фильтры
            log_level = st.selectbox("Уровень логов:", 
                                   ["Все", "ERROR", "WARNING", "INFO", "DEBUG"])
        
        # Кнопки управления
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Обновить"):
                st.rerun()
        
        with col2:
            if st.button("📥 Скачать лог"):
                log_path = os.path.join(log_stats['log_directory'], selected_file)
                try:
                    with open(log_path, 'r', encoding='utf-8') as f:
                        log_content = f.read()
                    st.download_button(
                        label="💾 Скачать файл",
                        data=log_content,
                        file_name=selected_file,
                        mime="text/plain"
                    )
                except Exception as e:
                    st.error(f"Ошибка при чтении файла: {e}")
        
        with col3:
            if st.button("🗑️ Очистить лог"):
                if st.session_state.get('confirm_clear'):
                    log_path = os.path.join(log_stats['log_directory'], selected_file)
                    try:
                        open(log_path, 'w').close()
                        st.success("✅ Лог очищен")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Ошибка очистки: {e}")
                else:
                    st.session_state['confirm_clear'] = True
                    st.warning("⚠️ Нажмите еще раз для подтверждения")
        
        # === ОТОБРАЖЕНИЕ СОДЕРЖИМОГО ===
        st.subheader(f"📄 Содержимое: {selected_file}")
        
        log_path = os.path.join(log_stats['log_directory'], selected_file)
        
        try:
            # Читаем файл
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Берем последние строки
            recent_lines = lines[-lines_count:] if len(lines) > lines_count else lines
            
            # Фильтруем по уровню логов
            if log_level != "Все":
                filtered_lines = []
                for line in recent_lines:
                    if f" - {log_level} - " in line:
                        filtered_lines.append(line)
                recent_lines = filtered_lines
            
            if recent_lines:
                # Анализ логов
                error_count = sum(1 for line in recent_lines if " - ERROR - " in line)
                warning_count = sum(1 for line in recent_lines if " - WARNING - " in line)
                
                if error_count > 0 or warning_count > 0:
                    col1, col2 = st.columns(2)
                    with col1:
                        if error_count > 0:
                            st.error(f"❌ Найдено ошибок: {error_count}")
                    with col2:
                        if warning_count > 0:
                            st.warning(f"⚠️ Найдено предупреждений: {warning_count}")
                
                # Отображаем логи с цветовой кодировкой
                log_container = st.container()
                
                with log_container:
                    log_text = ""
                    for line in recent_lines:
                        # Определяем уровень лога для стилизации
                        if " - ERROR - " in line:
                            log_text += f"🔴 {line}"
                        elif " - WARNING - " in line:
                            log_text += f"🟡 {line}"
                        elif " - INFO - " in line:
                            log_text += f"🟢 {line}"
                        elif " - DEBUG - " in line:
                            log_text += f"🔵 {line}"
                        else:
                            log_text += f"⚪ {line}"
                    
                    st.code(log_text, language=None)
                    
                # Показываем общую информацию
                st.info(f"📊 Отображено: {len(recent_lines)} строк из {len(lines)} общих")
                
            else:
                st.info("📝 Нет записей соответствующих фильтру")
                
        except FileNotFoundError:
            st.error(f"❌ Файл не найден: {log_path}")
        except PermissionError:
            st.error(f"❌ Нет прав доступа к файлу: {log_path}")
        except Exception as e:
            st.error(f"❌ Ошибка чтения файла: {e}")
            logger.error(f"Error reading log file {selected_file}: {e}", exc_info=True)

else:
    st.info("📂 Нет файлов логов")

# === АНАЛИЗ ОШИБОК ===
st.subheader("🔍 Анализ ошибок")

if st.button("🔄 Анализировать последние ошибки"):
    error_analysis = {}
    
    for file_info in log_stats.get('files', []):
        if 'error' in file_info['name'].lower():
            log_path = os.path.join(log_stats['log_directory'], file_info['name'])
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Ищем уникальные ошибки
                errors = []
                for line in lines[-100:]:  # Последние 100 строк
                    if " - ERROR - " in line:
                        # Извлекаем сообщение об ошибке
                        parts = line.split(" - ERROR - ")
                        if len(parts) > 1:
                            error_msg = parts[1].strip()
                            errors.append(error_msg)
                
                if errors:
                    error_analysis[file_info['name']] = {
                        'count': len(errors),
                        'unique': len(set(errors)),
                        'recent': errors[-5:]  # 5 последних
                    }
                    
            except Exception as e:
                st.error(f"Ошибка анализа {file_info['name']}: {e}")
    
    if error_analysis:
        for filename, analysis in error_analysis.items():
            st.write(f"**{filename}:**")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Всего ошибок", analysis['count'])
            with col2:
                st.metric("Уникальных", analysis['unique'])
            
            if analysis['recent']:
                st.write("**Последние ошибки:**")
                for error in analysis['recent']:
                    st.code(error, language=None)
            st.markdown("---")
    else:
        st.success("✅ Недавних ошибок не обнаружено")

# === НАСТРОЙКИ ЛОГИРОВАНИЯ ===
st.subheader("⚙️ Настройки логирования")

with st.expander("🔧 Конфигурация логгера"):
    st.code(f"""
Текущие настройки логирования:
    
📁 Папка логов: {log_stats['log_directory']}
📊 Уровни логирования:
    - DEBUG: Детальная отладочная информация
    - INFO: Общие информационные сообщения  
    - WARNING: Предупреждения о потенциальных проблемах
    - ERROR: Ошибки выполнения
    - CRITICAL: Критические ошибки

🔄 Ротация логов:
    - По размеру: 10MB (5 бэкапов)
    - По времени: ежедневно (30 дней)
    - Отдельные файлы для ошибок

📝 Типы файлов:
    - [component].log - основные логи
    - [component]_errors.log - только ошибки  
    - [component]_daily.log - дневная ротация
    """, language=None)

# === REAL-TIME МОНИТОРИНГ ===
st.subheader("⚡ Real-time мониторинг")

if st.button("🔴 Создать тестовую ошибку"):
    logger.error("🧪 Тестовая ошибка для проверки логирования")
    logger.warning("⚠️ Тестовое предупреждение")
    logger.info("ℹ️ Тестовое информационное сообщение")
    st.success("✅ Тестовые сообщения созданы. Обновите страницу для просмотра.")

# Автообновление страницы
if st.checkbox("🔄 Автообновление (каждые 30 сек)"):
    import time
    time.sleep(30)
    st.rerun()

logger.info("📋 Страница мониторинга логов загружена")