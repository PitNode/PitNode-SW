# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import gc
import os

from pitnode.web.websocket import handle_websocket
from pitnode.log.log import error, info

WEB_ROOT = "pitnode/web"

CH_COLORS = [
    "#f8e324",
    "#0b5704",
    "#0813a7",
]

# Redirect to index.html in case of /
def build_path(path):
    if path == "/":
        return WEB_ROOT + "/index.html"
    return WEB_ROOT + "/" + path.lstrip("/")

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

# Handle http requests
async def http_handler(reader, writer, presenter):
    request = await reader.readline()
    if not request:
        writer.close()
        await writer.wait_closed()
        return
    try:
        method, path, _ = request.decode().split(" ")
        path = path.split("?")[0]
    except Exception:
        error("Webserver client error:")
        writer.close()
        await writer.wait_closed()
        return

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
            build_path(path),
            "text/css"
        )
        writer.close()
        await writer.wait_closed()
        return
    
    # ---- static files (png) ----
    if path.endswith(".png"):
        await send_file(
            writer,
            build_path(path),
            "image/png"
        )
        writer.close()
        await writer.wait_closed()
        return
    
    if path.endswith(".svg"):
        await send_file(
            writer,
            build_path(path),
            "image/svg"
        )
        writer.close()
        await writer.wait_closed()
        return
    
    if path.endswith(".js"):
        await send_file(
            writer,
            build_path(path),
            "application/javascript"
        )
        writer.close()
        await writer.wait_closed()
        return
    
    if path.endswith(".ttf"):
        await send_file(
            writer,
            build_path(path),
            "font/ttf"
        )
        writer.close()
        await writer.wait_closed()
        return
    
    # ---- HTTP requests ----
    if path == "/":
        await send_file(
            writer,
            build_path(path),
            "text/html"
        )
        writer.close()
        await writer.wait_closed()
        return
    
    if path == "/channel":
        html = render_channels(presenter)
        await send_content(writer, html)
        writer.close()
        await writer.wait_closed()
        return


    # ---- Fallback ----
    writer.write(b"HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n")
    await writer.drain()
    writer.close()
    await writer.wait_closed()

def render_channels(presenter):
    html = ""
    channels = presenter.get_num_probe_channels()
    unit = presenter.get_unit()

    for ch in range(channels):
        html += render_channel(ch, unit)

    return html

def render_channel(ch, unit):
    if unit == "°C":
        min_val = 0
        max_val = 150
    else:
        min_val = 32
        max_val = 302

    return f"""
    <div class="col-12 col-md-6 col-lg-4">
        <div class="card ch-card h-100 bg-dark bg-gradient text-primary">
            <div class="card-header d-flex align-items-center">
                <span class="ch-circle" style="background-color:{CH_COLORS[ch]};"></span>
                <span class="ch-title text-primary">
                    Channel {ch+1}
                </span>

                <div class="ms-auto">
                    <span id="type-ch-{ch}-probe" class="badge probe-type bg-secondary">
                        --
                    </span>
                    <span id="model-ch-{ch}-probe" class="badge probe-param bg-secondary">
                        --
                    </span>
                </div>
            </div>

            <div class="card-body text-center">
                <p class="display-5 mb-0">
                    <strong id="temp-{ch}">--</strong>
                    <span class="unit fs-6">--</span>
                </p>

                <div class="mt-3">
                    <div class="mb-2">
                        Target:
                        <output id="target-{ch}">--</output>
                        <span class="unit fs-6">--</span>
                    </div>

                    <input
                        id="slider-{ch}"
                        data-ch="{ch}"
                        type="range"
                        min="{min_val}"
                        max="{max_val}"
                        class="form-range ch-slider">

                    <button
                        id="alarm-{ch}"
                        data-ch="{ch}"
                        type="button"
                        class="btn btn-secondary alarm-btn mt-2 w-100"
                        disabled>
                            Confirm alarm
                    </button>
                </div>
            </div>
        </div>
    </div>
    """

async def send_file(writer, path, content_type):
    try:
        size = os.stat(path)[6]
        writer.write(b"HTTP/1.1 200 OK\r\n")
        writer.write(b"Content-Type: ")
        writer.write(content_type.encode())
        writer.write(b"\r\nContent-Length: ")
        writer.write(str(size).encode())
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

async def send_content(writer, content, content_type="text/html"):
    data = content.encode()

    writer.write(b"HTTP/1.1 200 OK\r\n")
    writer.write(b"Content-Type: ")
    writer.write(content_type.encode())
    writer.write(b"\r\nContent-Length: ")
    writer.write(str(len(data)).encode())
    writer.write(b"\r\nConnection: close\r\n\r\n")

    writer.write(data)
    await writer.drain()