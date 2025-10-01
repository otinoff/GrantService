#!/bin/bash
# Скрипт для обновления systemd сервиса grantservice-admin
# Используется для исправления пути к Streamlit приложению

echo "========================================"
echo "  Updating grantservice-admin service"
echo "========================================"
echo ""

# Проверка прав
if [ "$EUID" -ne 0 ]; then
    echo "❌ Error: This script must be run as root (use sudo)"
    exit 1
fi

# Путь к сервису
SERVICE_FILE="/etc/systemd/system/grantservice-admin.service"

echo "📝 Creating updated systemd service..."

# Создание обновленного сервиса
tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=GrantService Streamlit Admin Panel
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/GrantService
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 -m streamlit run /var/GrantService/web-admin/app_main.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "✓ Service file updated"
echo ""

# Перезагрузка systemd
echo "🔄 Reloading systemd daemon..."
systemctl daemon-reload
echo "✓ Systemd reloaded"
echo ""

# Перезапуск сервиса
echo "🔄 Restarting grantservice-admin service..."
systemctl restart grantservice-admin
echo "✓ Service restarted"
echo ""

# Проверка статуса
echo "📊 Service status:"
systemctl status grantservice-admin --no-pager
echo ""

# Финальная проверка
if systemctl is-active --quiet grantservice-admin; then
    echo "✅ SUCCESS: grantservice-admin is running!"
    echo "🌐 Admin panel should be available at http://your-server:8501"
else
    echo "❌ ERROR: Service failed to start"
    echo "Check logs with: journalctl -u grantservice-admin -n 50"
    exit 1
fi

echo ""
echo "========================================"
echo "  Update completed successfully!"
echo "========================================"
