#!/bin/bash
# Usage: ./gen_device_cert.sh <device-id>
# Example: ./gen_device_cert.sh esp32-device-1

set -e
DEVICE_ID=$1
if [ -z "$DEVICE_ID" ]; then
  echo "Usage: $0 <device-id>"
  exit 1
fi

OUTDIR="certs/$DEVICE_ID"
mkdir -p "$OUTDIR"

MSYS_NO_PATHCONV=1 openssl genrsa -out "$OUTDIR/device.key" 2048

MSYS_NO_PATHCONV=1 openssl req -new \
  -key "$OUTDIR/device.key" \
  -out "$OUTDIR/device.csr" \
  -subj "/C=TH/O=ATITFinalProject/CN=$DEVICE_ID"

MSYS_NO_PATHCONV=1 openssl x509 -req -days 730 \
  -in "$OUTDIR/device.csr" \
  -CA certs/ca.crt \
  -CAkey certs/ca.key \
  -CAcreateserial \
  -out "$OUTDIR/device.crt"

rm "$OUTDIR/device.csr"

echo "Device cert generated: $OUTDIR/device.crt"
echo "Flash onto device with: python scripts/provision_device.py $DEVICE_ID"