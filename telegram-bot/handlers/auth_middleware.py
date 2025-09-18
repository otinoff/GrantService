#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Middleware для проверки прав доступа в Telegram боте
"""

from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
import logging
import sys
import os

# Добавляем путь к модулю БД
sys.path.append('/var/GrantService')

from data.database import auth_manager, UserRole
from config.auth_config import AuthManager as ConfigAuthManager, Permission

logger = logging.getLogger(__name__)

class AuthMiddleware:
    """Middleware для проверки авторизации и прав доступа"""
    
    @staticmethod
    def require_auth(func):
        """Декоратор для проверки авторизации"""
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id
            
            # Проверяем авторизацию через БД
            if not ConfigAuthManager.is_authorized(user_id):
                await update.message.reply_text(
                    "❌ У вас нет доступа к этой функции.\n"
                    "Обратитесь к администратору для получения доступа."
                )
                logger.warning(f"Неавторизованный доступ: {user_id}")
                return
            
            return await func(update, context, *args, **kwargs)
        
        return wrapper
    
    @staticmethod
    def require_role(role: UserRole):
        """Декоратор для проверки роли пользователя"""
        def decorator(func):
            @wraps(func)
            async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
                user_id = update.effective_user.id
                
                # Получаем роль пользователя из БД
                user_role = auth_manager.get_user_role(user_id)
                
                # Проверяем иерархию ролей
                role_hierarchy = {
                    UserRole.USER.value: 0,
                    UserRole.VIEWER.value: 1,
                    UserRole.EDITOR.value: 2,
                    UserRole.ADMIN.value: 3
                }
                
                user_level = role_hierarchy.get(user_role, 0)
                required_level = role_hierarchy.get(role.value, 999)
                
                if user_level < required_level:
                    await update.message.reply_text(
                        f"❌ Недостаточно прав.\n"
                        f"Требуется роль: {role.value}\n"
                        f"Ваша роль: {user_role}"
                    )
                    logger.warning(f"Недостаточно прав: {user_id} ({user_role}) пытался получить доступ к функции для {role.value}")
                    return
                
                return await func(update, context, *args, **kwargs)
            
            return wrapper
        return decorator
    
    @staticmethod
    def require_permission(permission: Permission):
        """Декоратор для проверки конкретного разрешения"""
        def decorator(func):
            @wraps(func)
            async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
                user_id = update.effective_user.id
                
                if not ConfigAuthManager.has_permission(user_id, permission):
                    await update.message.reply_text(
                        f"❌ У вас нет разрешения: {permission.value}\n"
                        "Обратитесь к администратору для получения доступа."
                    )
                    logger.warning(f"Нет разрешения: {user_id} пытался использовать {permission.value}")
                    return
                
                return await func(update, context, *args, **kwargs)
            
            return wrapper
        return decorator
    
    @staticmethod
    def admin_only(func):
        """Декоратор для функций только для администраторов"""
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id
            
            if not auth_manager.is_admin(user_id):
                await update.message.reply_text(
                    "❌ Эта функция доступна только администраторам.\n"
                    "Обратитесь к главному администратору для получения прав."
                )
                logger.warning(f"Попытка админского доступа: {user_id}")
                return
            
            return await func(update, context, *args, **kwargs)
        
        return wrapper
    
    @staticmethod
    def editor_only(func):
        """Декоратор для функций только для редакторов и администраторов"""
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id
            
            if not auth_manager.can_edit_content(user_id):
                await update.message.reply_text(
                    "❌ Эта функция доступна только редакторам и администраторам.\n"
                    "Обратитесь к администратору для получения прав редактора."
                )
                logger.warning(f"Попытка редакторского доступа: {user_id}")
                return
            
            return await func(update, context, *args, **kwargs)
        
        return wrapper
    
    @staticmethod
    async def check_callback_auth(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Проверка авторизации для callback запросов"""
        user_id = update.effective_user.id
        
        if not ConfigAuthManager.is_authorized(user_id):
            await update.callback_query.answer(
                "❌ Доступ запрещен. Обратитесь к администратору.",
                show_alert=True
            )
            return False
        
        return True
    
    @staticmethod
    async def check_callback_role(update: Update, context: ContextTypes.DEFAULT_TYPE, required_role: UserRole) -> bool:
        """Проверка роли для callback запросов"""
        user_id = update.effective_user.id
        user_role = auth_manager.get_user_role(user_id)
        
        role_hierarchy = {
            UserRole.USER.value: 0,
            UserRole.VIEWER.value: 1,
            UserRole.EDITOR.value: 2,
            UserRole.ADMIN.value: 3
        }
        
        user_level = role_hierarchy.get(user_role, 0)
        required_level = role_hierarchy.get(required_role.value, 999)
        
        if user_level < required_level:
            await update.callback_query.answer(
                f"❌ Требуется роль: {required_role.value}",
                show_alert=True
            )
            return False
        
        return True
    
    @staticmethod
    def log_action(action: str):
        """Декоратор для логирования действий пользователя"""
        def decorator(func):
            @wraps(func)
            async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
                user_id = update.effective_user.id
                username = update.effective_user.username or "unknown"
                
                logger.info(f"Action: {action} | User: {user_id} (@{username})")
                
                try:
                    result = await func(update, context, *args, **kwargs)
                    
                    # Логируем в БД
                    auth_manager.log_auth_action(
                        user_id=user_id,
                        action=action,
                        success=True
                    )
                    
                    return result
                    
                except Exception as e:
                    logger.error(f"Error in {action}: {e}")
                    
                    # Логируем ошибку в БД
                    auth_manager.log_auth_action(
                        user_id=user_id,
                        action=action,
                        success=False,
                        error_message=str(e)
                    )
                    
                    raise
            
            return wrapper
        return decorator

# Экспортируем декораторы для удобства использования
require_auth = AuthMiddleware.require_auth
require_role = AuthMiddleware.require_role
require_permission = AuthMiddleware.require_permission
admin_only = AuthMiddleware.admin_only
editor_only = AuthMiddleware.editor_only
log_action = AuthMiddleware.log_action