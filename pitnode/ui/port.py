# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import asyncio
from pitnode.app.app import App


async def start_ui():
    from pitnode.ui.impl_ugui import start_gui
    from pitnode.driver.rpi_pico import RPiPico
    hw = RPiPico()  # type: ignore
    app = App(hw=hw)
    await app.start()
    await start_gui(app)

async def start_local():
    from pitnode.driver.mock_hw import MockHw
    hw = MockHw()  # type: ignore
    hw.set_mock_pw() # type: ignore
    app = App(hw=hw)
    await app.start()
    app._on_gui_ready()
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Stopping local run")