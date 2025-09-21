#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Страница авторизации для GrantService Admin Panel
Впечатляющий дизайн с QR кодом и автообновлением
"""

import streamlit as st
import os
import time
from datetime import datetime
import qrcode
import io
from PIL import Image

def show_impressive_login_page():
    """Показать впечатляющую страницу входа через Telegram"""
    
    # Настройка стилей для полной ширины
    st.markdown("""
    <style>
    /* Убираем padding по умолчанию и используем всю ширину */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 5rem;
        padding-right: 5rem;
        max-width: 100%;
    }
    
    .main-container {
        max-width: 900px;
        margin: 0 auto;
        padding: 20px;
    }
    
    .main-title {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 30px;
        font-size: 48px;
    }
    
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 24px;
        margin-bottom: 40px;
    }
    
    .info-box {
        background-color: #f0f8ff;
        border-radius: 15px;
        padding: 30px;
        margin: 30px auto;
        border-left: 5px solid #0088cc;
        max-width: 700px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    .info-box h4 {
        font-size: 24px;
        margin-bottom: 15px;
    }
    
    .info-box p {
        font-size: 18px;
        line-height: 1.6;
    }
    
    .step-section {
        max-width: 700px;
        margin: 40px auto;
    }
    
    .step-section h3 {
        font-size: 28px;
        color: #333;
        margin-bottom: 20px;
    }
    
    .telegram-button {
        display: block;
        width: 100%;
        max-width: 500px;
        height: 70px;
        font-size: 24px;
        font-weight: bold;
        background-color: #0088cc;
        color: white;
        border-radius: 15px;
        border: none;
        cursor: pointer;
        margin: 20px auto;
        text-align: center;
        line-height: 70px;
        text-decoration: none;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,136,204,0.3);
    }
    
    .telegram-button:hover {
        background-color: #006699;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,136,204,0.4);
    }
    
    .security-note {
        background-color: #fff3cd;
        border-radius: 10px;
        padding: 20px;
        margin: 40px auto;
        border-left: 5px solid #ffc107;
        max-width: 700px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    .security-note strong {
        font-size: 20px;
    }
    
    .security-note ul {
        margin-top: 10px;
        font-size: 16px;
        line-height: 1.8;
    }
    
    .waiting-section {
        text-align: center;
        margin: 40px auto;
        max-width: 700px;
    }
    
    /* QR код контейнер */
    .qr-container {
        text-align: center;
        margin: 20px auto;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Основной контейнер
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # Заголовок
    st.markdown('<h1 class="main-title">🏛️ GrantService Admin Panel</h1>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Система управления грантовыми заявками</div>', unsafe_allow_html=True)
    
    # Информационный блок
    st.markdown("""
    <div class="info-box">
        <h4>🔐 Безопасная авторизация через Telegram</h4>
        <p>Для входа в админ-панель используется ваш Telegram аккаунт.<br>
        Никаких паролей запоминать не нужно - всё просто и безопасно!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Получаем имя бота
    bot_username = os.getenv('TELEGRAM_BOT_USERNAME', 'GrantServiceHelperBot')
    telegram_url = f"https://t.me/{bot_username}?start=get_access"
    
    # Секция с кнопкой
    st.markdown('<div class="step-section">', unsafe_allow_html=True)
    st.markdown("""
    <h3>📱 Шаг 1: Откройте Telegram бот</h3>
    <p style="font-size: 18px; color: #666; text-align: center;">
    Нажмите кнопку ниже, чтобы открыть наш бот в Telegram:
    </p>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <a href="{telegram_url}" target="_blank" class="telegram-button">
        🚀 Открыть @{bot_username}
    </a>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Инструкции
    st.markdown('<div class="step-section">', unsafe_allow_html=True)
    st.markdown("""
    <h3>🔗 Шаг 2: Получите ссылку для входа</h3>
    <ol style="font-size: 18px; line-height: 2;">
        <li>В боте автоматически выполнится команда <code>/get_access</code></li>
        <li>Бот пришлет вам уникальную ссылку для входа</li>
        <li>Перейдите по ссылке - и вы в системе!</li>
    </ol>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Ожидание авторизации
    st.markdown("""
    <div class="waiting-section">
        <h3>⏳ Ожидание авторизации...</h3>
        <p style="font-size: 18px; color: #666;">
        После получения ссылки в Telegram, перейдите по ней.<br>
        Страница обновится автоматически.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Автообновление
    st.markdown("""
    <script>
    setTimeout(function(){
        window.location.reload();
    }, 3000);
    </script>
    """, unsafe_allow_html=True)
    
    # Блок безопасности
    st.markdown("""
    <div class="security-note">
        <strong>🔒 Информация о безопасности:</strong>
        <ul>
            <li>Токены действуют 24 часа</li>
            <li>Каждый токен уникален и одноразовый</li>
            <li>Привязка к вашему Telegram ID</li>
            <li>Не делитесь ссылками с другими людьми</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # QR код в центре
    with st.container():
        with st.expander("📷 Альтернативный способ - QR код", expanded=False):
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                try:
                    # Генерируем QR код
                    qr = qrcode.QRCode(version=1, box_size=10, border=5)
                    qr.add_data(telegram_url)
                    qr.make(fit=True)
                    
                    img = qr.make_image(fill_color="black", back_color="white")
                    
                    # Конвертируем в байты
                    buf = io.BytesIO()
                    img.save(buf, format='PNG')
                    buf.seek(0)
                    
                    st.image(buf, caption=f"Сканируйте QR код для открытия @{bot_username}", width=300)
                    st.caption("Используйте камеру Telegram для сканирования")
                except Exception as e:
                    st.info("QR код будет доступен после установки библиотеки qrcode")
    
    st.markdown('</div>', unsafe_allow_html=True)