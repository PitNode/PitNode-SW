# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import uasyncio as asyncio
import gc

import uhashlib
import ubinascii
import ujson

from pitnode.log.log import error, info

# ---- WebSocket RFC-Konstante ----
WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

# Handshake helper
def websocket_accept(key):
    sha1 = uhashlib.sha1((key + WS_GUID).encode()).digest()
    return ubinascii.b2a_base64(sha1).strip().decode()

# Frame receive (Client -> Server)
# only: text, <125 Bytes, masked (Browser!)
async def ws_recv(reader):
    try:
        hdr = await reader.readexactly(2)
    except (EOFError, OSError):
        raise EOFError
    fin_opcode = hdr[0]
    masked_len = hdr[1]
    opcode = fin_opcode & 0x0F
    length = masked_len & 0x7F
    masked = masked_len & 0x80
    if not masked:
        raise ValueError("Client frames must be masked")
    if length >= 126:
        raise ValueError("Large frames not supported")
    mask = await reader.readexactly(4)
    data = await reader.readexactly(length)
    payload = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
    return opcode, payload

# Frame send (Server -> Client)
async def ws_send(writer, text):
    data = text.encode()
    length = len(data)
    if length >= 126:
        return  # ignore
    frame = bytearray()
    frame.append(0x81)  # FIN + Text
    frame.append(length) # unmasked
    frame.extend(data)
    writer.write(frame)
    await writer.drain()

# WebSocket Session
async def websocket_session(reader, writer, presenter):
    ws = WebSocketClient(writer)
    push_task = asyncio.create_task(ws_push_loop(ws, presenter))
    try:
        while True:
            try:
                opcode, payload = await ws_recv(reader)
            except EOFError:
                info("[WS] Client disconnected (EOF)")
                break
            # CLOSE Frame
            if opcode == 0x8:
                info("[WS] Client sent CLOSE")
                break
            # PING (ignorieren)
            if opcode == 0x9:
                continue
            # Only text
            if opcode != 0x1:
                continue
            try:
                data = ujson.loads(payload)
            except ValueError:
                error(f"[WS] Invalid JSON: {payload!r}")
                continue
            if data.get("cmd") == "set_targets":
                presenter.set_target_temps(data["values"])
    finally:
        push_task.cancel()
        try:
            await push_task
        except asyncio.CancelledError:
            pass
        writer.close()
        await writer.wait_closed()
        gc.collect()

async def ws_push_loop(ws, presenter):
    try:
        while True:
            temps = presenter.get_temps()
            targets = presenter.get_targets()
            alarms = presenter.get_alarms()
            for ch, t in enumerate(temps):
                await ws.update_temp(ch, t)
            for ch, tt in enumerate(targets):
                await ws.update_target(ch, tt)
            for ch, a in enumerate(alarms):
                await ws.set_alarm(ch, a)
            await asyncio.sleep(1)
    except (asyncio.CancelledError, OSError):
        pass

# HTTP upgrade
async def handle_websocket(reader, writer, headers, presenter):
    try:
        key = headers.get("sec-websocket-key")
        if not key:
            await writer.wait_closed()
            return
        accept = websocket_accept(key)
        response = (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {accept}\r\n\r\n"
        )
        writer.write(response.encode())
        await writer.drain()
        await websocket_session(reader, writer, presenter)
    except OSError as e:
        info(f"[WS] Connection closed: {e}")

async def ws_send_json(writer, obj):
    data = ujson.dumps(obj).encode()
    length = len(data)
    if length >= 126:
        return  # ignore
    frame = bytearray()
    frame.append(0x81) # FIN + Text
    frame.append(length)
    frame.extend(data)
    writer.write(frame)
    await writer.drain()

class WebSocketClient:
    def __init__(self, writer):
        self.writer = writer
    async def update_temp(self, ch, temp):
        await ws_send_json(self.writer, {
            "type": "temp",
            "ch": ch,
            "value": temp
        })

    async def update_target(self, ch, target):
        await ws_send_json(self.writer, {
            "type": "target",
            "ch": ch,
            "value": target
        })

    async def set_alarm(self, ch, active):
        await ws_send_json(self.writer, {
            "type": "alarm",
            "ch": ch,
            "value": active
        })
