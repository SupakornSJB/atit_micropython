# ESP32 Firmware — MicroPython

MicroPython firmware that turns an ESP32 into a physical game controller. It reads buttons,
knobs/thumbsticks and sensors, and publishes each change as an MQTT event over **mutual TLS**.
Every board authenticates to the broker with its own client certificate.

Part of [ATITFinalProject](https://github.com/SupakornSJB/ATITFinalProject), an IoT
multiplayer game where ESP32 controllers drive a Unity co-op shooter:

```
ESP32 firmware (this repo) ──MQTT/mTLS──▶ Mosquitto ──▶ ASP.NET relay ──gRPC/mTLS──▶ Unity server ──▶ clients
```

---

## Features

- **Config-driven inputs** — declare slots in `config.py`; no code changes per device
- **Input types** — debounced buttons, ADC knobs/thumbsticks (averaged, dead zone, optional
  center calibration), DHT11 temperature + humidity, HC-SR04 ultrasonic distance
- **Mutual TLS** — CA, device certificate and key flashed onto the board; the certificate CN
  is the device identity the broker's ACL checks
- **Resilient loop** — WiFi + NTP sync, MQTT keep-alive ping every 30 s, exponential reconnect
  backoff (1 s → 30 s) with an error blink on the onboard LED (GPIO 2)
- **Device PKI scripts** — create a CA, sign per-device certificates and flash them over USB

---

## Repository layout

```
├── iotgame/                  # Reusable firmware library (upload to the board as-is)
│   ├── device.py             # IoTDevice — builds inputs from config, polling loop, publish, backoff
│   ├── mqtt.py               # MQTT client; TLS with CA + client cert when cert paths are set
│   ├── wifi.py               # WiFi connect + NTP time sync (needed for certificate validation)
│   ├── debug.py              # DEBUG flag — set it from config.py to log every reading
│   └── inputs/               # ButtonInput, KnobInput, Dht11Input, UltrasonicInput
├── game/
│   ├── main.py               # Entry point — upload as :main.py
│   ├── config.example.py     # ESP32 #1: Player 1 thumbstick + round buttons + sensors
│   └── config_device2.example.py  # ESP32 #2: Player 2 knob + up/down/fire buttons
├── scripts/
│   ├── gen_ca.sh             # Create the project CA (certs/ca.key + certs/ca.crt)
│   ├── gen_device_cert.sh    # Sign a certificate for one device: certs/<id>/device.{crt,key}
│   └── provision_device.py   # Flash ca.crt, device.crt, device.key onto a board
└── certs/                    # Generated certificates — git-ignored
```

---

## Quick start

Full setup — certificates, broker, relay and Unity — is in the
[setup guide](https://github.com/SupakornSJB/ATITFinalProject/blob/main/docs/setup.md).
For the firmware alone:

```bash
pip install mpremote esptool

# 1. Flash MicroPython (https://micropython.org/download/esp32/)
esptool.py --chip esp32 erase_flash
esptool.py --chip esp32 write_flash -z 0x1000 esp32-firmware.bin

# 2. Certificates (once per CA / per device) — run from Git Bash on Windows
bash scripts/gen_ca.sh
bash scripts/gen_device_cert.sh esp32-01
python scripts/provision_device.py esp32-01 --port COM3

# 3. Config — copy an example and fill in WiFi + broker host
cp game/config.example.py game/config.py

# 4. Upload and watch the serial log
mpremote connect COM3 cp -r iotgame :
mpremote connect COM3 cp game/config.py :config.py
mpremote connect COM3 cp game/main.py :main.py
mpremote connect COM3 repl
```

Find the port with `python -m serial.tools.list_ports`. `game/config.py` and other real
configs are git-ignored; only the `*.example.py` files are committed.

---

## Configuring inputs

Each entry in `INPUTS` is one physical **slot**:

```python
INPUTS = [
    {"slotId": "btn-1",      "type": "button", "pin": 14, "debounce_ms": 50, "pull_up": True},
    {"slotId": "joystick-x", "type": "knob",   "pin": 34, "min_raw": 0, "max_raw": 4095,
     "dead_zone": 0.04, "center": 1900, "samples": 8},
    {"slotId": "dht11",      "type": "dht11",  "pin": 4, "read_interval_ms": 2000},
    {"slotId": "distance",   "type": "ultrasonic", "trig_pin": 5, "echo_pin": 18,
     "min_cm": 2.0, "max_cm": 200.0, "dead_zone_cm": 2.0, "read_interval_ms": 100},
]
```

| Type | Emits | Notes |
|---|---|---|
| `button` | `pressed` (1.0) / `released` (0.0) | `pull_up: False` for buttons wired to 3.3 V |
| `knob` | `change`, value normalized to 0.0–1.0 | Only when it moves more than `dead_zone`; `center` maps a thumbstick's rest position to 0.5 |
| `dht11` | `change`, value = °C, `auxiliary.humidity` = % | Needs a 4.7 kΩ pull-up on the data pin |
| `ultrasonic` | `change`, value = distance in cm | The relay turns distance into zones 1–4 |

`slotId` only names the physical slot. What a slot *does* — which player it belongs to, whether
it moves a ship, fires, starts the round or changes the environment — is set in the relay
server's `DeviceRegistry`, so remapping a controller never requires reflashing it.

---

## MQTT protocol

Topic — one per slot; the relay subscribes to `game/devices/+/slot/+`:

```
game/devices/{deviceId}/slot/{slotId}
```

Payload:

```json
{
  "deviceId": "esp32-01",
  "slotId": "dht11",
  "inputType": "dht11",
  "event": "change",
  "value": 27.0,
  "auxiliary": { "humidity": 61.0 },
  "timestamp": 1777777777,
  "sequenceNumber": 42
}
```

`auxiliary` is only present for multi-value sensors. `sequenceNumber` increases with every
event a device publishes; the relay records the latest one per device.

---

## Security

The broker (Mosquitto) is configured with `require_certificate` and
`use_identity_as_username`, and its ACL lets a device publish only under
`game/devices/<its CN>/#`. A board without a certificate signed by the project CA cannot
connect, and a valid board cannot impersonate another device's topics. The
[relay server](https://github.com/SupakornSJB/ATITInfraNode) adds intrusion detection
on top: rate limiting, unknown-slot alerts and quarantine.
