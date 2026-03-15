# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de


import asyncio
import gc

from pitnode.core.controller import PitNodeCtrl
from pitnode.core.presenter import PitNodePresenter
from pitnode.wifi.wifi import WiFiWrapper
from pitnode.web.webserver import WebServer
from pitnode.log.log import error, info
from pitnode.core.probe_setup import setup_probes


def mem(tag):
    gc.collect()

    if hasattr(gc, "mem_free"):
        print(tag, gc.mem_free(), gc.mem_alloc())
    else:
        # CPython fallback
        print(tag, "mem stats not available on CPython")

class App:
    def __init__(self, hw=None, cfg=None):
        self._cfg = cfg
        self._status = SystemStatus()
        self._controller = PitNodeCtrl(hw=hw, cfg=cfg)
        self._wifi = WiFiWrapper(
            self._cfg,
            self._status,
            self._controller.hw.wlan(), # type:ignore
            self._controller.hw.wlan_cfg_path, # type:ignore
            self._controller.hw.uid # type:ignore
            ) 
        
        self._wifi_view = WifiView(self._wifi)
        
        self._presenter = PitNodePresenter(
            self._status,
            self._wifi_view,
            self._controller
            )
        
        self._webserver = WebServer(self._presenter)
        
        self._gui_ready = asyncio.Event()

        self._wifi_task = None
        self._mem_task = None
        
        self._presenter.set_reboot_handler(self._request_reboot)
        self._wifi.set_reboot_handler(self._request_reboot)
        self._presenter.set_gui_ready_callback(self._on_gui_ready)
        
        self._presenter.set_wifi_config_handler(self._request_wifi_config)
        self._presenter.set_wifi_abort_handler(lambda: asyncio.create_task(self.exit_wifi_config_mode(aborted=True))
)
        self._wifi_was_connected = False
        self._running = False

    def _request_wifi_config(self):
        asyncio.create_task(self._enter_wifi_config_mode())

    async def _enter_wifi_config_mode(self):
        self._wifi_was_connected = self._wifi._wlan.isconnected()
        info("[APP] Entering WiFi config mode")
        self._status.wifi.config = True
        await self._webserver.stop()
        await self._wifi.disconnect()
        await self._wifi.scan_networks()
        info("[APP] WiFi scan ready")

    async def exit_wifi_config_mode(self, aborted):
        info(f"[APP] exit_wifi_config_mode called, aborted={aborted}, was_connected={self._wifi_was_connected}")
        if aborted and self._wifi_was_connected:
            self._status.wifi.config = False
            info("[APP] WLAN config aborted → restoring WiFi")
            await self._wifi.wifi_init()
            if self._status.wifi.connected:
                await self._webserver.start_webserver()

    def _on_gui_ready(self):
        self._gui_ready.set()

    async def _wait_for_gui_and_start_wifi(self):
        await self._gui_ready.wait()
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        await asyncio.sleep(0.5)
        info("[APP] GUI ready → starting WiFi")
        connected = await self._wifi.wifi_init()
        if connected:
            await self._webserver.start_webserver()
        else:
            info("No WiFi connection established. Webserver will not be started.")

    async def start(self):
        setup_probes(self._controller)
        await self._controller.start_pitnode_ctrl()
        self._wifi_task = asyncio.create_task(
            self._wait_for_gui_and_start_wifi()
        )
        #await self.webserver.start_webserver()
        if self._cfg.DEV_MODE: #type:ignore
            self._mem_task = asyncio.create_task(self._mem_info())

    async def stop(self):
        if self._wifi_task:
            self._wifi_task.cancel()
            try:
                await self._wifi_task
            except asyncio.CancelledError:
                pass

        if self._mem_task:
            self._mem_task.cancel()

        await self._wifi.stop()
        await self._controller.stop_pitnode_ctrl()
        
    def _request_reboot(self):
        self._controller.hw.reboot() #type:ignore
    
    async def _mem_info(self):
        while True:
            mem("Current mem")
            await asyncio.sleep(5)

class WifiView:
    __slots__ = ("_wifi")

    def __init__(self, wifi):
        self._wifi = wifi
        pass

    def get_scan_result(self):
        return self._wifi.networks
    
    def get_rssi(self):
        return self._wifi.rssi()

class WiFiStatus:
    __slots__ = ("connected", "ip", "active", "config")

    def __init__(self):
        self.connected = False
        self.ip = None
        self.active = False
        self.config = False

class SystemStatus:
    __slots__ = ("wifi",)

    def __init__(self):
        self.wifi = WiFiStatus()