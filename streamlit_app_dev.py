"""
Streamlit Admin Panel - DEV версия для @Grafana_SnowWhite_bot
"""
import streamlit as st
import os
import sys
import time

# Добавляем путь к модулям
sys.path.insert(0, 'C:\\SnowWhiteAI\\GrantService')

from data.database import db, auth_manager

# DEV БОТ - ВАЖНО!
DEV_BOT_USERNAME = "Grafana_SnowWhite_bot"
PROD_BOT_USERNAME = "GrantServiceHelperBot"

# Используем DEV бота для разработки
CURRENT_BOT = DEV_BOT_USERNAME  # <-- МЕНЯЙТЕ НА PROD_BOT_USERNAME для продакшна

def show_login_page():
    """Показать страницу входа с правильной ссылкой на DEV бота"""
    st.markdown("""
    <style>
    .stButton > button {
        width: 100%;
        height: 60px;
        font-size: 20px;
        background-color: #0088cc;
        color: white;
        border-radius: 10px;
        border: none;
        cursor: pointer;
    }
    .stButton > button:hover {
        background-color: #006699;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("🔐 Вход в админ-панель GrantService")
    
    # Показываем какой бот используется
    if CURRENT_BOT == DEV_BOT_USERNAME:
        st.warning(f"⚠️ DEV окружение: @{DEV_BOT_USERNAME}")
    else:
        st.info(f"✅ PROD окружение: @{PROD_BOT_USERNAME}")
    
    st.markdown("---")
    
    st.markdown("""
    ### Для получения доступа:
    
    1. Нажмите кнопку ниже для перехода в Telegram бот
    2. Бот автоматически сгенерирует токен доступа
    3. Страница обновится автоматически после получения токена
    """)
    
    # Правильная ссылка на текущего бота
    bot_link = f"https://t.me/{CURRENT_BOT}?start=get_access"
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button(f"🤖 Открыть @{CURRENT_BOT}", key="open_bot"):
            st.markdown(f'<meta http-equiv="refresh" content="0; url={bot_link}">', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Проверяем наличие токена в URL каждые 3 секунды
    query_params = st.experimental_get_query_params()
    if 'token' in query_params:
        token = query_params['token'][0]
        if token:
            # Валидируем токен
            telegram_id = db.validate_login_token(token)
            if telegram_id:
                st.success("✅ Токен получен! Выполняется вход...")
                st.session_state['authenticated'] = True
                st.session_state['user_id'] = telegram_id
                st.session_state['token'] = token
                time.sleep(1)
                st.experimental_rerun()
            else:
                st.error("❌ Недействительный или истекший токен")
    
    # Автообновление страницы
    st.markdown("""
    <script>
    setTimeout(function(){
        window.location.reload();
    }, 3000);
    </script>
    """, unsafe_allow_html=True)

def main():
    st.set_page_config(
        page_title="GrantService Admin - DEV",
        page_icon="🔧",
        layout="wide"
    )
    
    # Проверяем аутентификацию
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    
    if not st.session_state['authenticated']:
        show_login_page()
    else:
        st.success(f"✅ Вы вошли в систему! (DEV окружение)")
        st.write(f"User ID: {st.session_state.get('user_id', 'Unknown')}")
        
        if st.button("Выйти"):
            st.session_state['authenticated'] = False
            st.experimental_rerun()

if __name__ == "__main__":
    main()