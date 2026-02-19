# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import uasyncio as asyncio
import gc

from pitnode.web.websocket import handle_websocket
from pitnode.log.log import error, info
from config import SERVER_START_TIMEOUT


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
                80
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

async def http_handler(reader, writer, presenter):
    request = await reader.readline()
    if not request:
        writer.close()
        await writer.wait_closed()
        return
    try:
        method, path, _ = request.decode().split(" ")
    except Exception:
        error("Webserver client error:")
        writer.close()
        await writer.wait_closed()
        return

    # ---- Header lesen → dict ----
    headers = {}
    while True:
        line = await reader.readline()
        if line == b"\r\n":
            break
        key, value = line.decode().split(":", 1)
        headers[key.lower()] = value.strip()

    # ---- WebSocket Upgrade ----
    if path == "/ws" and headers.get("upgrade") == "websocket":
        await handle_websocket(reader, writer, headers, presenter)
        return

    # ---- static files (CSS) ----
    if path.endswith(".css"):
        await send_file(
            writer,
            "/pitnode/web" + path,
            "text/css"
        )
        writer.close()
        await writer.wait_closed()
        return
    
    # ---- static files (png) ----
    if path.endswith(".png"):
        await send_file(
            writer,
            "/pitnode/web" + path,
            "image/png"
        )
        writer.close()
        await writer.wait_closed()
        return
    
    # ---- static files (app.js) ----
    if path.endswith("/app.js"):
        await send_file(
            writer,
            "/pitnode/web" + path,
            "application/javascript"
        )
        writer.close()
        await writer.wait_closed()
        return
    
    # ---- HTTP requests ----
    if path == "/":
        await send_file(
            writer,
            "/pitnode/web/index.html",
            "text/html"
        )
        writer.close()
        await writer.wait_closed()
        return

    # ---- Fallback ----
    writer.write(b"HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n")
    await writer.drain()
    writer.close()
    await writer.wait_closed()

async def send_file(writer, path, content_type):
    try:
        writer.write(b"HTTP/1.1 200 OK\r\n")
        writer.write(b"Content-Type: ")
        writer.write(content_type.encode())
        writer.write(b"\r\nConnection: close\r\n\r\n")
        await writer.drain()

        with open(path, "rb") as f:
            while True:
                chunk = f.read(512)
                if not chunk:
                    break
                writer.write(chunk)
                await writer.drain()
        gc.collect()
    except OSError:
        writer.write(b"HTTP/1.1 404 Not Found\r\n\r\n")
        await writer.drain()
