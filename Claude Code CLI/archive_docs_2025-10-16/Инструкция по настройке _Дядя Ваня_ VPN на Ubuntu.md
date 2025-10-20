<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Инструкция по настройке "Дядя Ваня" VPN на Ubuntu с использованием вашего ssconf:// ключа

## Анализ вашего ключа

Ваш ключ имеет формат `ssconf://vova.loan/vanya/77d0e444-5cbd-489e-9169-4bb0a3006570`. Это специальный формат конфигурации, который используется некоторыми VPN-провайдерами для автоматической настройки клиентов.[^1][^2]

## Способ 1: Использование Outline Client (рекомендуемый)

### Установка Outline Client

**Шаг 1. Скачивание клиента**

```bash
# Создайте директорию для загрузок
mkdir -p ~/vpn-clients
cd ~/vpn-clients

# Скачайте Outline Client для Linux
wget -O Outline-Client.AppImage https://s3.amazonaws.com/outline-releases/client/linux/stable/Outline-Client.AppImage

# Сделайте файл исполняемым
chmod +x Outline-Client.AppImage
```

**Шаг 2. Запуск и настройка**

```bash
# Запустите Outline Client
./Outline-Client.AppImage
```

**Шаг 3. Добавление сервера**

1. В интерфейсе Outline Client нажмите кнопку "**+ Add Server**" или "**Add Access Key**"
2. Вставьте ваш ключ: `ssconf://vova.loan/vanya/77d0e444-5cbd-489e-9169-4bb0a3006570`
3. Нажмите "**Add Server**"
4. Клиент автоматически загрузит конфигурацию и настроит подключение[^3][^4][^5]

## Способ 2: Декодирование ключа и настройка shadowsocks-libev

### Установка shadowsocks-libev

```bash
# Обновите пакеты
sudo apt update

# Установите shadowsocks-libev
sudo apt install shadowsocks-libev

# Остановите и отключите серверный демон (нам нужен только клиент)
sudo systemctl stop shadowsocks-libev
sudo systemctl disable shadowsocks-libev
```


### Декодирование ssconf:// ключа

Ваш ключ `ssconf://` нужно декодировать для получения параметров подключения. Это можно сделать несколькими способами:[^2][^3]

**Способ А: Через веб-декодер**

1. Откройте любой онлайн-декодер Base64
2. Извлеките часть после `ssconf://` и декодируйте её
3. Получите параметры: сервер, порт, пароль, метод шифрования

**Способ Б: Через команду curl**

```bash
# Попробуйте получить конфигурацию напрямую
curl -s "https://vova.loan/vanya/77d0e444-5cbd-489e-9169-4bb0a3006570"
```


### Создание конфигурационного файла

После декодирования создайте файл конфигурации:

```bash
# Создайте конфигурационный файл
sudo nano /etc/shadowsocks-libev/vanya-config.json
```

Пример содержимого файла (замените на ваши параметры):

```json
{
    "server": "ваш_сервер_ip",
    "server_port": 443,
    "local_address": "127.0.0.1",
    "local_port": 1080,
    "password": "ваш_пароль",
    "timeout": 86400,
    "method": "chacha20-ietf-poly1305"
}
```


### Запуск клиента

```bash
# Запустите shadowsocks клиент
ss-local -c /etc/shadowsocks-libev/vanya-config.json -v
```

Для постоянной работы создайте systemd сервис:

```bash
# Создайте сервисный файл
sudo nano /etc/systemd/system/vanya-vpn.service
```

Содержимое файла:

```ini
[Unit]
Description=Dyadya Vanya VPN Client
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/ss-local -c /etc/shadowsocks-libev/vanya-config.json
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Активация сервиса:

```bash
# Обновите конфигурацию systemd
sudo systemctl daemon-reload

# Включите автозапуск
sudo systemctl enable vanya-vpn

# Запустите сервис
sudo systemctl start vanya-vpn

# Проверьте статус
sudo systemctl status vanya-vpn
```


## Способ 3: Использование альтернативных клиентов

### V2Ray/Xray (если поддерживается)

```bash
# Установите xray
wget -O install-release.sh https://github.com/XTLS/Xray-install/raw/main/install-release.sh
sudo bash install-release.sh

# Создайте конфигурационный файл на основе декодированных данных
sudo nano /usr/local/etc/xray/config.json
```


## Настройка браузера

После запуска любого из клиентов настройте браузер для использования SOCKS5 прокси:

**Firefox:**

1. Откройте Settings → General → Network Settings
2. Выберите "Manual proxy configuration"
3. SOCKS Host: `127.0.0.1`, Port: `1080`
4. Выберите SOCKS v5

**Chrome/Chromium:**

```bash
# Запустите браузер с прокси
google-chrome --proxy-server="socks5://127.0.0.1:1080"
```


## Системные настройки прокси

Для системного прокси:

```bash
# Установите переменные окружения
export http_proxy=socks5://127.0.0.1:1080
export https_proxy=socks5://127.0.0.1:1080
export HTTP_PROXY=socks5://127.0.0.1:1080
export HTTPS_PROXY=socks5://127.0.0.1:1080

# Добавьте в ~/.bashrc для постоянного использования
echo 'export http_proxy=socks5://127.0.0.1:1080' >> ~/.bashrc
echo 'export https_proxy=socks5://127.0.0.1:1080' >> ~/.bashrc
```


## Проверка подключения

Проверьте работу VPN:

```bash
# Проверьте ваш внешний IP
curl --proxy socks5://127.0.0.1:1080 http://ifconfig.me

# Или через wget
wget --proxy=on --proxy-server=socks5://127.0.0.1:1080 -qO- http://ifconfig.me
```


## Устранение неполадок

**Если подключение не работает:**

1. **Проверьте статус клиента:**
```bash
sudo systemctl status vanya-vpn
journalctl -u vanya-vpn -f
```

2. **Проверьте сетевые соединения:**
```bash
netstat -tlnp | grep 1080
ss -tlnp | grep 1080
```

3. **Тестируйте подключение к серверу:**
```bash
telnet сервер_ip порт_сервера
```

4. **Проверьте логи:**
```bash
ss-local -c /etc/shadowsocks-libev/vanya-config.json -v
```

**Рекомендации:**

- Используйте Outline Client как самый простой вариант[^5][^6]
- Если есть проблемы с декодированием ключа, обратитесь в поддержку "Дядя Ваня" - они предоставят параметры подключения[^7]
- Сохраните ваш ключ в надежном месте для повторного использования[^4]
- Регулярно проверяйте работоспособность соединения[^8][^9]
<span style="display:none">[^10][^11][^12][^13][^14][^15][^16][^17][^18][^19][^20][^21][^22][^23][^24][^25][^26][^27][^28][^29][^30][^31][^32][^33][^34][^35][^36][^37][^38][^39]</span>

<div align="center">⁂</div>

[^1]: https://otvet.mail.ru/question/242102501

[^2]: https://www.reddit.com/r/outlinevpn/comments/1izsr1e/outline_update_shadowsocksoverwebsockets_enhanced/

[^3]: https://habr.com/ru/articles/843638/

[^4]: https://coin.host/blog/guide-to-setting-up-your-personal-shadowsocks-server-on-a-vps-using-outline

[^5]: https://kifarunix.com/how-to-install-outline-vpn-on-linux-systems/

[^6]: https://github.com/Jigsaw-Code/outline-apps

[^7]: https://vanyavpn.app/router

[^8]: https://losst.pro/nastrojka-shadowsocks

[^9]: https://likevps.net/blog/shadowsocks

[^10]: https://help.ubuntu.ru/wiki/ssh

[^11]: https://selectel.ru/blog/ssh-ubuntu-setup/

[^12]: https://habr.com/ru/articles/802179/

[^13]: https://serverspace.ru/support/help/ssh-config-dlya-servera-bystro-i-bezopasno/

[^14]: https://miran.ru/blog/nastrojka-ssh-dlya-ubuntu

[^15]: https://www.vitaliy.org/post/7243

[^16]: https://corpsoft24.ru/about/blog/podklyuchenie-k-ssh-na-ubuntu/

[^17]: https://gvozdb.ru/linux/shadowsocks

[^18]: https://www.servers.ru/knowledge/vpn-to-gpn/setting-up-ubuntu-built-in-vpn-client

[^19]: https://gist.github.com/JohnyDeath/3f93899dc78f90cc57ae52b41ea29bac

[^20]: https://redos.red-soft.ru/base/redos-7_3/7_3-remote-access/7_3-ssh/7_3-sshd-config/

[^21]: https://timeweb.cloud/tutorials/ubuntu/ustanovka-i-nastrojka-ssh-na-servere

[^22]: https://webhamster.ru/mytetrashare/index/mtb0/1509881463292g8fr0qp

[^23]: https://qa.yodo.im/t/kak-nastroit-shadowsocks-na-ubuntu-24-04/5625

[^24]: https://trueconf.ru/docs/group/ru/command-line-interface/

[^25]: https://github.com/shadowsocks/simple-obfs

[^26]: https://wiki.archlinux.org/title/Shadowsocks

[^27]: https://manpages.ubuntu.com/manpages/jammy/man1/ss-local.1.html

[^28]: https://www.linuxbabe.com/ubuntu/shadowsocks-libev-proxy-server-ubuntu

[^29]: https://docs.rs/shadowrocks/latest/shadowrocks/struct.ParsedServerUrl.html

[^30]: https://arenda-server.cloud/blog/kak-nastroit-ssh-kljuchi-na-ubuntu-24/

[^31]: https://manpages.ubuntu.com/manpages/jammy/man1/ss-redir.1.html

[^32]: https://shadowsocks.org/doc/deploying.html

[^33]: https://www.digitalocean.com/community/tutorials/how-to-set-up-ssh-keys-on-ubuntu-20-04-ru

[^34]: https://www.linode.com/docs/guides/create-a-socks5-proxy-server-with-shadowsocks-on-ubuntu-and-centos7/

[^35]: https://umnoe-gelezo.ru/2023/06/1532/

[^36]: https://upcloud.com/resources/tutorials/install-shadowsocks-libev-socks5-proxy/

[^37]: https://adminvps.ru/blog/nastraivaem-ssh-dostup-s-ispolzovaniem-klyuchej-v-ubuntu-22-04/

[^38]: https://stackoverflow.com/questions/18589281/decode-url-whereas-encoded-string-are-in-double-quotes

[^39]: https://timeweb.cloud/tutorials/ubuntu/nastrojka-klyuchej-ssh-v-ubuntu

