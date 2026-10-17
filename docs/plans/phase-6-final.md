# Phase 6 — Mutual TLS Client Certificate Authentication

## Overview

Phase 6 adds **mutual TLS (mTLS) client certificate authentication** to the MQTT connection layer. Prior to this phase, each ESP32 authenticated using a plaintext username and password stored in `config.py`. Anyone with physical access to the device could read the flash and extract valid credentials. Phase 6 eliminates this by replacing credentials with X.509 client certificates issued by a project-owned Certificate Authority (CA).

**Core security upgrade:** The broker now rejects any device that cannot present a certificate signed by the project CA — stolen credentials alone are no longer sufficient to connect.

---

## Problem Being Solved

| Threat | Before Phase 6 | After Phase 6 |
|---|---|---|
| Attacker reads flash → gets MQTT credentials | Possible — credentials are plaintext in `config.py` | Gets cert bytes only — useless without the CA-signed private key |
| Rogue device connects with stolen credentials | Possible | Rejected — cert not signed by trusted CA |
| Man-in-the-middle intercepts MQTT traffic | Already prevented by TLS | Still prevented |
| Tampered firmware with valid cert copied | N/A | Still possible — full protection requires secure boot (eFuse); documented as known limitation |

---

## What Was Implemented

### 1. `iotgame/mqtt.py` — mTLS support added

The `MqttClient` class was updated to accept and use X.509 certificates:

**New constructor parameters:**
- `ca_cert_path` — path to CA certificate on the ESP32 filesystem (used to verify the broker)
- `cert_path` — path to the device's client certificate
- `key_path` — path to the device's private key

**Behaviour:**
- `_load_file(path)` reads cert/key bytes from the ESP32 filesystem at startup; logs load success and file size
- `connect()` builds `ssl_params` dynamically:
  - When `ca_cert` is present: sets `cert_reqs = ussl.CERT_REQUIRED` — the ESP32 verifies the broker certificate
  - When `cert` + `key` are both present: attaches client cert for mutual TLS handshake
  - Falls back cleanly to password auth or anonymous TLS when cert params are `None`
- Detailed diagnostic logging on connect: prints TLS mode, CA status, cert status, and user status
- `mqtt_user` / `mqtt_password` remain accepted but are set to `None` in mTLS mode (broker uses cert CN as identity)

**Key constraint:** `ussl.CERT_REQUIRED` and client cert loading require MicroPython v1.22+ on ESP32 with mbedTLS. Earlier builds may silently skip cert verification.

---

### 2. `iotgame/device.py` — cert parameters threaded through

`IoTDevice.__init__` signature updated:
- `mqtt_user` and `mqtt_password` changed from positional to keyword-only with `None` defaults
- Three new keyword-only parameters added: `ca_cert_path`, `cert_path`, `key_path`
- All cert params forwarded directly to `MqttClient`

This change was backward-compatible with `game/main.py` but would break any callers using positional arguments for `mqtt_user`/`mqtt_password` (none existed beyond `game/main.py`).

---

### 3. `game/main.py` — backward-compatible cert pickup

Uses `getattr(config, "CA_CERT_PATH", None)` for all three cert paths, so old `config.py` files without cert fields continue to work without modification.

---

### 4. `game/config.py` — cert fields added

New configuration block added (commented out by default):

```python
# Certificate paths (flashed onto ESP32 by provision_device.py)
CA_CERT_PATH  = "ca.crt"
CERT_PATH     = "device.crt"
KEY_PATH      = "device.key"

# Set both to None when using cert auth
MQTT_USER     = None
MQTT_PASSWORD = None
```

Current local setup remains on port 1883 with no-auth for Mosquitto development. Switching to mTLS requires uncommenting cert paths, setting `MQTT_PORT = 8883`, and setting credentials to `None`.

---

### 5. `certs/.gitignore` — secret material protection

Ignores: `*.key`, `*.p12`, `*.pfx`  
Allows committing: `ca.crt`, `*/device.crt` (public certificate material only)

The CA private key (`ca.key`) is never committed — it stays on the provisioning machine only.

---

### 6. `scripts/gen_ca.sh` — root CA generation

Generates the project root CA. Run **once per project**.

- Produces a **4096-bit RSA** root CA private key (`certs/ca.key`)
- Produces a self-signed CA certificate valid for **10 years** (`certs/ca.crt`)
- Subject: `/C=TH/O=ATITFinalProject/CN=ATITFinalProject-CA`
- `ca.crt` is safe to distribute and commit; `ca.key` must never leave the provisioning machine

---

### 7. `scripts/gen_device_cert.sh <device-id>` — per-device certificate signing

Run **once per device**. Accepts a device ID as argument.

- Generates a **2048-bit RSA** device private key (smaller than CA for ESP32 performance)
- Generates a CSR with `CN=<device-id>` — CN must match the `DEVICE_ID` in `config.py` and the ASP.NET device registry
- Signs with the project CA (valid **2 years**)
- Cleans up the intermediate CSR file
- Output: `certs/<device-id>/device.crt` and `certs/<device-id>/device.key`

The CN-to-deviceId match is critical: Mosquitto's `use_identity_as_username` maps the cert CN to the MQTT username, which feeds into the ACL pattern `write game/devices/%u/#` to enforce per-device topic isolation.

---

### 8. `scripts/provision_device.py` — automated cert flashing

A Python script that flashes the three cert files onto an ESP32 via `mpremote`.

**Usage:**
```bash
python scripts/provision_device.py <device-id> [--port /dev/ttyUSB0]
```

- Validates that `certs/<device-id>/` exists before attempting any flash operation
- Flashes: `certs/ca.crt` → `:ca.crt`, `device.crt` → `:device.crt`, `device.key` → `:device.key`
- Exits with error on any `mpremote` failure
- Confirms completion and suggests verifying with `mpremote ls`

---

### 9. `tools/rogue_device.py` — security demo tool

A Python script (runs on a laptop, not on ESP32) that simulates three attack scenarios for the security demonstration. Requires `pip install paho-mqtt`.

#### Attack 1: `no-cert`
- Attempts TLS connection to the broker without loading any client certificate
- Expected outcome: **SSL rejected at handshake** — broker enforces `require_certificate true`
- Uses `ssl.create_default_context` with CA cert but no `load_cert_chain()`

#### Attack 2: `flood`
- Connects with a valid-looking rogue device cert (generated separately with `gen_device_cert.sh rogue`)
- Publishes **200 events/second** for 5 seconds to `game/devices/esp32-device-1/slot/fire`
- Expected outcome: **server-side rate limiter quarantines the device** within 5 seconds
- Demonstrates that cert auth alone is insufficient — application-layer rate limiting is also required

#### Attack 3: `spoof-slot`
- Connects with the rogue cert and publishes a single event with `slotId = "inject-admin"` — a slot that does not exist in the device registry
- Expected outcome: **ASP.NET server raises an unknown-slot alert**
- Demonstrates that the server must validate `slotId` against the registry and not blindly forward unknown slot events

---

## Mosquitto Broker Configuration

For mTLS to work end-to-end, the broker requires:

```
listener 8883
require_certificate true
use_identity_as_username true
acl_file /etc/mosquitto/acl.conf
```

ACL pattern:
```
pattern write game/devices/%u/#
user aspnet-server
topic read game/devices/#
```

`use_identity_as_username` maps the certificate CN (= deviceId) to the MQTT username, enabling the ACL pattern to enforce that each device can only publish to its own topic prefix.

---

## Certificate and Key Architecture

```
Project CA (root)
  ├── ca.key            ← NEVER committed; stays on provisioning machine
  ├── ca.crt            ← committed; distributed to broker + all ESP32 devices
  ├── esp32-device-1/
  │   ├── device.crt    ← committed; flashed onto ESP32
  │   └── device.key    ← gitignored; flashed onto ESP32
  ├── esp32-device-2/
  │   └── ...
  └── rogue/
      ├── device.crt    ← used only for demo attacks 2 and 3
      └── device.key
```

Each ESP32 stores three files on its filesystem: `ca.crt`, `device.crt`, `device.key`. The firmware reads them at boot and passes them into the TLS handshake.

---

## Files Changed or Created in Phase 6

| File | Status | Change |
|---|---|---|
| `iotgame/mqtt.py` | Updated | Added `ca_cert_path`, `cert_path`, `key_path` params; full mTLS `ssl_params` construction; diagnostic logging |
| `iotgame/device.py` | Updated | `mqtt_user`/`mqtt_password` made keyword-only; three cert params added and forwarded |
| `game/main.py` | Updated | `getattr(config, ...)` for backward-compatible cert pickup |
| `game/config.py` | Updated | Cert path constants added (commented out); instructions included |
| `certs/.gitignore` | New | Ignores private key material; allows cert files |
| `scripts/gen_ca.sh` | New | Generates root CA (4096-bit RSA, 10 years) |
| `scripts/gen_device_cert.sh` | New | Signs per-device cert (2048-bit RSA, 2 years, CN=deviceId) |
| `scripts/provision_device.py` | New | Flashes 3 cert files onto ESP32 via mpremote |
| `tools/rogue_device.py` | New | Demo tool: 3 attack scenarios (no-cert, flood, spoof-slot) |
| `docs/plans/phase-6-security.md` | New | Full setup guide, threat model, checklist, Mosquitto config |

---

## Setup Order (for Demo or Production)

1. `bash scripts/gen_ca.sh` — generate root CA once
2. `bash scripts/gen_device_cert.sh <device-id>` — for each device + `rogue`
3. Configure Mosquitto: `require_certificate true`, `use_identity_as_username true`, ACL file
4. `python scripts/provision_device.py <device-id>` with ESP32 connected via USB
5. Update `game/config.py`: uncomment cert paths, set `MQTT_PORT = 8883`, set credentials to `None`
6. Flash `main.py` + `config.py` and verify serial log shows `[MQTT] Connected to ... with client cert`
7. Run demo attacks and verify expected outcomes

---

## Known Limitations

- **Firmware tampering:** If an attacker copies both `device.crt` and `device.key` off flash, they can impersonate the device. Full protection requires ESP32 secure boot via eFuse burning — irreversible and out of scope for this phase. The PKI approach significantly raises the bar by requiring access to two separate secret files.
- **MicroPython TLS compatibility:** `ussl.CERT_REQUIRED` and client cert loading require MicroPython v1.22+ with mbedTLS. Earlier builds may silently accept connections without cert verification.
- **No certificate revocation:** There is no CRL or OCSP infrastructure. Revoking a compromised cert requires manually removing it from the broker trust store and regenerating. Acceptable at demo scale.
