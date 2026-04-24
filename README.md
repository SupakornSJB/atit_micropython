# ESP32 Firmware — MicroPython

MicroPython firmware for ESP32 that reads physical inputs (buttons, knobs, sensors) and
publishes events to an MQTT broker. Acts as a physical game controller for a Unity-based game.

Part of a three-component system: **ESP32 firmware** → **ASP.NET Core server** → **Unity game**.

## Hardware

- ESP32 (any variant with WiFi)
- Push buttons, potentiometers, or DHT11 sensors wired to GPIO pins
- Pull-up resistor (4.7kΩ) required on DHT11 data pin
- Onboard LED on GPIO 2 blinks on connection errors

## Setup

**1. Install tooling**
```bash
pip install mpremote esptool
```

**2. Flash MicroPython to the ESP32**

Download the latest `.bin` from https://micropython.org/download/esp32/
```bash
esptool.py --chip esp32 erase_flash
esptool.py --chip esp32 write_flash -z 0x1000 esp32-firmware.bin
```

**3. Configure the device**
```bash
cp config.example.py config.py
# Edit config.py with your WiFi credentials, MQTT broker, and input wiring
```

**4. Upload all files**
```bash
mpremote connect COM3 cp config.py :config.py
mpremote connect COM3 cp device.py :device.py
mpremote connect COM3 cp main.py :main.py
mpremote connect COM3 cp mqtt_client.py :mqtt_client.py
mpremote connect COM3 cp wifi_client.py :wifi_client.py
mpremote connect COM3 cp inputs/__init__.py :inputs/__init__.py
mpremote connect COM3 cp inputs/base.py :inputs/base.py
mpremote connect COM3 cp inputs/button_input.py :inputs/button_input.py
mpremote connect COM3 cp inputs/knob_input.py :inputs/knob_input.py
mpremote connect COM3 cp inputs/sensor_input.py :inputs/sensor_input.py
mpremote connect COM3 cp inputs/dht11_input.py :inputs/dht11_input.py
```

Replace `COM3` with your actual port (`python -m serial.tools.list_ports` to find it).

**5. Monitor serial output**
```bash
mpremote connect COM3 repl
```

## Project Structure

```
├── main.py                  # Entry point — builds IoTDevice from config, calls device.run()
├── device.py                # IoTDevice — polling loop, publish logic, exponential backoff
├── wifi_client.py           # WiFi connect/reconnect
├── mqtt_client.py           # MQTT connect, publish, reconnect
├── config.py                # Your credentials and input wiring (not committed)
├── config.example.py        # Template — copy to config.py and fill in values
└── inputs/
    ├── base.py              # Abstract Input base class
    ├── button_input.py      # Digital GPIO with debounce
    ├── knob_input.py        # ADC potentiometer with dead zone filtering
    ├── sensor_input.py      # Generic analog base — subclass and override read_raw()
    └── dht11_input.py       # DHT11 temperature + humidity (publishes two slots)
```

## MQTT Topics

```
game/devices/{deviceId}/slot/{slotId}
```

Server wildcard subscription: `game/devices/+/slot/+`

### Payload
```json
{
  "deviceId": "esp32-01",
  "slotId": "btn1",
  "inputType": "button",
  "event": "pressed",
  "value": 1.0,
  "timestamp": 1234567890,
  "sequenceNumber": 42
}
```

## Adding Inputs

Edit `INPUTS` in `config.py` — each entry maps to one physical slot:
```python
INPUTS = [
    {"slotId": "btn1",  "type": "button", "pin": 18, "debounce_ms": 50},
    {"slotId": "btn2",  "type": "button", "pin": 16, "debounce_ms": 50},
    {"slotId": "knob1", "type": "knob",   "pin": 34, "dead_zone": 0.02},
    {"slotId": "dht1",  "type": "dht11",  "pin": 19},
]
```

`slotId` is a physical identifier only. Semantic names and player assignment live in the ASP.NET server registry.

## Multi-Device Setup

Each physical ESP32 gets its own `config.py` with a unique `DEVICE_ID`. All other files are identical across devices.