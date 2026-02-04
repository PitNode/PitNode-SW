# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import ujson
import ubinascii
import uhashlib
import machine

from pitnode.log.log import error, info, warn

FILE_PW = "wifi.json"
FILE_SSID = "ssid.json"

def _device_key():
    uid = machine.unique_id()
    return uhashlib.sha256(uid).digest()

def _xor(data):
    key = _device_key()
    return bytes(a ^ b for a, b in zip(data, key))

def save_password(password):
    with open(FILE_PW, "w") as f:
        ujson.dump({
            "p": ubinascii.b2a_base64(_xor(password.encode())).decode()
        }, f)
    info("Pw saved")

def load_password():
    try:
        with open(FILE_PW) as f:
            blob = ujson.load(f)
        return _xor(ubinascii.a2b_base64(blob["p"])).decode()
    except:
        return None
    
def save_ssid(ssid):
    with open(FILE_SSID, "w") as f:
        ujson.dump({
            "ssid": ssid
        }, f)
    info("SSID saved")

def load_ssid():
    try:
        with open(FILE_SSID) as f:
            ssid = ujson.load(f)
        return ssid["ssid"]
    except:
        return None