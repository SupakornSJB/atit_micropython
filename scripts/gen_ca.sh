#!/bin/bash
# Generates root CA key and self-signed certificate
# Output: certs/ca.key (KEEP SECRET), certs/ca.crt (safe to distribute)

set -e
mkdir -p certs

MSYS_NO_PATHCONV=1 openssl genrsa -out certs/ca.key 4096

MSYS_NO_PATHCONV=1 openssl req -new -x509 -days 3650 \
  -key certs/ca.key \
  -out certs/ca.crt \
  -subj "/C=TH/O=ATITFinalProject/CN=ATITFinalProject-CA"

echo "CA generated: certs/ca.crt"
echo "KEEP certs/ca.key SECRET — never commit or share"