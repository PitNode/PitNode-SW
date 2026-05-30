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
    await asyncio.sleep(1)
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

    async def send(self, html):
        await ws_send(self.writer, html)

def render_temp(ch, temp):
    if not temp:
        temp=-1
    return f"""
    <strong id="temp-{ch}" hx-swap-oob="outerHTML">{temp:.1f}</strong>
    """

def render_unit(unit):
    return f"""
    <span hx-swap-oob="innerHTML:.unit">{unit}</span>
    """

def render_bbq_temp(temp):
    if not temp:
        temp=-1
    return f"""
    <strong id="bbq-temp" hx-swap-oob="outerHTML">{temp:.1f}</strong>
    """

def render_bbq_type_probe(type):
    return f"""
    <span id="type-bbq-probe" hx-swap-oob="outerHTML" class="badge bg-secondary">{type}</span>
    """

def render_ch_probe(ch, type, model):
    return f"""
    <span id="type-ch-{ch}-probe" hx-swap-oob="outerHTML" class="badge bg-secondary">{type}</span>
    <span id="model-ch-{ch}-probe" hx-swap-oob="outerHTML" class="badge bg-secondary">{model}</span>
    """

def render_target(ch, target):
    return f"""
    <output id="target-{ch}"
            hx-swap-oob="outerHTML">
        {target}
    </output>
    """

def render_alarm_button(ch, alarm):
    if alarm:
        return f"""
        <button
            id="alarm-{ch}"
            class="btn btn-secondary alarm-btn mt-2 w-100 alarm-active"
            data-ch="{ch}"
            hx-swap-oob="outerHTML">
            Confirm alarm
        </button>
        """
    else:
        return f"""
        <button
            id="alarm-{ch}"
            class="btn btn-secondary alarm-btn mt-2 w-100"
            data-ch="{ch}"
            disabled
            hx-swap-oob="outerHTML">
            Confirm alarm
        </button>
        """

async def ws_push_loop(ws, presenter: "PitNodePresenter"):
    try:
        info("WS: Push loop started.")
        # Unit
        unit = presenter.get_unit()
        temps = presenter.get_temps()
        probe_types = presenter.get_probe_types()
        probe_model = presenter.get_probe_model()

        html=""
        for ch in range(len(temps)):
            html += render_unit(
                unit=unit
            )
            html += render_bbq_type_probe(
                type=probe_types[ch]
            )
            html += render_ch_probe(
                ch=ch,
                type=probe_types[ch],
                model=probe_model,
            )
        await ws.send(html)

        while True:
            # Probes data
            temps = presenter.get_temps()
            targets = presenter.get_targets()
            bbq_temp = presenter.get_tc_temp()
            states = presenter.get_probe_states()

            # Alarms
            alarms = presenter.get_alarms()
            
            # WiFi
            rssi = presenter.get_rssi()
            ssid = presenter.get_connected_ssid()

            html=""
            for ch in range(len(temps)):
                html += render_temp(
                    ch=ch,
                    temp=temps[ch]
                )

                html += render_bbq_temp(
                    temp=bbq_temp
                )

                html += render_target(
                    ch=ch,
                    target=targets[ch]
                )

                html += render_alarm_button(
                    ch=ch,
                    alarm=alarms[ch]
                )

            await ws.send(html)

            await asyncio.sleep(1)

    except (asyncio.CancelledError, OSError):
        info("WS: Push loop stopped.")