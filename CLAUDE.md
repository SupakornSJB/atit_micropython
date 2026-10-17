# CLAUDE.md — ESP32 Firmware (MicroPython)

## Session Updates Log

Daily notes on problems encountered and solutions applied are in `docs/logs/`.
Always check the latest file there for context on recent changes before making suggestions.

- [`docs/logs/2026-04-24.md`](docs/logs/2026-04-24.md) — Local Mosquitto setup, WiFi 2.4GHz fix, MQTT config
- [`docs/logs/2026-04-25.md`](docs/logs/2026-04-25.md) — Phase 2 & 2.1 implementation, slotId protocol fix, DHT11 debugging
- [`docs/logs/2026-04-26.md`](docs/logs/2026-04-26.md) — Phase 3, 3.1, 3.2 implementation, DEBUG flag, auxiliary field for DHT11
- [`docs/logs/2026-04-27.md`](docs/logs/2026-04-27.md) — DHT11 slotId fix, ESP32-32U pinout, next steps checklist
- [`docs/logs/2026-05-06.md`](docs/logs/2026-05-06.md) — Phase 6: mutual TLS client cert auth, cert generation scripts, rogue device demo tool

## What This Project Is

This is one of three components in an **IoT-powered physical game controller system**.
A player interacts with the game by pressing a physical button wired to an ESP32
microcontroller instead of using a keyboard or gamepad. Multiple ESP32 devices can be
active simultaneously, each representing a different player.

## Full System Architecture

```
[ESP32 #1]  ──┐
[ESP32 #2]  ──┤  MQTT publish over TLS
[ESP32 #N]  ──┘  topic: game/controllers/{deviceId}/button
                  broker: HiveMQ Cloud
                        │
                        ▼
              [ASP.NET Core Server]          <- sibling project: /server
                - Subscribes to all MQTT button topics (wildcard)
                - Maps deviceId → playerId via device registry
                - Forwards input to Unity over gRPC
                        │
                        │  gRPC (HTTP/2 + Protobuf)
                        ▼
              [Unity Dedicated Server]       <- sibling project: /unity-game-server
                - Embedded gRPC server receives input
                - Feeds input into NGO server-side game logic
                - Replicates game state to clients via NGO
                        │
                        │  Netcode for GameObjects (NGO/UTP)
                        ▼
              [Unity Game Clients]
                - Players view the game on screen
                - Game state is driven by physical button presses
```

## What the Completed Firmware Does

When fully implemented, each ESP32 device:
1. Connects to WiFi on boot and reconnects automatically on drop
2. Connects to HiveMQ Cloud broker over TLS (port 8883)
3. Waits for a physical button press/release on a GPIO pin
4. Debounces the signal in software to eliminate noise
5. Publishes a JSON event to `game/controllers/{deviceId}/button`
6. Recovers gracefully from WiFi or MQTT failures without requiring a manual reboot

The firmware is intentionally minimal — all game logic, player mapping, and routing
lives in the server layer. The ESP32 only knows how to read a button and report it.

## This Component's Responsibilities

| Responsibility | Owner |
|---|---|
| Read physical button GPIO | ✅ This project |
| Debounce button signal | ✅ This project |
| Connect to WiFi | ✅ This project |
| Publish MQTT events | ✅ This project |
| Map deviceId to playerId | ❌ ASP.NET server |
| Game logic | ❌ Unity server |
| Routing to correct game session | ❌ ASP.NET server |

## Project Overview

MicroPython firmware for an ESP32 microcontroller that reads a physical button and publishes
press/release events to an MQTT broker. This acts as a physical game controller for a
Unity-based game.

## Hardware

- **Chip:** ESP32 (any variant with WiFi)
- **Input:** Single push button wired to a GPIO pin (default: GPIO 14)
- **Pull configuration:** Internal pull-up enabled — button connects GPIO to GND when pressed

## Tech Stack

- **Runtime:** MicroPython (latest stable)
- **Protocol:** MQTT over TCP via `umqtt.simple` (built into MicroPython)
- **Broker:** HiveMQ Cloud (TLS, port 8883)
- **Payload format:** JSON

## Project Structure

```
firmware/
├── CLAUDE.md
├── main.py              # Entry point, wires everything together
├── button.py            # GPIO read + software debounce
├── wifi_client.py       # WiFi connect/reconnect logic
├── mqtt_client.py       # MQTT connect, publish, reconnect logic
└── config.py            # All configuration constants (WiFi, MQTT, GPIO)
```

## Configuration (`config.py`)

All environment-specific values live here. Never hardcode credentials in other files.

```python
# WiFi
WIFI_SSID     = "your-ssid"
WIFI_PASSWORD = "your-password"

# Device identity
DEVICE_ID = "esp32-01"   # Unique per physical device

# MQTT Broker (HiveMQ Cloud)
MQTT_HOST     = "xxxx.hivemq.cloud"
MQTT_PORT     = 8883          # TLS
MQTT_USER     = "your-user"
MQTT_PASSWORD = "your-password"
MQTT_CLIENT_ID = DEVICE_ID

# Topics
MQTT_TOPIC_BUTTON = f"game/controllers/{DEVICE_ID}/button"

# Hardware
BUTTON_PIN      = 14
DEBOUNCE_MS     = 50
```

## MQTT Message Format

Publish to topic: `game/controllers/{deviceId}/button`

```json
{
  "deviceId": "esp32-01",
  "event": "pressed",
  "timestamp": 1234567890
}
```

- `event` is either `"pressed"` or `"released"`
- `timestamp` is `utime.time()` (seconds since epoch, or since boot if NTP not synced)
- QoS: **0** (fire and forget — acceptable for light gaming input)

## Implementation Tasks

### Task 1: `config.py`
- All constants as shown above
- No logic, just values

### Task 2: `wifi_client.py`
- Use `network.WLAN(network.STA_IF)`
- Retry connection up to 10 times with 1s delay
- Raise `RuntimeError` if connection fails after retries
- Expose a single `connect()` function

### Task 3: `button.py`
- Class `Button(pin_number, on_press=None, on_release=None)`
- Read GPIO with internal pull-up (`Pin.PULL_UP`)
- Software debounce: ignore state changes within `DEBOUNCE_MS` of last change
- Use `utime.ticks_ms()` and `utime.ticks_diff()` for timing
- Expose a `tick()` method to be called in the main loop (no interrupts — polling is fine)

### Task 4: `mqtt_client.py`
- Wrap `umqtt.simple.MQTTClient`
- Handle TLS connection using `ussl`
- Auto-reconnect on publish failure
- Expose `connect()` and `publish(topic, payload_dict)` — serializes dict to JSON internally

### Task 5: `main.py`
- Call `wifi_client.connect()`
- Call `mqtt_client.connect()`
- Instantiate `Button` with callbacks that call `mqtt_client.publish()`
- Main loop: call `button.tick()` every 10ms, handle any exceptions with reconnect logic

## Error Handling

- WiFi drop: reconnect before next publish attempt
- MQTT disconnect: reconnect and re-publish in `mqtt_client.publish()`
- If reconnect fails, blink onboard LED rapidly and retry after 5s

## Flashing & Testing

```bash
# Install MicroPython tooling
pip install mpremote esptool

# Flash MicroPython firmware to ESP32
esptool.py --chip esp32 erase_flash
esptool.py --chip esp32 write_flash -z 0x1000 esp32-firmware.bin

# Upload project files
mpremote connect /dev/ttyUSB0 cp config.py :config.py
mpremote connect /dev/ttyUSB0 cp wifi_client.py :wifi_client.py
mpremote connect /dev/ttyUSB0 cp button.py :button.py
mpremote connect /dev/ttyUSB0 cp mqtt_client.py :mqtt_client.py
mpremote connect /dev/ttyUSB0 cp main.py :main.py

# Monitor serial output
mpremote connect /dev/ttyUSB0 repl
```

## Constraints & Notes

- MicroPython has no threading — use a polling loop, not async or interrupts
- `umqtt.simple` does not support QoS 2; use QoS 0 or 1 only
- TLS on ESP32 with MicroPython requires `ussl` — ensure firmware includes it
- Keep JSON payload small; ESP32 RAM is limited (~200KB usable heap)
- Do not use f-strings in hot paths; prefer `%` formatting for performance

---

# Phase 2 — Multi-Input, Multi-Device, Multi-Player

## What Changed in Phase 2

Phase 1 assumed one ESP32 = one button = one player. Phase 2 expands this in three directions:

- **One device can have multiple inputs** of different types (buttons, knobs, sensors)
- **One player can own multiple devices** — e.g. one ESP32 in each hand
- **One device can serve multiple players** — different inputs on the same ESP32 are
  routed to different players by the ASP.NET server (see server CLAUDE.md for details)
  The firmware remains intentionally dumb. It does not know about players, sessions, or
  game logic. It only knows its own `deviceId`, its configured inputs, and the MQTT broker.
  All player resolution happens server-side.

---

## Architectural Decision: Firmware Responsibility Boundary

A key design decision made in Phase 2: **the firmware never knows which player an input
belongs to.** Even when one ESP32 serves two players (e.g. two buttons, each for a
different player), the firmware just publishes `{ deviceId, inputName, ... }`. The
ASP.NET server holds the registry that maps `(deviceId, inputName) → playerId`.

This keeps firmware updates decoupled from player/session changes — reassigning which
button belongs to which player is a server config change, not a firmware reflash.
 
---

## Phase 2 Input Type Support

| Type | Hardware | Value | Events |
|---|---|---|---|
| `button` | Digital GPIO | `1.0` pressed / `0.0` released | `pressed`, `released` |
| `knob` | Potentiometer via ADC | `0.0–1.0` normalized | `change` |
| `sensor` | Generic analog (IMU, distance, etc.) | `float` raw or normalized | `change` |

All three use the same wire format — they differ only in how they read hardware and
when they emit events. The `inputType` field in the payload is metadata for the
receiver, not a different message shape.
 
---

## Phase 2 MQTT Topic Schema (Breaking Change from Phase 1)

**Phase 1 (deprecated):**
```
game/controllers/{deviceId}/button
```

**Phase 2:**
```
game/devices/{deviceId}/input/{inputName}
```

Changes:
- `controllers` → `devices` — not button-specific
- `/button` → `/input/{inputName}` — input name is in the topic, enabling broker-side
  filtering per input type in future
- The wildcard subscription on the server side is: `game/devices/+/input/+`
---

## Phase 2 MQTT Payload Format (Breaking Change from Phase 1)

```json
{
  "deviceId": "esp32-living-room",
  "inputName": "speed",
  "inputType": "knob",
  "event": "change",
  "value": 0.73,
  "timestamp": 1234567890,
  "sequenceNumber": 4821
}
```

**New fields vs Phase 1:**
- `inputName` — developer-defined string, matches the name registered in ASP.NET config
- `inputType` — `"button"` / `"knob"` / `"sensor"`
- `value` — always explicit float; `1.0`/`0.0` for buttons, `0.0–1.0` for knobs/sensors
- `sequenceNumber` — per-device monotonic counter; lets the server detect dropped or
  out-of-order messages without needing QoS 2. Increment once per published event,
  reset to 0 on device reboot.
---

## Phase 2 Project Structure

```
firmware/
├── CLAUDE.md
├── main.py                  # Entry point — configure inputs, call device.run()
├── wifi_client.py           # Unchanged from Phase 1
├── mqtt_client.py           # Updated: new topic schema, new payload fields
├── config.py                # Updated: inputs list replaces single BUTTON_PIN
├── inputs/
│   ├── __init__.py
│   ├── base.py              # Abstract Input base class
│   ├── button_input.py      # Digital GPIO with debounce
│   ├── knob_input.py        # ADC read with dead zone filtering
│   └── sensor_input.py      # Generic analog — subclass for specific sensors
└── device.py                # IoTDevice — owns inputs list, polling loop, publish logic
```
 
---

## Phase 2 Configuration (`config.py`)

```python
# WiFi
WIFI_SSID     = "your-ssid"
WIFI_PASSWORD = "your-password"
 
# Device identity
DEVICE_ID = "esp32-living-room"
 
# MQTT Broker
MQTT_HOST      = "xxxx.hivemq.cloud"
MQTT_PORT      = 8883
MQTT_USER      = "your-user"
MQTT_PASSWORD  = "your-password"
MQTT_CLIENT_ID = DEVICE_ID
 
# Topic template — do not change; must match server wildcard subscription
MQTT_TOPIC_TEMPLATE = "game/devices/{device_id}/input/{input_name}"
 
# Inputs — list of (inputName, inputType, config dict)
# inputName must match the name registered in the ASP.NET device registry
INPUTS = [
    { "name": "jump",  "type": "button", "pin": 14, "debounce_ms": 50 },
    { "name": "speed", "type": "knob",   "pin": 34, "min_raw": 0, "max_raw": 4095, "dead_zone": 0.02 },
    { "name": "fire",  "type": "button", "pin": 27, "debounce_ms": 50 },
]
```
 
---

## Phase 2 Input Classes

### `inputs/base.py` — Abstract base
```python
class Input:
    def __init__(self, name: str, input_type: str): ...
 
    def tick(self) -> list[dict] | None:
        # Returns list of event dicts if state changed since last tick, else None
        # Each dict: { "inputName", "inputType", "event", "value" }
        raise NotImplementedError
```

### `inputs/button_input.py`
- Extends `Input(name, "button")`
- Constructor: `ButtonInput(name, pin, debounce_ms=50, pull_up=True)`
- `tick()`: returns `[{ event: "pressed", value: 1.0 }]` or `[{ event: "released", value: 0.0 }]`
  only on state change; returns `None` if no change
- Debounce via `utime.ticks_ms()` / `utime.ticks_diff()`
### `inputs/knob_input.py`
- Extends `Input(name, "knob")`
- Constructor: `KnobInput(name, pin, min_raw=0, max_raw=4095, dead_zone=0.02)`
- `tick()`: reads ADC, normalizes to `0.0–1.0`, returns `[{ event: "change", value: x }]`
  only if value changed by more than `dead_zone` since last publish; else `None`
- Use `machine.ADC(pin)` for analog read
- Normalize: `value = (raw - min_raw) / (max_raw - min_raw)`, clamped to `[0.0, 1.0]`
### `inputs/sensor_input.py`
- Extends `Input(name, "sensor")`
- Generic base for analog sensors — subclass and override `read_raw() -> float`
- Default `tick()`: reads raw, emits `change` event if delta > `dead_zone`
- Developers subclass this for IMU, distance sensor, etc.
---

## Phase 2 `device.py`

```python
class IoTDevice:
    def __init__(self, device_id, mqtt_host, mqtt_port, mqtt_user,
                 mqtt_password, wifi_ssid, wifi_password): ...
 
    def add_input(self, input: Input) -> None: ...
 
    def run(self) -> None:
        # Blocking polling loop:
        # 1. Ensure WiFi connected
        # 2. Ensure MQTT connected
        # 3. For each input: call tick()
        # 4. For each returned event: build payload, publish to topic
        # 5. Increment sequenceNumber
        # 6. Sleep 10ms
        # 7. Handle exceptions: reconnect with exponential backoff
```

The `sequenceNumber` is a single device-level counter, shared across all inputs.
It increments once per published event (not per tick).
 
---

## Phase 2 Knob / Analog Constraints

- **Dead zone is mandatory** for knobs — without it a jittery ADC generates hundreds
  of events per second and floods MQTT
- Default dead zone: `0.02` (2% of full range) — adjust per hardware
- The server has an additional rate limiter as a second line of defence (see server CLAUDE.md)
- Do not use `utime.sleep_ms()` longer than 10ms in the polling loop — button responsiveness
  degrades above ~20ms polling interval
---

## Phase 2 Error Handling

Same strategy as Phase 1, extended:
- Per-input errors (e.g. ADC read failure) are caught, logged, and skipped for that tick
  — do not crash the entire loop for one bad sensor read
- WiFi/MQTT failures: exponential backoff (1s → 2s → 4s → ... → 30s max), blink LED
- `sequenceNumber` is NOT reset on reconnect — only on full device reboot — so the
  server can distinguish reconnect from reboot

---
 
# Phase 2.1 — Protocol Fix: Separate Physical Slot Identity from Semantic Input Name
 
## What Changed in Phase 2.1
 
Phase 2 introduced a design flaw: `inputName` was used both as a **physical slot
identifier** (for routing) and a **semantic label** (for game logic). This caused a
collision when two physical slots on the same device meant the same thing to the game
but belonged to different players — e.g. two buttons both named `"jump"` but one for
player-1 and one for player-2.
 
Phase 2.1 fixes this with a clean separation:
 
| Field | Meaning | Lives in |
|---|---|---|
| `slotId` | Physical identifier of the input slot on the hardware | Firmware + MQTT topic |
| `inputName` | Semantic game label (e.g. `"jump"`, `"speed"`) | ASP.NET registry only |
| `playerId` | Which player this slot belongs to | ASP.NET registry only |
 
**The firmware now only knows about physical slots.** It never knows semantic names,
player identities, or game logic. All translation happens in the ASP.NET server registry.
 
---
 
## Architectural Decision: Why `slotId` Not `inputName` in the Firmware
 
Using semantic names like `"jump"` in the firmware created an invisible coupling:
changing what a button *means* in the game required either a firmware reflash (to rename
the slot) or awkward workarounds like `"p1-jump"` that smuggled player identity into the
name. Neither is acceptable.
 
`slotId` is a stable physical identifier — it describes the hardware, not the game.
`btn1`, `btn2`, `knob1` never need to change regardless of what the game does with them.
Semantic meaning and player assignment are pure server config.
 
---
 
## Phase 2.1 MQTT Topic Schema (Breaking Change from Phase 2)
 
**Phase 2 (deprecated):**
```
game/devices/{deviceId}/input/{inputName}
```
 
**Phase 2.1:**
```
game/devices/{deviceId}/slot/{slotId}
```
 
Changes:
- `input/` → `slot/` — reflects that this is a physical hardware slot, not a semantic input
- `{inputName}` → `{slotId}` — physical identifier only (e.g. `btn1`, `knob1`, `gpio14`)
- Server wildcard subscription: `game/devices/+/slot/+`
The topic hierarchy now reads unambiguously:
```
game/              ← application namespace
  devices/         ← device layer
    {deviceId}/    ← which physical device
      slot/        ← physical slot layer
        {slotId}   ← which slot on that device
```
 
---
 
## Phase 2.1 MQTT Payload Format (Breaking Change from Phase 2)
 
**Phase 2 (deprecated):**
```json
{
  "deviceId": "esp32-shared",
  "inputName": "speed",
  "inputType": "knob",
  ...
}
```
 
**Phase 2.1:**
```json
{
  "deviceId": "esp32-shared",
  "slotId": "knob1",
  "inputType": "knob",
  "event": "change",
  "value": 0.73,
  "timestamp": 1234567890,
  "sequenceNumber": 4821
}
```
 
- `inputName` removed from payload entirely — it is not the firmware's concern
- `slotId` replaces it — purely physical identifier matching the topic segment
- All other fields unchanged
---
 
## Phase 2.1 Configuration (`config.py`) Update
 
Slots are now named as physical identifiers. The registry on the server assigns
semantic meaning and player ownership — the firmware config has no knowledge of either.
 
```python
INPUTS = [
    { "slotId": "btn1",  "type": "button", "pin": 14, "debounce_ms": 50 },
    { "slotId": "btn2",  "type": "button", "pin": 27, "debounce_ms": 50 },
    { "slotId": "knob1", "type": "knob",   "pin": 34, "min_raw": 0, "max_raw": 4095, "dead_zone": 0.02 },
]
```
 
Previously `"name"` in config carried semantic meaning (e.g. `"jump"`). It is now
`"slotId"` and carries only physical identity. The firmware publishes whatever `slotId`
is configured — no validation against game semantics.
 
---
 
## Phase 2.1 Input Class Updates
 
The `Input` base class and all subclasses replace `name` with `slotId`:
 
```python
class Input:
    def __init__(self, slot_id: str, input_type: str): ...
    # tick() return dicts now use "slotId" key instead of "inputName"
    # { "slotId": "btn1", "inputType": "button", "event": "pressed", "value": 1.0 }
```
 
`IoTDevice.run()` builds the MQTT topic as:
```python
topic = "game/devices/%s/slot/%s" % (self.device_id, event["slotId"])
```

# Phase 3 — Space Shooter: New Input Types & Stage Controller
 
## What Changed in Phase 3
 
Phase 3 adds three new hardware input types to support the space shooter game and
the stage controller role. All existing input types (`ButtonInput`, `KnobInput`)
are unchanged. The MQTT topic schema, payload format, and device registry protocol
are all unchanged from Phase 2.1.
 
---
 
## Phase 3 Player & Device Map
 
The full game has six ESP32 devices across five roles:
 
| Player | Role | Device | Slots |
|---|---|---|---|
| Player 1 | Ship | ESP32 + thumbstick + button | `joystick-x`, `joystick-y`, `stick-click`, `fire` |
| Player 2 | Ship | ESP32 + thumbstick + button | `joystick-x`, `joystick-y`, `stick-click`, `fire` |
| Player 3 | Boss bird | ESP32 + button | `flap` |
| Player 4 | Boss bird | ESP32 + button | `flap` |
| Stage player | Environment + stage | ESP32 + DHT11 + ultrasonic + button | `temp`, `distance`, `pipe-flip` |
 
The stage player device combines all environmental and stage inputs on one ESP32.
No `playerId` is associated with the stage player device — `inputRole` is `"environment"`
and `"stage"` in the registry.
 
---
 
## New Input Type 1: Thumbstick (Analog Joystick Module)
 
The thumbstick module has 5 pins: VCC, GND, VRX (X axis ADC), VRY (Y axis ADC),
SW (click button GPIO). It is three `slotId` entries in config:
 
```python
{ "slotId": "joystick-x",  "type": "knob",   "pin": 34, "min_raw": 0, "max_raw": 4095, "dead_zone": 0.04 },
{ "slotId": "joystick-y",  "type": "knob",   "pin": 35, "min_raw": 0, "max_raw": 4095, "dead_zone": 0.04 },
{ "slotId": "stick-click", "type": "button", "pin": 32, "debounce_ms": 50 },
```
 
Use a slightly larger dead zone (`0.04`) for joystick axes than for standalone knobs —
thumbstick potentiometers have more mechanical jitter at center position. Center
resting position reads approximately `2048` raw (0.5 normalized) — Unity maps
`0.5 → 0 velocity`, `0.0 → full left/down`, `1.0 → full right/up`.
 
`KnobInput` handles VRX and VRY with no code changes. `ButtonInput` handles SW
with no code changes. No new class needed.
 
---
 
## New Input Type 2: DHT11 Temperature Sensor
 
DHT11 uses a single-wire protocol — one data pin, no ADC. Requires a MicroPython
DHT library (`import dht`, available in MicroPython standard library).
 
**Only temperature is used in Phase 3.** Humidity is read but discarded.
 
### `inputs/dht11_input.py`
 
```python
import dht
import machine
from inputs.base import Input
 
class Dht11Input(Input):
    def __init__(self, slot_id: str, pin: int, read_interval_ms: int = 2000):
        super().__init__(slot_id, "sensor")
        self._sensor = dht.DHT11(machine.Pin(pin))
        self._read_interval_ms = read_interval_ms
        self._last_read_ms = 0
        self._last_temp = None
 
    def tick(self) -> list[dict] | None:
        now = utime.ticks_ms()
        if utime.ticks_diff(now, self._last_read_ms) < self._read_interval_ms:
            return None
        self._last_read_ms = now
        try:
            self._sensor.measure()
            temp = self._sensor.temperature()  # Celsius float
            if temp == self._last_temp:
                return None
            self._last_temp = temp
            return [{ "event": "change", "value": float(temp) }]
        except Exception as e:
            print("[DHT11] read error:", e)
            return None
```
 
**Key constraints:**
- DHT11 minimum read interval is 1 second — enforce `read_interval_ms >= 1000`
- Value is raw Celsius (e.g. `28.0`) — NOT normalized to 0.0–1.0. Temperature is an
  absolute physical value; normalization would lose meaning. Unity interprets raw Celsius.
- Do not normalize — the ASP.NET server passes temperature through as-is to Unity
- Read errors are caught and skipped silently — DHT11 occasionally fails on first read
### Config entry
 
```python
{ "slotId": "dht11", "type": "dht11", "pin": 4, "read_interval_ms": 2000 }
```
 
---
 
## New Input Type 3: Ultrasonic Range Sensor (HC-SR04)
 
HC-SR04 uses two GPIO pins: TRIG (output pulse) and ECHO (input pulse width).
Distance is calculated from echo pulse duration.
 
### `inputs/ultrasonic_input.py`
 
```python
import machine
import utime
from inputs.base import Input
 
class UltrasonicInput(Input):
    def __init__(self, slot_id: str, trig_pin: int, echo_pin: int,
                 min_cm: float = 2.0, max_cm: float = 200.0,
                 dead_zone_cm: float = 2.0, read_interval_ms: int = 100):
        super().__init__(slot_id, "sensor")
        self._trig = machine.Pin(trig_pin, machine.Pin.OUT)
        self._echo = machine.Pin(echo_pin, machine.Pin.IN)
        self._min_cm = min_cm
        self._max_cm = max_cm
        self._dead_zone_cm = dead_zone_cm
        self._read_interval_ms = read_interval_ms
        self._last_read_ms = 0
        self._last_distance = None
 
    def _measure_cm(self) -> float | None:
        self._trig.value(0)
        utime.sleep_us(2)
        self._trig.value(1)
        utime.sleep_us(10)
        self._trig.value(0)
        start = utime.ticks_us()
        timeout = utime.ticks_add(start, 30000)
        while self._echo.value() == 0:
            if utime.ticks_diff(utime.ticks_us(), timeout) > 0:
                return None
        pulse_start = utime.ticks_us()
        while self._echo.value() == 1:
            if utime.ticks_diff(utime.ticks_us(), timeout) > 0:
                return None
        pulse_end = utime.ticks_us()
        duration_us = utime.ticks_diff(pulse_end, pulse_start)
        return (duration_us * 0.0343) / 2.0
 
    def tick(self) -> list[dict] | None:
        now = utime.ticks_ms()
        if utime.ticks_diff(now, self._last_read_ms) < self._read_interval_ms:
            return None
        self._last_read_ms = now
        cm = self._measure_cm()
        if cm is None:
            return None
        cm = max(self._min_cm, min(self._max_cm, cm))
        if (self._last_distance is not None and
                abs(cm - self._last_distance) < self._dead_zone_cm):
            return None
        self._last_distance = cm
        return [{ "event": "change", "value": cm }]
```
 
**Key constraints:**
- Value is raw centimetres (e.g. `34.5`) — NOT normalized. Zone computation happens
  server-side, not in firmware. Unity never sees raw distance — only resolved zone ID.
- Dead zone of 2cm prevents jitter from noisy readings
- 30ms timeout on echo pulse prevents infinite loop if sensor is obstructed
- Read interval 100ms (10Hz) — sufficient for zone detection, not too noisy
### Config entry
 
```python
{ "slotId": "distance", "type": "ultrasonic", "trig_pin": 5, "echo_pin": 18,
  "min_cm": 2.0, "max_cm": 200.0, "dead_zone_cm": 2.0, "read_interval_ms": 100 }
```
 
---
 
## Phase 3 Stage Device Config (`config.py`)
 
```python
DEVICE_ID = "esp32-stage"
 
INPUTS = [
    { "slotId": "dht11",     "type": "dht11",      "pin": 4,
      "read_interval_ms": 2000 },
    { "slotId": "distance",  "type": "ultrasonic",  "trig_pin": 5, "echo_pin": 18,
      "min_cm": 2.0, "max_cm": 200.0, "dead_zone_cm": 2.0, "read_interval_ms": 100 },
    { "slotId": "pipe-flip", "type": "button",      "pin": 14, "debounce_ms": 50 },
]
```
 
---
 
## Phase 3 `device.py` Update
 
Add `Dht11Input` and `UltrasonicInput` to the factory in `IoTDevice.add_input()`:
 
```python
def _build_input(self, cfg: dict) -> Input:
    t = cfg["type"]
    if t == "button":     return ButtonInput(...)
    if t == "knob":       return KnobInput(...)
    if t == "dht11":      return Dht11Input(...)
    if t == "ultrasonic": return UltrasonicInput(...)
    raise ValueError("Unknown input type: " + t)
```
 
No other changes to `device.py` — the polling loop handles all input types uniformly.
 
---
 
# Phase 3.1 — Protocol Fix: Auxiliary Field for Multi-Output Sensors
 
## What Changed in Phase 3.1
 
Phase 3 modelled DHT11 as a single-value sensor, discarding humidity. This was
incorrect — DHT11 produces temperature AND humidity from one physical read on one
data pin. Splitting into two slots misrepresents the hardware. Phase 3.1 fixes this
by adding an optional `auxiliary` map to the MQTT payload.
 
---
 
## Architectural Decision: `auxiliary` Is for Sensor Overflow Only
 
The `auxiliary` field is added to the payload defensively — it costs nothing when
empty and future-proofs any multi-output sensor without protocol changes. However
it has a strict usage rule:
 
> **`auxiliary` is always read-optional.** Receivers must never require it.
> Senders populate it only when a single physical source produces multiple
> simultaneous values from one hardware read. It is not a general-purpose
> parameter bag.
 
---
 
## Phase 3.1 MQTT Payload Update (Additive — No Breaking Change)
 
New optional `auxiliary` field added to all payloads. Ignored when empty.
All existing single-value slots are unaffected — they simply never populate it.
 
```json
{
  "deviceId": "esp32-stage",
  "slotId": "dht11",
  "inputType": "dht11",
  "event": "change",
  "value": 28.5,
  "auxiliary": {
    "humidity": 65.0
  },
  "timestamp": 1234567890,
  "sequenceNumber": 4821
}
```
 
- `value` — primary reading (temperature for DHT11)
- `auxiliary.humidity` — secondary reading from the same physical read
- All other input types: `auxiliary` omitted entirely
---
 
## Phase 3.1 `Dht11Input` Update
 
Publish both temperature and humidity on every read:
 
```python
def tick(self) -> list[dict] | None:
    now = utime.ticks_ms()
    if utime.ticks_diff(now, self._last_read_ms) < self._read_interval_ms:
        return None
    self._last_read_ms = now
    try:
        self._sensor.measure()
        temp     = float(self._sensor.temperature())
        humidity = float(self._sensor.humidity())
        if temp == self._last_temp and humidity == self._last_humidity:
            return None
        self._last_temp     = temp
        self._last_humidity = humidity
        return [{
            "event":     "change",
            "value":     temp,
            "auxiliary": { "humidity": humidity }
        }]
    except Exception as e:
        print("[DHT11] read error:", e)
        return None
```
 
Humidity is now always published alongside temperature. The server decides
what to do with it — the firmware does not filter or discard readings.
 
---
 
## Phase 3.1 Payload Serialization in `mqtt_client.py`
 
`publish()` already serializes the full event dict to JSON. The `auxiliary`
key is included automatically if present — no changes needed to `mqtt_client.py`.
`json.dumps()` handles nested dicts correctly in MicroPython.
 

---
 
# Phase 3.2 — Design Fix: Swap Temperature and Humidity Effects
 
## What Changed in Phase 3.2
 
Phase 3 and 3.1 assigned spawn rate to temperature and left humidity unused.
This was based on an incorrect assumption about DHT11 sensor responsiveness.
In practice:
 
- **Temperature** changes very slowly (10–30 seconds for meaningful shift)
  — unsuitable for a dynamic real-time mechanic like spawn rate
- **Humidity** changes quickly (2–3 seconds from breath or hand proximity)
  — well suited for immediate player-visible effects
Phase 3.2 swaps the effects. No firmware code changes required — the firmware
already publishes both `value` (temperature) and `auxiliary.humidity` (humidity)
since Phase 3.1. This fix is purely a server and Unity concern.
 
## No Firmware Changes
 
The firmware is unaffected. `Dht11Input` already publishes:
```json
{
  "value": 28.5,
  "auxiliary": { "humidity": 65.0 }
}
```
 
Both values flow through the pipeline unchanged. What changes is how the
ASP.NET server and Unity *interpret* them.
 

---
 
# Phase 3.3 — Infrastructure Fix: gRPC Connection Stability
 
## What Changed in Phase 3.3
 
No firmware changes. The gRPC connection stability fix is entirely in the
ASP.NET server. This section is included for completeness — no action required
in this project.
 
 
---
 
---
 
# Phase 4 — Library Foundation
 
## What Changed in Phase 4
 
Phase 4 restructures the firmware into a clear library/game separation.
No protocol changes, no new input types. This is purely a structural refactor
that makes the firmware reusable as a source library for other games.
 
---
 
## Architectural Decision: Source Library, Not Package
 
The firmware is distributed as a **source library** — developers clone the repo
and write their game code in the `game/` folder. The `iotgame/` folder is the
library and should not be modified. This approach keeps the code visible and
explainable without requiring a package distribution mechanism.
 
```
Clone repo → configure game/config.py → run game/main.py
```
 
---
 
## Phase 4 Folder Structure
 
```
iotgame-firmware/
├── iotgame/                      ← LIBRARY — do not modify
│   ├── __init__.py               ← exports IoTDevice + all Input types
│   ├── device.py                 ← IoTDevice class
│   ├── mqtt.py                   ← internal MQTT client
│   ├── wifi.py                   ← internal WiFi client
│   └── inputs/
│       ├── __init__.py           ← exports all input types
│       ├── base.py               ← abstract Input base class
│       ├── button_input.py
│       ├── knob_input.py
│       ├── dht11_input.py
│       └── ultrasonic_input.py
│
└── game/                         ← DEVELOPER CODE — modify freely
    ├── main.py                   ← entry point, wire up device + inputs
    └── config.py                 ← all device configuration
```
 
---
 
## Public Library API (`iotgame/__init__.py`)
 
Everything a developer needs is exported from the top-level package:
 
```python
from iotgame import IoTDevice, ButtonInput, KnobInput, Dht11Input, UltrasonicInput
```
 
Internal modules (`mqtt`, `wifi`) are not exported — developers never import them
directly. All internal implementation details are hidden behind `IoTDevice`.
 
---
 
## Developer Entry Point (`game/main.py`)
 
The only file a developer writes from scratch. Full example:
 
```python
from iotgame import IoTDevice, ButtonInput, KnobInput, Dht11Input, UltrasonicInput
import config
 
device = IoTDevice(
    device_id     = config.DEVICE_ID,
    mqtt_host     = config.MQTT_HOST,
    mqtt_port     = config.MQTT_PORT,
    mqtt_user     = config.MQTT_USER,
    mqtt_password = config.MQTT_PASSWORD,
    wifi_ssid     = config.WIFI_SSID,
    wifi_password = config.WIFI_PASSWORD,
)
 
# Register inputs — slotId must match device registry on ASP.NET server
for cfg in config.INPUTS:
    device.add_input_from_config(cfg)
 
device.run()  # blocking — never returns normally
```
 
---
 
## Developer Configuration (`game/config.py`)
 
All device-specific values in one place:
 
```python
# WiFi
WIFI_SSID     = "your-ssid"
WIFI_PASSWORD = "your-password"
 
# Device identity — must match ASP.NET device registry
DEVICE_ID = "esp32-ship-1"
 
# MQTT broker
MQTT_HOST     = "xxxx.hivemq.cloud"
MQTT_PORT     = 8883
MQTT_USER     = "your-user"
MQTT_PASSWORD = "your-password"
 
# Input slots — slotId must match ASP.NET device registry
INPUTS = [
    { "slotId": "fire",       "type": "button",     "pin": 14, "debounce_ms": 50 },
    { "slotId": "joystick-x", "type": "knob",       "pin": 34, "min_raw": 0, "max_raw": 4095, "dead_zone": 0.04 },
    { "slotId": "joystick-y", "type": "knob",       "pin": 35, "min_raw": 0, "max_raw": 4095, "dead_zone": 0.04 },
    { "slotId": "dht11",      "type": "dht11",      "pin": 4,  "read_interval_ms": 2000 },
    { "slotId": "distance",   "type": "ultrasonic", "trig_pin": 5, "echo_pin": 18 },
]
```
 
---
 
## Known Limitations (Document for Library Users)
 
- MQTT credentials are stored in plaintext in `config.py`. On a shared device,
  anyone with flash access can read them. This is a known limitation of
  MicroPython on ESP32 — no secure enclave is available.
- The library does not support OTA (over-the-air) firmware updates.
- Maximum ~10 registered inputs per device due to MicroPython RAM constraints.