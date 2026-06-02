# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de


import gc
import os

from pitnode.web.websocket import handle_websocket
from pitnode.web.views.channels import render_channels
from pitnode.web import api
from pitnode.log.log import error, info

STATIC_FILES = {
    ".css": "text/css",
    ".png": "image/png",
    ".svg": "image/svg+xml",
    ".js": "application/javascript",
    ".ttf": "font/ttf",
}

WEB_ROOT = "pitnode/web"

# Redirect to index.html in case of /
def build_path(path):
    if path == "/":
        return WEB_ROOT + "/index.html"
    return WEB_ROOT + "/" + path.lstrip("/")

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

    # ---- static files ----
    for ext, mime in STATIC_FILES.items():
        if path.endswith(ext):
            await send_file(
                writer,
                build_path(path),
                mime
            )
            writer.close()
            await writer.wait_closed()
            return
    
    # ---- HTTP requests ----
    if path == "/":
        info("INDEX PAGE REQUEST")
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
    
    # ---- HTTP API requests ----
    if path == "/api/target" and method == "POST":
       await api.handle_target(reader, writer, headers, presenter)
       return
    
    if path == "/api/confirm-alarm" and method == "POST":
       await api.handle_confirm_alarm(reader, writer, headers, presenter)
       return

    # ---- Fallback ----
    writer.write(b"HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n")
    await writer.drain()
    writer.close()
    await writer.wait_closed()

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