#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для работы с авторизацией и ролями пользователей (PostgreSQL)
"""

import json
import time
import secrets
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum

class UserRole(Enum):
    """Роли пользователей в системе"""
    ADMIN = "admin"          # Полный доступ ко всем функциям
    EDITOR = "editor"        # Доступ к редактированию контента
    VIEWER = "viewer"        # Только просмотр
    USER = "user"            # Обычный пользователь Telegram бота

class UserPermission(Enum):
    """Разрешения пользователей в системе"""
    VIEW_ANALYTICS = "view_analytics"     # Просмотр аналитики
    EDIT_QUESTIONS = "edit_questions"     # Редактирование вопросов
    EDIT_PROMPTS = "edit_prompts"         # Редактирование промптов
    MANAGE_USERS = "manage_users"         # Управление пользователями
    EXPORT_DATA = "export_data"           # Экспорт данных
    REVIEW_GRANTS = "review_grants"       # Проверка грантов
    SEND_MESSAGES = "send_messages"       # Отправка сообщений

class AuthManager:
    """Менеджер авторизации и управления ролями (PostgreSQL)"""

    def __init__(self, db):
        self.db = db
        self._ensure_auth_tables()

    def _ensure_auth_tables(self):
        """Проверить наличие необходимых полей для авторизации"""
        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()

                # Проверяем наличие колонок в таблице users
                cursor.execute("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'users'
                """)

                columns = [row[0] for row in cursor.fetchall()]

                # Добавляем колонку role если её нет
                if 'role' not in columns:
                    cursor.execute("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user'")
                    conn.commit()
                    print("Добавлено поле role в таблицу users")

                # Добавляем колонку permissions если её нет
                if 'permissions' not in columns:
                    cursor.execute("ALTER TABLE users ADD COLUMN permissions TEXT")
                    conn.commit()
                    print("Добавлено поле permissions в таблицу users")

                # Добавляем колонку token_expires_at если её нет
                if 'token_expires_at' not in columns:
                    cursor.execute("ALTER TABLE users ADD COLUMN token_expires_at TIMESTAMP")
                    conn.commit()
                    print("Добавлено поле token_expires_at в таблицу users")

                # Таблица auth_logs уже существует в миграции
                # Таблица page_permissions уже существует в миграции

                cursor.close()
                print("Таблицы авторизации инициализированы")

        except Exception as e:
            print(f"Ошибка создания таблиц авторизации: {e}")

    def set_user_role(self, telegram_id: int, role: str) -> bool:
        """Установить роль пользователя"""
        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()

                # Проверяем валидность роли
                valid_roles = [r.value for r in UserRole]
                if role not in valid_roles:
                    print(f"Недопустимая роль: {role}")
                    return False

                cursor.execute("""
                    UPDATE users SET role = %s WHERE telegram_id = %s
                """, (role, telegram_id))

                conn.commit()
                cursor.close()
                print(f"Установлена роль {role} для пользователя {telegram_id}")
                return True

        except Exception as e:
            print(f"Ошибка установки роли: {e}")
            return False

    def get_user_role(self, telegram_id: int) -> Optional[str]:
        """Получить роль пользователя"""
        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT role FROM users WHERE telegram_id = %s
                """, (telegram_id,))

                result = cursor.fetchone()
                cursor.close()

                if result:
                    return result[0] or UserRole.USER.value
                return UserRole.USER.value

        except Exception as e:
            print(f"Ошибка получения роли: {e}")
            return UserRole.USER.value

    def is_admin(self, telegram_id: int) -> bool:
        """Проверить, является ли пользователь администратором"""
        role = self.get_user_role(telegram_id)
        return role == UserRole.ADMIN.value

    def is_editor(self, telegram_id: int) -> bool:
        """Проверить, является ли пользователь редактором"""
        role = self.get_user_role(telegram_id)
        return role == UserRole.EDITOR.value

    def can_edit_content(self, telegram_id: int) -> bool:
        """Проверить, может ли пользователь редактировать контент"""
        role = self.get_user_role(telegram_id)
        return role in [UserRole.ADMIN.value, UserRole.EDITOR.value]

    def can_view_analytics(self, telegram_id: int) -> bool:
        """Проверить, может ли пользователь просматривать аналитику"""
        role = self.get_user_role(telegram_id)
        return role in [UserRole.ADMIN.value, UserRole.EDITOR.value, UserRole.VIEWER.value]

    def set_user_permissions(self, telegram_id: int, permissions: List[str]) -> bool:
        """Установить дополнительные разрешения пользователю"""
        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()

                permissions_json = json.dumps(permissions)
                cursor.execute("""
                    UPDATE users SET permissions = %s WHERE telegram_id = %s
                """, (permissions_json, telegram_id))

                conn.commit()
                cursor.close()
                print(f"Установлены разрешения для пользователя {telegram_id}")
                return True

        except Exception as e:
            print(f"Ошибка установки разрешений: {e}")
            return False

    def get_user_permissions(self, telegram_id: int) -> List[str]:
        """Получить дополнительные разрешения пользователя"""
        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT permissions FROM users WHERE telegram_id = %s
                """, (telegram_id,))

                result = cursor.fetchone()
                cursor.close()

                if result and result[0]:
                    return json.loads(result[0])
                return []

        except Exception as e:
            print(f"Ошибка получения разрешений: {e}")
            return []

    def log_auth_action(self, user_id: int, action: str, success: bool = True,
                       error_message: str = None, ip_address: str = None,
                       user_agent: str = None):
        """Записать действие авторизации в лог"""
        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO auth_logs (user_id, action, ip_address, user_agent,
                                         success, error_message, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (user_id, action, ip_address, user_agent, success,
                     error_message, datetime.now()))

                conn.commit()
                cursor.close()

        except Exception as e:
            print(f"Ошибка записи в лог авторизации: {e}")

    def get_auth_logs(self, user_id: int = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Получить логи авторизации"""
        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()

                if user_id:
                    cursor.execute("""
                        SELECT * FROM auth_logs
                        WHERE user_id = %s
                        ORDER BY created_at DESC
                        LIMIT %s
                    """, (user_id, limit))
                else:
                    cursor.execute("""
                        SELECT al.*, u.username, u.first_name, u.last_name
                        FROM auth_logs al
                        LEFT JOIN users u ON al.user_id = u.id
                        ORDER BY al.created_at DESC
                        LIMIT %s
                    """, (limit,))

                columns = [desc[0] for desc in cursor.description]
                logs = []

                for row in cursor.fetchall():
                    log_dict = dict(zip(columns, row))
                    logs.append(log_dict)

                cursor.close()
                return logs

        except Exception as e:
            print(f"Ошибка получения логов: {e}")
            return []

    def set_page_permissions(self, page_name: str, required_role: str = None,
                            required_permissions: List[str] = None,
                            description: str = None) -> bool:
        """Установить требования доступа к странице"""
        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()

                permissions_json = json.dumps(required_permissions) if required_permissions else None

                # PostgreSQL использует INSERT ... ON CONFLICT
                cursor.execute("""
                    INSERT INTO page_permissions
                    (page_name, required_role, required_permissions, description)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (page_name)
                    DO UPDATE SET
                        required_role = EXCLUDED.required_role,
                        required_permissions = EXCLUDED.required_permissions,
                        description = EXCLUDED.description
                """, (page_name, required_role, permissions_json, description))

                conn.commit()
                cursor.close()
                print(f"Установлены права доступа для страницы {page_name}")
                return True

        except Exception as e:
            print(f"Ошибка установки прав страницы: {e}")
            return False

    def can_access_page(self, telegram_id: int, page_name: str) -> bool:
        """Проверить доступ пользователя к странице"""
        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()

                # Получаем требования страницы
                cursor.execute("""
                    SELECT required_role, required_permissions
                    FROM page_permissions
                    WHERE page_name = %s AND is_active = TRUE
                """, (page_name,))

                page_req = cursor.fetchone()
                if not page_req:
                    # Если страница не настроена, доступ открыт
                    cursor.close()
                    return True

                required_role, required_permissions_json = page_req

                # Получаем роль пользователя
                user_role = self.get_user_role(telegram_id)

                # Админы имеют доступ везде
                if user_role == UserRole.ADMIN.value:
                    cursor.close()
                    return True

                # Проверяем роль
                if required_role:
                    role_hierarchy = {
                        UserRole.USER.value: 0,
                        UserRole.VIEWER.value: 1,
                        UserRole.EDITOR.value: 2,
                        UserRole.ADMIN.value: 3
                    }

                    user_level = role_hierarchy.get(user_role, 0)
                    required_level = role_hierarchy.get(required_role, 999)

                    if user_level < required_level:
                        cursor.close()
                        return False

                # Проверяем дополнительные разрешения
                if required_permissions_json:
                    required_permissions = json.loads(required_permissions_json)
                    user_permissions = self.get_user_permissions(telegram_id)

                    # Проверяем, есть ли хотя бы одно из требуемых разрешений
                    if not any(perm in user_permissions for perm in required_permissions):
                        cursor.close()
                        return False

                cursor.close()
                return True

        except Exception as e:
            print(f"Ошибка проверки доступа к странице: {e}")
            return False

    def get_accessible_pages(self, telegram_id: int) -> List[str]:
        """Получить список доступных страниц для пользователя"""
        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT page_name FROM page_permissions WHERE is_active = TRUE
                """)

                all_pages = cursor.fetchall()
                accessible_pages = []

                for (page_name,) in all_pages:
                    if self.can_access_page(telegram_id, page_name):
                        accessible_pages.append(page_name)

                cursor.close()
                return accessible_pages

        except Exception as e:
            print(f"Ошибка получения доступных страниц: {e}")
            return []

    def get_users_by_role(self, role: str) -> List[Dict[str, Any]]:
        """Получить всех пользователей с определенной ролью"""
        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT id, telegram_id, username, first_name, last_name, role,
                           created_at, last_active
                    FROM users
                    WHERE role = %s
                    ORDER BY created_at DESC
                """, (role,))

                columns = [desc[0] for desc in cursor.description]
                users = []

                for row in cursor.fetchall():
                    user_dict = dict(zip(columns, row))
                    users.append(user_dict)

                cursor.close()
                return users

        except Exception as e:
            print(f"Ошибка получения пользователей по роли: {e}")
            return []

# Глобальные функции для обратной совместимости
def create_login_token() -> str:
    """Генерирует новый токен для входа"""
    timestamp = int(time.time())
    random_hex = secrets.token_hex(16)
    return f"token_{timestamp}_{random_hex}"

def verify_login_token(token: str) -> bool:
    """Проверяет валидность токена (действителен 24 часа)"""
    print(f"[AUTH] Проверка токена verify_login_token")
    print(f"[AUTH] Входной токен (длина {len(token) if token else 0}): {token}")

    if not token:
        print("[AUTH] ❌ Токен пустой")
        return False

    token_timestamp = None

    # Формат 1: token_timestamp_hash (с подчеркиваниями)
    if '_' in token:
        parts = token.split('_')
        print(f"[AUTH] Обнаружен формат с подчеркиваниями, частей: {len(parts)}")
        if len(parts) >= 3:
            try:
                token_timestamp = int(parts[1])
                print(f"[AUTH] Извлечен timestamp из формата с подчеркиваниями: {token_timestamp}")
            except (ValueError, IndexError):
                pass

    # Формат 2: tokenTIMESTAMPHASH (без подчеркиваний, фиксированные позиции)
    if not token_timestamp and token.startswith('token') and len(token) == 47:
        print(f"[AUTH] Обнаружен формат без подчеркиваний (длина 47)")
        try:
            # Позиции: token(5) + timestamp(10) + hash(32) = 47
            timestamp_str = token[5:15]  # позиции 5-14 (10 цифр)

            # Проверяем, что timestamp состоит из цифр
            if timestamp_str.isdigit():
                token_timestamp = int(timestamp_str)
                print(f"[AUTH] Извлечен timestamp из формата без подчеркиваний: {token_timestamp}")
        except (ValueError, IndexError) as e:
            print(f"[AUTH] Ошибка парсинга формата без подчеркиваний: {e}")

    # Проверяем, удалось ли извлечь timestamp
    if token_timestamp:
        current_time = int(time.time())
        time_diff = current_time - token_timestamp
        print(f"[AUTH] Timestamp: {token_timestamp}, текущее: {current_time}, разница: {time_diff} сек")

        # Токен действителен 24 часа (86400 секунд)
        is_valid = time_diff < 86400
        print(f"[AUTH] Результат проверки: {'✅ ВАЛИДЕН' if is_valid else '❌ ИСТЕК'}")
        return is_valid

    print(f"[AUTH] ❌ Не удалось извлечь timestamp из токена")
    print(f"[AUTH] ❌ Токен невалиден")
    return False

def get_or_create_login_token(telegram_id: int) -> Optional[str]:
    """Получает или создает токен для пользователя"""
    from . import db
    return db.get_or_create_login_token(telegram_id)

def cleanup_expired_tokens():
    """Очистка истекших токенов"""
    try:
        from . import db
        with db.connect() as conn:
            cursor = conn.cursor()

            # Очищаем токены старше 24 часов (PostgreSQL syntax)
            cursor.execute("""
                UPDATE users
                SET login_token = NULL, token_expires_at = NULL
                WHERE token_expires_at < NOW() - INTERVAL '1 day'
            """)

            conn.commit()
            cursor.close()
            print("Истекшие токены очищены")

    except Exception as e:
        print(f"Ошибка очистки токенов: {e}")

# Функции для работы с ролями
def get_user_role(telegram_id: int) -> Optional[str]:
    """Получить роль пользователя"""
    from . import db
    auth_manager = AuthManager(db)
    return auth_manager.get_user_role(telegram_id)

def set_user_role(telegram_id: int, role: str) -> bool:
    """Установить роль пользователя"""
    from . import db
    auth_manager = AuthManager(db)
    return auth_manager.set_user_role(telegram_id, role)
