from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import requests
import os
from dotenv import load_dotenv

load_dotenv('/var/GrantService/config/.env')

app = FastAPI(title="ГрантСервис - FastAPI Admin Panel")

@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
    <html>
        <head><title>ГрантСервис - FastAPI Admin</title></head>
        <body>
            <h1>🏆 ГрантСервис - FastAPI Admin</h1>
            <ul>
                <li><a href='/status'>Статус бота</a></li>
                <li><a href='/analytics'>Аналитика</a></li>
            </ul>
        </body>
    </html>
    """

@app.get("/status")
def get_bot_status():
    token = os.getenv('TELEGRAM_BOT_TOKEN', '')
    if not token:
        return {"status": "error", "reason": "No token set"}
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=5)
        if response.status_code == 200:
            return {"status": "running", "data": response.json()}
        else:
            return {"status": "error", "data": None}
    except Exception as e:
        return {"status": "error", "reason": str(e)}

@app.get("/analytics")
def get_analytics():
    # Заглушка, можно заменить на реальные данные из БД
    return {
        "total_sessions": 142,
        "completed_apps": 67,
        "conversion_rate": 47.2,
        "avg_time_minutes": 12,
        "daily_stats": {
            "Понедельник": 15,
            "Вторник": 23,
            "Среда": 18,
            "Четверг": 31,
            "Пятница": 42,
            "Суббота": 12,
            "Воскресенье": 8
        }
    } 