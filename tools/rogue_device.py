#!/usr/bin/env python3
"""
Rogue device simulator for Phase 6 security demo.
Demonstrates three attack scenarios:

  python rogue_device.py no-cert        # Attack 1: connect without certificate
  python rogue_device.py flood          # Attack 2: flood valid-looking events
  python rogue_device.py spoof-slot     # Attack 3: publish unknown slotId

Requires: pip install paho-mqtt
"""
import argparse
import json
import ssl
import time
import sys
import paho.mqtt.client as mqtt

BROKER_HOST = "your-broker-host"
BROKER_PORT = 8883
CA_CERT     = "certs/ca.crt"


# ── Attack 1: No certificate ──────────────────────────────────────────────────
def attack_no_cert():
    print("[Attack 1] Attempting connection WITHOUT client certificate...")
    client = mqtt.Client(client_id="rogue-no-cert")
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=CA_CERT)
    client.tls_set_context(ctx)

    def on_connect(c, userdata, flags, rc):
        if rc == 0:
            print("[Attack 1] CONNECTED — broker accepted (unexpected!)")
        else:
            print(f"[Attack 1] REJECTED — broker refused (rc={rc}) ✓")

    client.on_connect = on_connect
    try:
        client.connect(BROKER_HOST, BROKER_PORT, keepalive=5)
        client.loop_start()
        time.sleep(3)
        client.loop_stop()
    except ssl.SSLError as e:
        print(f"[Attack 1] SSL rejected at handshake: {e} ✓")
    except Exception as e:
        print(f"[Attack 1] Connection failed: {e} ✓")


# ── Attack 2: Flood events ────────────────────────────────────────────────────
def attack_flood(cert_path: str, key_path: str):
    print("[Attack 2] Flooding with 200 events/sec using valid-looking device ID...")
    client = mqtt.Client(client_id="rogue-flood")
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=CA_CERT)
    ctx.load_cert_chain(certfile=cert_path, keyfile=key_path)
    client.tls_set_context(ctx)
    client.connect(BROKER_HOST, BROKER_PORT)
    client.loop_start()

    topic = "game/devices/esp32-device-1/slot/fire"
    payload = json.dumps({
        "deviceId": "esp32-device-1", "slotId": "fire",
        "inputType": "button", "event": "pressed",
        "value": 1.0, "timestamp": 0, "sequenceNumber": 0
    })

    sent = 0
    start = time.time()
    while time.time() - start < 5:
        client.publish(topic, payload, qos=0)
        sent += 1
        time.sleep(0.005)

    client.loop_stop()
    print(f"[Attack 2] Sent {sent} events in 5 seconds")
    print("[Attack 2] Check dashboard — device should be quarantined ✓")


# ── Attack 3: Unknown slotId ──────────────────────────────────────────────────
def attack_spoof_slot(cert_path: str, key_path: str):
    print("[Attack 3] Publishing unknown slotId 'inject-admin'...")
    client = mqtt.Client(client_id="rogue-slot")
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=CA_CERT)
    ctx.load_cert_chain(certfile=cert_path, keyfile=key_path)
    client.tls_set_context(ctx)
    client.connect(BROKER_HOST, BROKER_PORT)
    client.loop_start()

    topic = "game/devices/esp32-device-1/slot/inject-admin"
    payload = json.dumps({
        "deviceId": "esp32-device-1", "slotId": "inject-admin",
        "inputType": "button", "event": "pressed",
        "value": 1.0, "timestamp": int(time.time()), "sequenceNumber": 9999
    })
    client.publish(topic, payload, qos=0)
    time.sleep(1)
    client.loop_stop()
    print("[Attack 3] Published. Check dashboard — unknown slot alert should appear ✓")


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("attack",
        choices=["no-cert", "flood", "spoof-slot"],
        help="Which attack to simulate")
    parser.add_argument("--cert", default="certs/rogue/device.crt",
        help="Rogue device cert (for attacks that need one)")
    parser.add_argument("--key", default="certs/rogue/device.key")
    args = parser.parse_args()

    if args.attack == "no-cert":
        attack_no_cert()
    elif args.attack == "flood":
        attack_flood(args.cert, args.key)
    elif args.attack == "spoof-slot":
        attack_spoof_slot(args.cert, args.key)