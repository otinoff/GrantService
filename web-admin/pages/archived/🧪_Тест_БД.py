#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовая страница для проверки подключения к БД
"""

import streamlit as st
import sqlite3
import os
import json

st.title("🧪 Тест подключения к БД")
st.markdown("---")

# Определяем путь к БД в зависимости от ОС
import os
if os.name == 'nt':  # Windows
    db_path = "C:/SnowWhiteAI/GrantService/data/grantservice.db"
else:  # Linux/Unix
    db_path = "/var/GrantService/data/grantservice.db"

st.write(f"**Путь к БД:** `{db_path}`")
st.write(f"**Файл существует:** {os.path.exists(db_path)}")

if os.path.exists(db_path):
    try:
        # Прямое подключение к БД
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        st.success("✅ Подключение к БД успешно!")
        
        # Проверяем таблицу grant_applications
        st.subheader("📊 Таблица grant_applications")
        
        cursor.execute("SELECT COUNT(*) FROM grant_applications")
        count = cursor.fetchone()[0]
        st.metric("Всего заявок в БД", count)
        
        if count > 0:
            st.write("**Последние 5 заявок:**")
            cursor.execute("""
                SELECT id, application_number, title, status, created_at 
                FROM grant_applications 
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            
            for row in cursor.fetchall():
                st.write(f"- **ID {row[0]}**: {row[1]} - {row[2]} (статус: {row[3]})")
        
        # Проверяем другие таблицы
        st.subheader("📊 Другие таблицы")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            st.write(f"- **{table_name}**: {count} записей")
        
        conn.close()
        
    except Exception as e:
        st.error(f"❌ Ошибка при работе с БД: {e}")
        import traceback
        st.code(traceback.format_exc())
else:
    st.error(f"❌ Файл БД не найден по пути: {db_path}")
    st.info("Проверьте путь к базе данных")