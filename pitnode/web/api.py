# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de


from pitnode.log.log import error, info

async def handle_target(reader, writer, headers, presenter):
    try:
        length = int(headers.get("content-length", 0))
        body = await reader.readexactly(length)

        params = {}

        for pair in body.decode().split("&"):
            key, value = pair.split("=", 1)
            params[key] = value

        ch = int(params["ch"])
        target = int(params["value"])

        presenter.set_target_temp(ch, target)

        writer.write(
            b"HTTP/1.1 204 No Content\r\n"
            b"Connection: close\r\n\r\n"
        )
        await writer.drain()

    except Exception as e:
        error(f"[API] target failed: {e}")

        writer.write(
            b"HTTP/1.1 400 Bad Request\r\n"
            b"Connection: close\r\n\r\n"
        )
        await writer.drain()

    writer.close()
    await writer.wait_closed()


async def handle_confirm_alarm(reader, writer, headers, presenter):
    try:
        length = int(headers.get("content-length", 0))
        body = await reader.readexactly(length)

        params = {}

        for pair in body.decode().split("&"):
            key, value = pair.split("=", 1)
            params[key] = value

        ch = int(params["ch"])

        presenter.confirm_alarm(ch)

        writer.write(
            b"HTTP/1.1 204 No Content\r\n"
            b"Connection: close\r\n\r\n"
        )

        await writer.drain()

    except Exception as e:
        error(f"[API] alarm failed: {e}")

    writer.close()
    await writer.wait_closed()