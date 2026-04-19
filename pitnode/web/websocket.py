# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import gc

try:
    import uhashlib as hashlib
except ImportError:
    import hashlib

try:
    import ubinascii as binascii
except ImportError:
    import binascii

try:
    import ujson as json
except ImportError:
    import json

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from pitnode.core.presenter import PitNodePresenter

from pitnode.log.log import error, info

# ---- WebSocket RFC-Konstante ----
WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

# Handshake helper
def websocket_accept(key):
    sha1 = hashlib.sha1((key + WS_GUID).encode()).digest()
    return binascii.b2a_base64(sha1).strip().decode()

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

    frame = bytearray()
    frame.append(0x81)  # FIN + Text Frame

    if length < 126:
        frame.append(length)
    elif length < 65536:
        frame.append(126)
        frame.extend(length.to_bytes(2, "big"))
    else:
        frame.append(127)
        frame.extend(length.to_bytes(8, "big"))

    frame.extend(data)

    try:
        writer.write(frame)
    except Exception as e:
        error(f"[WS] send failed: {e}")

# WebSocket Session
async def websocket_session(reader, writer, presenter: "PitNodePresenter"):
    ws = WebSocketClient(writer)
    # Initialize data after connect

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
                data = json.loads(payload)
            except ValueError:
                error(f"[WS] Invalid JSON: {payload!r}")
                continue
            if data.get("cmd") == "set_targets":
                presenter.set_target_temps(data["values"])
            if data.get("cmd") == "set_target":
                presenter.set_target_temp(data["ch"], data["value"])
            if data.get("cmd") == "confirm_alarm":
                info(f"[WS] Received confirm_alarm: {data}")
                presenter.confirm_alarm(data["ch"])
    finally:
        push_task.cancel()
        try:
            await push_task
        except asyncio.CancelledError:
            pass
        writer.close()
        await writer.wait_closed()
        gc.collect()

# HTTP upgrade
async def handle_websocket(reader, writer, headers, presenter: "PitNodePresenter"):
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
    data = json.dumps(obj).encode()
    length = len(data)

    frame = bytearray()
    frame.append(0x81)  # FIN + Text

    if length < 126:
        frame.append(length)
    elif length < 65536:
        frame.append(126)
        frame.extend(length.to_bytes(2, "big"))
    else:
        frame.append(127)
        frame.extend(length.to_bytes(8, "big"))

    frame.extend(data)

    try:
        writer.write(frame)
    except Exception as e:
        error(f"[WS] send failed: {e}")

class WebSocketClient:
    def __init__(self, writer):
        self.writer = writer

    async def send(self, data):
        await ws_send_json(self.writer, {
            "type": "update",
            "data": data
        })

async def ws_push_loop(ws, presenter: "PitNodePresenter"):
    try:
        info("WS: Push loop started.")
        while True:
            # Probes data
            temps = presenter.get_temps()
            targets = presenter.get_targets()
            bbq_temp = presenter.get_tc_temp()
            states = presenter.get_probe_states()
            probe_types = presenter.get_probe_types()
            probe_model = presenter.get_probe_model()
            
            # Alarms
            alarms = presenter.get_alarms()
            
            # Unit
            unit = presenter.get_unit()

            # WiFi
            rssi = presenter.get_rssi()
            ssid = presenter.get_connected_ssid()


            system = {
                "unit": unit,
                "wifi": {
                    "rssi:": rssi,
                    "ssid": ssid
                }
                
            }
            
            channels = {}

            for ch in range(len(temps)):
                channels[str(ch)] = {
                    "temp": temps[ch],
                    "target": targets[ch],
                    "alarm": alarms[ch],
                    "state": states[ch],
                    "probe_name": "",
                    "probe_type": probe_types[ch],
                    "probe_model": probe_model,
                    "cal": False,

                }

            await ws.send({
                "channels": channels,
                "bbq": {
                    "temp": bbq_temp
                },
                "system": system
            })

            await asyncio.sleep(1)

    except (asyncio.CancelledError, OSError):
        info("WS: Push loop stopped.")