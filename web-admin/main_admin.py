#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ГрантСервис - Веб-админ панель (Streamlit)
Модульная версия: только заголовок и стили
Кроссплатформенная версия
"""

import streamlit as st
import sys
import os

# Определяем пути
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# Добавляем пути для импортов
sys.path.insert(0, parent_dir)  # Для импорта config
sys.path.insert(0, current_dir)  # Для импорта utils

# Импортируем кроссплатформенные пути
from config import paths

# Инициализация логгера - пробуем разные варианты импорта
try:
    from utils.logger import setup_logger
except ImportError:
    try:
        # Если не получилось, добавляем web-admin в путь
        sys.path.insert(0, os.path.join(parent_dir, 'web-admin'))
        from utils.logger import setup_logger
    except ImportError:
        # Создаем заглушку если логгер не найден
        import logging
        def setup_logger(name):
            return logging.getLogger(name)

logger = setup_logger('main_admin')

st.set_page_config(
    page_title="🏆 ГрантСервис - Админ панель",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': 'ГрантСервис - Админ панель v2.0'
    }
)

# CSS стили
st.markdown("""
<style>
.main-header {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    padding: 1rem;
    border-radius: 10px;
    color: white;
    text-align: center;
    margin-bottom: 2rem;
}
.metric-card {
    background: #f8f9fa;
    padding: 1rem;
    border-radius: 8px;
    border-left: 4px solid #667eea;
}
.status-running {
    color: #28a745;
    font-weight: bold;
}
.status-error {
    color: #dc3545;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# Основной заголовок
st.markdown("""
<div class="main-header">
    <h1>🏆 ГрантСервис - Админ панель</h1>
    <p>Управление системой создания грантовых заявок</p>
</div>
""", unsafe_allow_html=True)

# Streamlit автоматически создаст навигацию для файлов в папке pages/
# Никакого дополнительного кода не нужно 