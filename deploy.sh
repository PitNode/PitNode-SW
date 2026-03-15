#!/bin/sh

# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

set -e

PORT=${1:-auto}
MPREMOTE="mpremote connect $PORT"

echo "=== Deploy PitNode ==="
echo "Using port: $PORT"
echo

# ---------- helper ----------
mp_mkdir() {
    $MPREMOTE exec "
import os
path='$1'
parts = path.split('/')
cur = ''
for p in parts:
    if not p:
        continue
    cur = cur + '/' + p if cur else p
    try:
        os.mkdir(cur)
    except OSError:
        pass
"
}

# ---------- root files ----------
echo "--- Copy root files ---"
$MPREMOTE cp main.py :
$MPREMOTE cp touch_setup.py :
$MPREMOTE cp config.txt :
$MPREMOTE cp bg_img.bin :

# ---------- pitnode ----------
echo "--- Create pitnode directories (excluding pycache and tests) ---"
find pitnode \( -name "__pycache__" -o -name "tests" \) -prune -o -type d -print | while read d; do
    mp_mkdir "$d"
done

echo "--- Copy pitnode files (.py and .txt, excluding tests) ---"
find pitnode \( -name "__pycache__" -o -name "tests" \) -prune -o -type f \( -name "*.py" -o -name "*.txt" \) -print | while read f; do
    $MPREMOTE cp "$f" ":$f"
done

# ---------- web assets ----------
find pitnode/web -type d -name "__pycache__" -prune -o -type d -print | while read d; do
    mp_mkdir "$d"
done

echo "--- Copy web assets ---"
find pitnode/web -type d -name "__pycache__" -prune -o -type f \( \
    -name "*.html" -o \
    -name "*.css"  -o \
    -name "*.js"   -o \
    -name "*.json" -o \
    -name "*.png" -o \
    -name "*.ico" \
  \) -print | while read f; do
    $MPREMOTE cp "$f" ":$f"
done

# ---------- GUI / drivers ----------
echo "--- Create GUI directories ---"
find gui drivers -type d -name "__pycache__" -prune -o -type d -print | while read d; do
    mp_mkdir "$d"
done

echo "--- Copy GUI files ---"
find gui drivers -type d -name "__pycache__" -prune -o -type f -name "*.py" -print | while read f; do
    $MPREMOTE cp "$f" ":$f"
done

echo
echo "=== Deploy finished ==="

