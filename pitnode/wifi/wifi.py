# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import network
import gc
import asyncio
from pitnode.config import ENABLE_WIFI
from pitnode.storage.secrets import load_password, load_ssid
from pitnode.log.log import error, info, warn

class WiFiWrapper:
    def __init__(self):
        self._connected = False
        self._wlan = None
        self._networks = []

    @property
    def connected(self):
        return self._connected
    
    @property
    def networks(self):
        return self._networks

    async def connect_sta(self, ssid, password, timeout=20):
        if not self._wlan:
            self._wlan = network.WLAN(network.STA_IF)
            self._wlan.active(True)
        self._wlan.connect(ssid, password)
        
        for _ in range(timeout):
            try:
                if self._wlan.isconnected():
                    self._connected = True
                    info(f"WLAN verbunden: {self._wlan.ifconfig()}")
                    return True
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                warn("[WIFI] Wifi connection aborted")
                raise

        warn("WLAN Verbindung fehlgeschlagen")
        self._connected = False
        return False

    async def wifi_init(self):
        if not ENABLE_WIFI:
            info("WLAN deaktiviert")
            return False
        ssid = load_ssid()
        pw = load_password()
        if not pw or not ssid:
            info("[WIFI] No password or SSID for WiFi set. Skipping.")
            return False
        
        print("Verbinde WLAN:", ssid)
        return await self.connect_sta(ssid, pw)

    async def stop(self):
        if self._wlan:
            if self._wlan.isconnected():
                self._wlan.disconnect()
            self._wlan.active(False)
            self._wlan = None
        self._connected = False

    async def scan_networks(self):
        if not self._wlan:
            self._wlan = network.WLAN(network.STA_IF)
            self._wlan.active(True)
            await asyncio.sleep(0.2)

        # Scan NICHT während Verbindung
        if self._wlan.isconnected():
            warn("[WIFI] Scan skipped: already connected")
            return self._networks

        info("[WIFI] Scanning networks...")

        try:
            # scan() ist blockierend → kurz aus dem Eventloop raus
            await asyncio.sleep(0)
            result = self._wlan.scan()

            networks = []
            for entry in result:
                ssid = entry[0]
                try:
                    ssid = ssid.decode("utf-8")
                except Exception:
                    ssid = str(ssid)
                if ssid and ssid not in networks:
                    networks.append(ssid)

            self._networks = networks
            gc.collect()
            info(f"[WIFI] Found {len(networks)} networks")
            return networks

        except asyncio.CancelledError:
            warn("[WIFI] Scan aborted")
            raise
        except Exception as e:
            error(f"[WIFI] Scan failed: {e}")
            self._networks = []
            return []

    async def disconnect(self):
        if not self._wlan:
            return

        try:
            if self._wlan.isconnected():
                info("[WIFI] Disconnecting from WLAN")
                self._wlan.disconnect()

                # kurz warten, bis Status sauber ist
                for _ in range(10):
                    if not self._wlan.isconnected():
                        break
                    await asyncio.sleep(0.1)

            self._connected = False

        except asyncio.CancelledError:
            warn("[WIFI] Disconnect aborted")
            raise
