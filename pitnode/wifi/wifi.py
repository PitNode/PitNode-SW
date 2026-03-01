# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

#import network
import gc
import asyncio
from config import ENABLE_WIFI
from pitnode.storage.secrets import load_password, load_ssid
from pitnode.log.log import error, info, warn


class WiFiWrapper:
    def __init__(self, system_status, wlan):
        self._lock = asyncio.Lock()
        self._system_status = system_status
        #self._wlan = None
        self._wlan = wlan
        self._networks = []

    @property
    def networks(self):
        return self._networks

    def set_reboot_handler(self, fn):
        self._on_reboot = fn

    def request_reboot(self):
        if self._on_reboot:
            self._on_reboot()

    def rssi(self):
        if self._system_status.wifi.connected:
            return self._wlan.status('rssi') #type:ignore
        else:
            return None

    async def connect_sta(self, ssid, password, timeout=20):
        try:
            async with self._lock:
                # Falls schon verbunden → sauber trennen
                if self._wlan.isconnected():
                    info("[WIFI] Already connected → disconnecting first")
                    self._wlan.disconnect()
                    await asyncio.sleep(0.5)

                # Falls Interface aktiv → komplett resetten
                if self._wlan.active():
                    info("[WIFI] Resetting WLAN interface")
                    self._wlan.active(False)
                    await asyncio.sleep(0.5)

                # Neu aktivieren
                self._wlan.active(True)
                self._system_status.wifi.active = True
                info("[WIFI] Connecting...")
                self._wlan.connect(ssid, password)

        except OSError as e:
            error(f"[WIFI] connect() failed immediately: {e}")
            warn("[WIFI] Performing machine reset due to EPERM")
            await asyncio.sleep(0.2)
            self.request_reboot()
            return False

        # Wait loop
        for _ in range(timeout):
            try:
                if self._wlan.isconnected():
                    self._system_status.wifi.connected = True
                    self._system_status.wifi.ip = self._wlan.ifconfig()[0]
                    info(f"WLAN verbunden: {self._wlan.ifconfig()}")
                    return True

                await asyncio.sleep(1)

            except asyncio.CancelledError:
                warn("[WIFI] Wifi connection aborted")
                raise

        warn("WLAN Verbindung fehlgeschlagen")
        self._system_status.wifi.connected = False
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

        info(f"Verbinde WLAN: {ssid}")
        return await self.connect_sta(ssid, pw)

    async def stop(self):
        async with self._lock:
            if self._wlan.active():
                if self._wlan.isconnected():
                    self._wlan.disconnect()
                self._wlan.active(False)
                self._system_status.wifi.active = False
            self._system_status.wifi.connected = False
            self._system_status.wifi.ip = None

    async def scan_networks(self):
        async with self._lock:

            was_active = self._wlan.active()

            if not was_active:
                self._wlan.active(True)
                self._system_status.wifi.active = True
                await asyncio.sleep(0.2)

            info("[WIFI] Scanning networks...")

            try:
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

            except Exception as e:
                error(f"[WIFI] Scan failed: {e}")
                self._networks = []

            # Falls vorher inactive → wieder deaktivieren
            if not was_active:
                self._wlan.active(False)
                self._system_status.wifi.active = False

    async def disconnect(self):
        async with self._lock:
            if not self._wlan.isconnected():
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

                self._system_status.wifi.connected = False

            except asyncio.CancelledError:
                warn("[WIFI] Disconnect aborted")
                raise
