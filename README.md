# ESP32 Button Firmware (MicroPython)

Physical game controller firmware — reads a button and publishes MQTT events to HiveMQ Cloud.

## Setup

### 1. Configure credentials

Edit `config.py` with your actual values:

```python
WIFI_SSID     = "your-ssid"
WIFI_PASSWORD = "your-password"

MQTT_HOST     = "xxxx.hivemq.cloud"
MQTT_USER     = "your-user"
MQTT_PASSWORD = "your-password"

DEVICE_ID = "esp32-01"   # unique per physical device
```

### 2. Install tooling

```bash
pip install mpremote esptool
```

### 3. Flash MicroPython to the ESP32

Download the latest MicroPython `.bin` for ESP32 from https://micropython.org/download/esp32/

```bash
esptool.py --chip esp32 erase_flash
esptool.py --chip esp32 write_flash -z 0x1000 esp32-firmware.bin
```

### 4. Upload firmware files

```bash
mpremote connect /dev/ttyUSB0 cp config.py :config.py
mpremote connect /dev/ttyUSB0 cp wifi_client.py :wifi_client.py
mpremote connect /dev/ttyUSB0 cp button.py :button.py
mpremote connect /dev/ttyUSB0 cp mqtt_client.py :mqtt_client.py
mpremote connect /dev/ttyUSB0 cp main.py :main.py
```

> On Windows, replace `/dev/ttyUSB0` with the appropriate COM port (e.g. `COM3`).

### 5. Monitor serial output

```bash
mpremote connect /dev/ttyUSB0 repl
```

## Hardware

- Button wired between **GPIO 14** and **GND** (internal pull-up enabled)
- Onboard LED on **GPIO 2** blinks rapidly on connection errors