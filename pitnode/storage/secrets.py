# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de


try:
    import ujson as json
except ImportError:
    import json

try:
    import ubinascii as binascii
except ImportError:
    import binascii

try:
    import uhashlib as hashlib
except ImportError:
    import hashlib

#from pitnode.core.controller import PitNodeCtrl as Ctrl
from pitnode.log.log import error, info, warn

def _path(filename, base_path=None):
    if base_path:
        if base_path.endswith("/"):
            return base_path + filename
        return base_path + "/" + filename
    return filename

FILE_PW = "wifi.json"
FILE_SSID = "ssid.json"

def _device_key(uid):
    return hashlib.sha256(uid).digest()

def _xor(data, uid):
    key = _device_key(uid)
    out = bytearray(len(data))
    for i in range(len(data)):
        out[i] = data[i] ^ key[i % len(key)]
    return bytes(out)

def save_password(password, base, uid):
    with open(_path(FILE_PW, base), "w") as f:
        json.dump({
            "p": binascii.b2a_base64(_xor(password.encode(), uid)).decode()
        }, f)
    info("Pw saved")

def load_password(base, uid):
    try:
        with open(_path(FILE_PW, base)) as f:
            blob = json.load(f)
        return _xor(binascii.a2b_base64(blob["p"]), uid).decode()
    except:
        return None
    
def save_ssid(ssid, base):
    with open(_path(FILE_SSID, base), "w") as f:
        json.dump({
            "ssid": ssid
        }, f)
    info("SSID saved")

def load_ssid(base):
    try:
        with open(_path(FILE_SSID, base)) as f:
            ssid = json.load(f)
        return ssid["ssid"]
    except:
        return None