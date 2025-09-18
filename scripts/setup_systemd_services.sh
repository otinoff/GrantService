#!/bin/bash
# Скрипт для создания systemd сервисов

echo "Creating systemd service for Telegram bot..."

# Создание сервиса для бота
sudo tee /etc/systemd/system/grantservice-bot.service > /dev/null <<EOF
[Unit]
Description=GrantService Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/GrantService/telegram-bot
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 /var/GrantService/telegram-bot/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "Creating systemd service for Admin panel..."

# Создание сервиса для админки
sudo tee /etc/systemd/system/grantservice-admin.service > /dev/null <<EOF
[Unit]
Description=GrantService Streamlit Admin Panel
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/GrantService/web-admin
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 -m streamlit run /var/GrantService/web-admin/pages/🏠_Главная.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Перезагрузка systemd
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

# Включение автозапуска
echo "Enabling services..."
sudo systemctl enable grantservice-bot
sudo systemctl enable grantservice-admin

echo "Services created successfully!"
echo ""
echo "To start services use:"
echo "  sudo systemctl start grantservice-bot"
echo "  sudo systemctl start grantservice-admin"
echo ""
echo "To check status:"
echo "  sudo systemctl status grantservice-bot"
echo "  sudo systemctl status grantservice-admin"