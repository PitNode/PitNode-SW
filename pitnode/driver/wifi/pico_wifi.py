# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import network

class PicoWiFiDriver:
    def __init__(self):
        self._wlan = network.WLAN(network.STA_IF)

    def active(self, state: bool):
        self._wlan.active(state)

    def connect(self, ssid, password):
        self._wlan.connect(ssid, password)

    def isconnected(self):
        return self._wlan.isconnected()

    def disconnect(self):
        self._wlan.disconnect()

    def scan(self):
        return self._wlan.scan()

    def rssi(self):
        return self._wlan.status("rssi")

    def ifconfig(self):
        return self._wlan.ifconfig()