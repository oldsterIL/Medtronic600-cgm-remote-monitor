# RPi + SIM7000e + Contour NextLink 2.4 USB
Первоначальная установка и настройка
## Задача
Настроить передачу данных с помпы Medtronic 640g на мобильный телефон посредством глюкометра Contour NextLink 2.4 USB. Для реализации были выбраны следующие компоненты:
- Raspberry Pi 3 Model B+
- [Waveshare SIM7000E NB-IoT HAT](https://www.waveshare.com/wiki/SIM7000E_NB-IoT_HAT) ссылка на [aliexpress](https://ru.aliexpress.com/item/32883236829.html?spm=a2g0s.9042311.0.0.302d33edCWnpxz)

## Реализация
### Установка OS
За основу была взята [Raspbian Buster Lite](https://downloads.raspberrypi.org/raspbian_lite_latest). Качаем, прошиваем согласно [инструкции](https://www.raspberrypi.org/documentation/installation/installing-images/README.md), загружаемся.
### Настройка OS
После запуска входим в систему, используя логин\пароль:
```bash
pi
raspberry
```
Запускаем настройку Малинки
```bash
sudo raspi-config
```
Выбираем опции:

***1. Change User Password*** и меняем пароль

***2. Network Option*** - меняем имя Hostname (если необходимо), настраиваем Wi-Fi указывая свою сеть и пароль. [Подробнее](https://www.raspberrypi.org/documentation/configuration/wireless/wireless-cli.md)

***4. Localisation Option*** - настраиваем TimeZone

***5. Interfacing Options*** - Выбираем необходимые *SSH* - enable, *I2C* - enable, *Serial* - *Login shell over serial* - DISABLE!, *hardware* - enable
 
***Finish*** - Перезагружаем

После перезагрузки проверяем включения UART
```bash
pi@contur:~ $ grep "enable_uart" /boot/config.txt 
enable_uart=1
```
Если ключа нет, необходимо добавить его в конфиг /boot/config.txt строку:
```
enable_uart=1
```
Отключаем Bluetooth [подробнее о UART](https://www.raspberrypi.org/documentation/configuration/uart.md)
```bash
pi@contur:~ $ sudo nano /boot/config.txt 
Добавим в конец
dtoverlay=pi3-disable-bt
```
***Внимание!*** После этого модем будет доступен по /dev/ttyAMA0

Настраиваем статический адрес на Wi-Fi (если надо)
```bash
pi@contur:~ $ sudo nano /etc/dhcpcd.conf
```
Добавляем в конец строки (адреса меняем на ваши):
```bash
interface wlan0
static ip_address=192.168.36.6/24
static routers=192.168.36.1
static domain_name_servers=192.168.36.1
```
Перезагружаем
```bash
sudo reboot now
```
Теперь можно подключаться через ssh к Малинке
### Обновление
из консоли:
```bash
sudo apt-get update && sudo apt-get dist-upgrade
```
После обновления - перезагружаемся
```bash
sudo reboot now
```
### Настраиваем GPRS на модеме
Информацию о работе с модемом можно найти на [официальном сайте](https://www.waveshare.com/wiki/SIM7000E_NB-IoT_HAT)
Устанавливаем утилиты
```bash
sudo apt-get install minicom ppp mc mtr -y
```
Проверяем работу модему:
```bash
pi@contur:~ $ minicom -D /dev/ttyAMA0
Welcome to minicom 2.7.1

OPTIONS: I18n 
Compiled on Aug 13 2017, 15:25:34.
Port /dev/ttyAMA0, 16:55:14

Press CTRL-A Z for help on special keys

at
OK
AT+COPS?
+COPS: 0,0,"MTS RUS MTS RUS",3

OK
ati
SIM7000E R1351

OK
```
Выход: Ctrl+A + q

Настраиваем соединения через PPP
```bash
sudo cp /etc/ppp/peers/provider /etc/ppp/peers/gprs
sudo nano /etc/ppp/peers/gprs
```
приводим файл к такому виду, я пользуюсь МТС (не реклама):
```bash
# Задаёт имя в качестве имени, используемого локальной системой для аутентификации у партнёра
user "mts"
password "mts"

# modem initialization string.
connect "/usr/sbin/chat -v -f /etc/chatscripts/gprs"

# Serial device to which the modem is connected.
/dev/ttyAMA0

# Speed of the serial line.
115200

# Отключает аппаратное управление потоком (то есть RTS/CTS) на последовательном порту.
# Если не задана ни одна из опций crtscts, nocrtscts, cdtrcts, nocdtrcts, то настройка
# аппаратного управления потоком на последовательном порту останется неизменной.
nocrtscts

# Включает средства отладки соединения
debug

# Не отделяться от правляющего терминала.
# Если указано последовательное устройство отличное от терминала на стандартном
# вводе, но не указана эта опция, то pppd выполнит операцию fork для перехода в фоновый режим
nodetach

# При указании этой опции pppd будет принимать локальный IP-адрес предложенный партнёром,
# даже если IP-адрес был явно указан с помощью опции
ipcp-accept-local

# При указании этой опции pppd будет принимать удалённый IP-адрес предложенный партнёром,
# даже если IP-адрес был явно указан с помощью опции.
ipcp-accept-remote


# Assumes that your IP address is allocated dynamically by the ISP.
# Отключает поведение по умолчанию, при котором локальный IP-адрес (по возможности) определяется
# из имени узла, если он не указан явно. При указании этой опции партнёру придётся предоставить локальный
# IP-адрес во время согласования IPCP (если адрес не указан явно в командной строке или в файле опций)
noipdefault

# Try to get the name server addresses from the ISP.
# Запросить до 2 адресов серверов DNS. Адреса, предоставленные партнёром (если есть) передаются
# сценарию /etc/ppp/ip-up в переменных окружения DNS1 и DNS2, а переменная окружения USEPEERDNS будет установлена в 1.
# pppd также создаст файл /var/run/ppp/resolv.conf, содержащий одну или две строки nameserver с адресами, предоставленными партнёром
usepeerdns

# Use this connection as the default route.
# При удачном завершении согласования IPCP добавить в системные таблицы маршрутизации маршрут по умолчанию через партнёра.
# Эта запись удаляется при разрыве соединения PPP. Эта опция привилегированая, если была указана опция nodefaultroute
defaultroute

# Makes pppd "dial again" when the connection is lost.
# Не завершать работу сразу после разрыва соединения, а попытаться установить его заново. При этом учитывается опция maxfail
persist

# Do not ask the remote to authenticate.
# Не требовать аутентифиции у партнёра. Эта опция привилегированная
noauth
```
Редактируем файл /etc/chatscripts/gprs
```bash
sudo nano /etc/chatscripts/gprs
```
приводим его к такому виду:
```bash
ABORT		BUSY
ABORT		VOICE
ABORT		"NO CARRIER"
ABORT		"NO DIALTONE"
ABORT		"NO DIAL TONE"
ABORT		"NO ANSWER"
ABORT		"DELAYED"
ABORT		"ERROR"

# cease if the modem is not attached to the network yet
ABORT		"+CGATT: 0"

""		AT
TIMEOUT		12
OK		ATH
OK		ATE1

# +CPIN provides the SIM card PIN
#OK		"AT+CPIN=1234"

# +CFUN may allow to configure the handset to limit operations to
# GPRS/EDGE/UMTS/etc to save power, but the arguments are not standard
# except for 1 which means "full functionality".
#OK		AT+CFUN=1

OK		AT+CGDCONT=1,"IP","internet.mts.ru"
OK		ATD*99#
TIMEOUT		22
CONNECT		""
```
Настраиваем службу ppp:
```bash
sudo nano /etc/systemd/system/ppp.service
```
Добавляем:
```bash
[Unit]
Description=PRi UART PPP Link
After=syslog.target
After=network.target

[Service]
Type=simple
ExecStart=/usr/sbin/pppd call gprs
Restart=always

[Install]
WantedBy=multi-user.target
Alias=ppp.service

```
Перечитаем конфиги:
```bash
sudo systemctl daemon-reload
```
### Установим gammu для работы с SMS
```bash
sudo apt-get install gammu gammu-smsd
```
Настроим
```bash
gammu-config
```
Указываем порт (/dev/ttyAMA0), больше ничего не меняем.
Так же, меняем порт (/dev/ttyAMA0) тут:
```bash
sudo nano /etc/gammu-smsdrc
```
SMS храняться тут: /var/spool/gammu/
Отключим автозапуск службы, запускать будем руками.
```bash
sudo systemctl disable gammu-smsd.service
```
### Установим Zabbix-agent
```bash
sudo apt-get install zabbix-agent zabbix-sender
```
Отключим автозапуск
```bash
sudo systemctl disable zabbix-agent.service
sudo systemctl stop zabbix-agent.service
```

### Установим необходимые библиотеки
```bash
sudo apt-get install python-smbus
sudo apt-get install python-pip
sudo apt-get install libudev-dev libusb-1.0-0-dev liblzo2-dev

pip install pyserial
sudo -H pip install --upgrade setuptools --user python
sudo -H pip install cython
sudo -H pip install hidapi
sudo -H pip install requests astm PyCrypto crc16 python-dateutil
sudo -H pip install python-lzo
sudo -H pip install pytz
sudo -H pip install pyTelegramBotAPI
sudo -H pip install requests[socks]
```
### Внесем изменения в настройки системы
Разрешим пользователю "pi" общаться с Contour NextLink 2.4 USB, создадим файл 
```bash
sudo nano /etc/udev/rules.d/30-bayer.rules
```
Добавив в него:
```bash
SUBSYSTEMS=="usb", ATTRS{idVendor}=="1a79", ATTRS{idProduct}=="6210", GROUP="pi", MODE="0664"
```
Перенесем /tmp на RAM диск, добавим строчку (последнюю) в /etc/fstab:
```bash
proc            /proc           proc    defaults          0       0
PARTUUID=83e027df-01  /boot           vfat    defaults          0       2
PARTUUID=83e027df-02  /               ext4    defaults,noatime  0       1
# a swapfile is not a swap partition, no line here
#   use  dphys-swapfile swap[on|off]  for that
tmpfs /tmp tmpfs defaults,noatime,nosuid 0 0
```
Перезагружаемся
```bash
sudo reboot now
```
