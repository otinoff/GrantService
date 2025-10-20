#!/usr/bin/env python3
"""
Автоматическое обновление OAuth токена для Claude Code CLI
Использует refresh token для получения нового access token

Использование:
    python3 auto_refresh_claude_oauth.py

Установить в cron:
    0 */6 * * * /usr/bin/python3 /root/auto_refresh_claude_oauth.py >> /var/log/claude-oauth-refresh.log 2>&1
"""

import json
import time
import sys
from pathlib import Path
from datetime import datetime, timedelta
import urllib.request
import urllib.error

# Конфигурация
CREDENTIALS_PATH = Path.home() / ".claude" / ".credentials.json"
BACKUP_DIR = Path.home() / ".claude" / "backups"
OAUTH_TOKEN_URL = "https://api.anthropic.com/v1/oauth/token"
CLIENT_ID = "claude-code-cli"  # Стандартный client_id для Claude CLI

# Минимальное время до истечения для обновления (в днях)
REFRESH_THRESHOLD_DAYS = 1

def log(message: str):
    """Логирование с timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def load_credentials() -> dict:
    """Загрузить текущие credentials"""
    try:
        with open(CREDENTIALS_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        log(f"❌ Credentials file not found: {CREDENTIALS_PATH}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        log(f"❌ Invalid JSON in credentials file: {e}")
        sys.exit(1)

def save_credentials(data: dict):
    """Сохранить credentials с backup"""
    # Создать backup
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = BACKUP_DIR / f"credentials-{timestamp}.json"

    # Backup старого файла
    if CREDENTIALS_PATH.exists():
        with open(CREDENTIALS_PATH, 'r') as f:
            old_data = json.load(f)
        with open(backup_path, 'w') as f:
            json.dump(old_data, f, indent=2)
        log(f"📦 Backup saved: {backup_path}")

    # Сохранить новый
    with open(CREDENTIALS_PATH, 'w') as f:
        json.dump(data, f, indent=2)
    log(f"✅ Credentials saved: {CREDENTIALS_PATH}")

def check_token_expiry(credentials: dict) -> tuple[bool, float]:
    """
    Проверить срок истечения токена
    Возвращает (needs_refresh, days_remaining)
    """
    oauth_data = credentials.get("claudeAiOauth", {})
    expires_at = oauth_data.get("expiresAt", 0)

    if expires_at == 0:
        log("⚠️ No expiration time found")
        return False, 0

    # Конвертация milliseconds → seconds
    expires_at_seconds = expires_at / 1000
    now = time.time()

    days_remaining = (expires_at_seconds - now) / 86400

    log(f"📅 Token expires in: {days_remaining:.2f} days")

    needs_refresh = days_remaining < REFRESH_THRESHOLD_DAYS
    return needs_refresh, days_remaining

def refresh_access_token(refresh_token: str) -> dict:
    """
    Обновить access token используя refresh token

    Returns:
        dict: {"access_token": "...", "refresh_token": "...", "expires_in": 3600}
    """
    log(f"🔄 Requesting new token from: {OAUTH_TOKEN_URL}")

    # Подготовка данных запроса
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID
    }

    # Конвертация в JSON
    json_data = json.dumps(data).encode('utf-8')

    # HTTP запрос
    request = urllib.request.Request(
        OAUTH_TOKEN_URL,
        data=json_data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Claude-Code-CLI-Auto-Refresh/1.0"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            response_data = json.loads(response.read().decode('utf-8'))
            log("✅ Token refresh successful")
            return response_data

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        log(f"❌ HTTP Error {e.code}: {error_body}")
        raise
    except urllib.error.URLError as e:
        log(f"❌ URL Error: {e.reason}")
        raise
    except Exception as e:
        log(f"❌ Unexpected error: {e}")
        raise

def update_credentials_with_new_token(credentials: dict, token_response: dict) -> dict:
    """
    Обновить credentials новым токеном
    """
    oauth_data = credentials["claudeAiOauth"]

    # Обновить access token
    if "access_token" in token_response:
        oauth_data["accessToken"] = token_response["access_token"]
        log(f"✅ Access token updated")

    # Обновить refresh token (если пришел новый)
    if "refresh_token" in token_response:
        oauth_data["refreshToken"] = token_response["refresh_token"]
        log(f"✅ Refresh token updated")

    # Обновить время истечения
    if "expires_in" in token_response:
        expires_in_seconds = token_response["expires_in"]
        new_expires_at = int((time.time() + expires_in_seconds) * 1000)
        oauth_data["expiresAt"] = new_expires_at

        days_valid = expires_in_seconds / 86400
        log(f"✅ New token valid for: {days_valid:.2f} days")

    credentials["claudeAiOauth"] = oauth_data
    return credentials

def main():
    """Основная логика"""
    log("=" * 60)
    log("🚀 Claude OAuth Auto-Refresh Started")
    log("=" * 60)

    # 1. Загрузить credentials
    log("📖 Loading credentials...")
    credentials = load_credentials()

    oauth_data = credentials.get("claudeAiOauth", {})
    if not oauth_data:
        log("❌ No OAuth data found in credentials")
        sys.exit(1)

    subscription_type = oauth_data.get("subscriptionType", "unknown")
    log(f"📊 Subscription: {subscription_type}")

    # 2. Проверить срок истечения
    needs_refresh, days_remaining = check_token_expiry(credentials)

    if not needs_refresh:
        log(f"✅ Token is still valid ({days_remaining:.2f} days remaining)")
        log("ℹ️ No refresh needed")
        return

    log(f"⚠️ Token expiring soon! ({days_remaining:.2f} days remaining)")
    log(f"🔄 Starting refresh process...")

    # 3. Получить refresh token
    refresh_token = oauth_data.get("refreshToken")
    if not refresh_token:
        log("❌ No refresh token found!")
        log("⚠️ Manual re-login required: claude login")
        sys.exit(1)

    log(f"🔑 Refresh token found: {refresh_token[:20]}...")

    # 4. Обновить токен
    try:
        token_response = refresh_access_token(refresh_token)
    except Exception as e:
        log(f"❌ Failed to refresh token: {e}")
        log("⚠️ Manual re-login may be required: claude login")
        sys.exit(1)

    # 5. Обновить credentials
    log("💾 Updating credentials file...")
    updated_credentials = update_credentials_with_new_token(credentials, token_response)

    # 6. Сохранить
    save_credentials(updated_credentials)

    # 7. Финальная проверка
    log("🔍 Verifying updated credentials...")
    final_check = load_credentials()
    needs_refresh_after, days_remaining_after = check_token_expiry(final_check)

    if days_remaining_after > days_remaining:
        log(f"✅ SUCCESS! Token refreshed successfully")
        log(f"📅 New expiration: {days_remaining_after:.2f} days from now")
    else:
        log(f"⚠️ WARNING: Token expiration did not increase as expected")

    log("=" * 60)
    log("✅ Auto-Refresh Completed")
    log("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n⚠️ Interrupted by user")
        sys.exit(130)
    except Exception as e:
        log(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
