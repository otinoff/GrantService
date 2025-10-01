#!/bin/bash
# Быстрая проверка статуса сервисов - запустить на сервере

echo "=== GrantService Quick Check ==="
echo ""

# Проверка бота
echo -n "🤖 Bot: "
if systemctl is-active --quiet grantservice-bot; then
    echo "✓ Running"
else
    echo "✗ Stopped"
fi

# Проверка админки
echo -n "💻 Admin: "
if systemctl is-active --quiet grantservice-admin; then
    echo "✓ Running"
else
    echo "✗ Stopped"
fi

# Проверка порта
echo -n "🌐 Port 8550: "
if ss -tuln | grep -q ":8550 "; then
    echo "✓ Open"
else
    echo "✗ Closed"
fi

# Проверка файла
echo -n "📄 app_main.py: "
if [ -f "/var/GrantService/web-admin/app_main.py" ]; then
    echo "✓ Exists"
else
    echo "✗ Missing"
fi

echo ""
echo "Последние 5 строк логов админки:"
journalctl -u grantservice-admin -n 5 --no-pager
