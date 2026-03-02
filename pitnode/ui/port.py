# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import asyncio
from pitnode.app.app import App
from pitnode.core.controller import PitNodeCtrl as Ctrl

async def start_ui():
    from pitnode.ui.impl_ugui import start_gui
    from pitnode.driver.rpi_pico import RPiPico
    Ctrl.hw = RPiPico  # type: ignore
    app = App()
    await app.start()
    await start_gui(app)

async def start_local():
    from pitnode.driver.mock_hw import MockHw
    Ctrl.hw = MockHw  # type: ignore
    Ctrl.hw.set_mock_pw() # type: ignore
    app = App()
    await app.start()
    app._on_gui_ready()
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Stopping local run")