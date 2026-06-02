# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import gc

from pitnode.web.router import http_handler
from pitnode.log.log import error, info

class WebServer:
    def __init__(self, presenter):
        self.presenter = presenter
        self._server = None

    async def start_webserver(self):
        if self._server:
            return
        try:
            self._server = await asyncio.start_server(
                lambda r, w: http_handler(r, w, self.presenter),
                "0.0.0.0",
                self.presenter.get_cfg().WEB_PORT
            )
            info("[WEB] Webserver gestartet")
        except Exception as e:
            error(f"[WEB] Webserver start failed: {e}")
            self._server = None

    async def stop(self):
        server = self._server
        if not server:
            return
        info("[WEB] Webserver stopping")
        self._server = None
        try:
            server.close()
            await server.wait_closed()
            gc.collect()
            info("[WEB] Webserver stopped")
        except Exception as e:
            error(f"[WEB] Error while stopping webserver: {e}")
