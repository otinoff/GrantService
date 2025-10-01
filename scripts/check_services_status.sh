#!/bin/bash
# Скрипт для проверки статуса всех сервисов GrantService
# Запускается на продакшн сервере

echo "========================================"
echo "  GrantService Health Check"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo ""

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для проверки сервиса
check_service() {
    local service_name=$1
    local display_name=$2

    echo -n "📦 $display_name: "

    if systemctl is-active --quiet $service_name; then
        echo -e "${GREEN}✓ Running${NC}"

        # Показываем uptime
        uptime=$(systemctl show $service_name --property=ActiveEnterTimestamp --value)
        echo "   └─ Started: $uptime"

        # Показываем последние 3 строки логов
        echo "   └─ Recent logs:"
        journalctl -u $service_name -n 3 --no-pager | sed 's/^/      /'

        return 0
    else
        echo -e "${RED}✗ Not running${NC}"

        # Показываем причину падения
        echo "   └─ Last error:"
        journalctl -u $service_name -n 5 --no-pager | sed 's/^/      /'

        return 1
    fi
    echo ""
}

# Функция для проверки порта
check_port() {
    local port=$1
    local service=$2

    echo -n "🌐 Port $port ($service): "

    if netstat -tuln 2>/dev/null | grep -q ":$port " || ss -tuln 2>/dev/null | grep -q ":$port "; then
        echo -e "${GREEN}✓ Open${NC}"
        return 0
    else
        echo -e "${RED}✗ Closed${NC}"
        return 1
    fi
}

# Функция для проверки процесса
check_process() {
    local process_name=$1
    local display_name=$2

    echo -n "🔍 $display_name process: "

    if pgrep -f "$process_name" > /dev/null; then
        pid=$(pgrep -f "$process_name" | head -1)
        echo -e "${GREEN}✓ Running (PID: $pid)${NC}"
        return 0
    else
        echo -e "${RED}✗ Not found${NC}"
        return 1
    fi
}

# ===================================
# Проверка systemd сервисов
# ===================================
echo "1️⃣  Systemd Services"
echo "-----------------------------------"

bot_status=0
admin_status=0

check_service "grantservice-bot" "Telegram Bot" || bot_status=1
echo ""
check_service "grantservice-admin" "Streamlit Admin" || admin_status=1
echo ""

# ===================================
# Проверка портов
# ===================================
echo "2️⃣  Network Ports"
echo "-----------------------------------"

port_8501=0
port_80=0

check_port "8501" "Streamlit" || port_8501=1
check_port "80" "Nginx" || port_80=1
echo ""

# ===================================
# Проверка процессов
# ===================================
echo "3️⃣  Processes"
echo "-----------------------------------"

check_process "streamlit run" "Streamlit"
check_process "python.*main.py" "Bot"
echo ""

# ===================================
# Проверка файлов
# ===================================
echo "4️⃣  Critical Files"
echo "-----------------------------------"

files_ok=0

# Проверка главного файла Streamlit
echo -n "📄 Streamlit entry point: "
if [ -f "/var/GrantService/web-admin/app_main.py" ]; then
    echo -e "${GREEN}✓ Found${NC}"
else
    echo -e "${RED}✗ Missing: /var/GrantService/web-admin/app_main.py${NC}"
    files_ok=1
fi

# Проверка главного файла бота
echo -n "📄 Bot entry point: "
if [ -f "/var/GrantService/telegram-bot/main.py" ]; then
    echo -e "${GREEN}✓ Found${NC}"
else
    echo -e "${RED}✗ Missing: /var/GrantService/telegram-bot/main.py${NC}"
    files_ok=1
fi

# Проверка БД
echo -n "💾 Database: "
if [ -f "/var/GrantService/data/grantservice.db" ]; then
    db_size=$(du -h /var/GrantService/data/grantservice.db | cut -f1)
    echo -e "${GREEN}✓ Found ($db_size)${NC}"
else
    echo -e "${RED}✗ Missing: /var/GrantService/data/grantservice.db${NC}"
    files_ok=1
fi

echo ""

# ===================================
# Проверка systemd конфигурации
# ===================================
echo "5️⃣  Systemd Configuration"
echo "-----------------------------------"

echo -n "⚙️  Admin service config: "
if [ -f "/etc/systemd/system/grantservice-admin.service" ]; then
    echo -e "${GREEN}✓ Found${NC}"

    # Проверяем путь к Streamlit
    entry_point=$(grep "ExecStart" /etc/systemd/system/grantservice-admin.service | grep -o "/var/GrantService/[^ ]*\.py")
    echo "   └─ Entry point: $entry_point"

    if echo "$entry_point" | grep -q "web-admin/app_main.py"; then
        echo -e "   └─ ${GREEN}✓ Correct path${NC}"
    else
        echo -e "   └─ ${RED}✗ Wrong path! Should be: /var/GrantService/web-admin/app_main.py${NC}"
        echo -e "   └─ ${YELLOW}Run: sudo bash /var/GrantService/scripts/update_admin_service.sh${NC}"
    fi
else
    echo -e "${RED}✗ Missing${NC}"
fi

echo ""

# ===================================
# Проверка доступности
# ===================================
echo "6️⃣  Service Availability"
echo "-----------------------------------"

echo -n "🌐 Streamlit HTTP: "
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8501 | grep -q "200\|302"; then
    echo -e "${GREEN}✓ Responding${NC}"
else
    echo -e "${RED}✗ Not responding${NC}"
fi

echo ""

# ===================================
# Сводка
# ===================================
echo "========================================"
echo "  Summary"
echo "========================================"

total_issues=$((bot_status + admin_status + port_8501 + files_ok))

if [ $total_issues -eq 0 ]; then
    echo -e "${GREEN}✅ All systems operational!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Found $total_issues issue(s)${NC}"
    echo ""
    echo "Quick fixes:"

    if [ $admin_status -eq 1 ]; then
        echo "  • Restart admin: sudo systemctl restart grantservice-admin"
        echo "  • Check logs: journalctl -u grantservice-admin -n 50"
        echo "  • Update service: sudo bash scripts/update_admin_service.sh"
    fi

    if [ $bot_status -eq 1 ]; then
        echo "  • Restart bot: sudo systemctl restart grantservice-bot"
        echo "  • Check logs: journalctl -u grantservice-bot -n 50"
    fi

    exit 1
fi
