# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

from machine import reset
import asyncio

from pitnode.core.controller import PitNodeCtrl
from pitnode.core.presenter import PitNodePresenter
from pitnode.wifi.wifi import WiFiWrapper
from pitnode.web.webserver import WebServer
import config as cfg
from pitnode.log.log import error, info
import gc


def mem(tag):
    gc.collect()
    print(tag, gc.mem_free(), gc.mem_alloc())

class SystemStatus:
    __slots__ = ("wifi_connected",)

    def __init__(self):
        self.wifi_connected = False

class App:
    def __init__(self):
        self.status = SystemStatus()
        self.controller = PitNodeCtrl
        self.wifi = WiFiWrapper()
        self.presenter = PitNodePresenter(self.status, self.wifi)
        
        self._wifi_task = None
        self._mem_task = None
        
        self.gui_ready = asyncio.Event()
        self.webserver = WebServer(self.presenter)
        self.presenter.set_reboot_handler(self._request_reboot)
        self.presenter.set_gui_ready_callback(self._on_gui_ready)
        self.presenter.set_wifi_config_handler(self._request_wifi_config)
        self.presenter.set_wifi_abort_handler(lambda: asyncio.create_task(self.exit_wifi_config_mode(aborted=True))
)
        self._wifi_was_connected = False

    def _request_wifi_config(self):
        asyncio.create_task(self._enter_wifi_config_mode())

    async def _enter_wifi_config_mode(self):
        info("[APP] Entering WiFi config mode")
        self._wifi_was_connected = self.status.wifi_connected
        await self.webserver.stop()
        await self.wifi.disconnect()
        self._update_status()
        await self.wifi.scan_networks()
        info("[APP] WiFi scan ready")

    async def exit_wifi_config_mode(self, aborted):
        if aborted and self._wifi_was_connected:
            info("[APP] WLAN config aborted → restoring WiFi")
            await self.wifi.wifi_init()
            self._update_status()

            if self.status.wifi_connected:
                await self.webserver.start_webserver()

    def _update_status(self):
        self.status.wifi_connected = self.wifi.connected

    def _on_gui_ready(self):
        self.gui_ready.set()

    async def _wait_for_gui_and_start_wifi(self):
        await self.gui_ready.wait()
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        await asyncio.sleep(0.3)
        info("[APP] GUI ready → starting WiFi")
        connected = await self.wifi.wifi_init()
        self._update_status()
        if connected:
            await self.webserver.start_webserver()
        else:
            info("No WiFi connection established. Webserver will not be started.")

    async def start(self):
        await self.controller.start_pitnode_ctrl()
        self._wifi_task = asyncio.create_task(
            self._wait_for_gui_and_start_wifi()
        )
        #await self.webserver.start_webserver()
        if cfg.DEV_MODE:
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

        await self.wifi.stop()
        await self.controller.stop_pitnode_ctrl()
        self._update_status()
        
    def _request_reboot(self):
        asyncio.create_task(self.reboot())

    async def reboot(self):
        self._running = False
        info("[APP] reboot")
        await asyncio.sleep(0)
        await self.stop()
        reset()
    
    async def _mem_info(self):
        while True:
            mem("Current mem")
            await asyncio.sleep(5)