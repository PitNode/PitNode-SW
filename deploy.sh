#!/bin/sh
set -e

PORT=${1:-auto}

echo "=== Deploy PitNode ==="
echo "Using port: $PORT"
echo

MPREMOTE="mpremote connect $PORT"

echo "--- Copy root files ---"
$MPREMOTE cp main.py :
$MPREMOTE cp touch_setup.py :
$MPREMOTE cp config.py :

echo "--- Copy pitnode package ---"
$MPREMOTE cp -r pitnode :

echo "--- Copy UI frameworks ---"
$MPREMOTE cp -r gui :
$MPREMOTE cp -r drivers :

echo
echo "=== Deploy finished ==="
