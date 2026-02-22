# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

from pitnode.ui.impl_ugui import start_gui

from pitnode.app.app import App
from pitnode.core.controller import PitNodeCtrl as Ctrl
from pitnode.driver.rpi_pico import RPiPico


async def start_ui():
    Ctrl.hw = RPiPico  # type: ignore

    app = App()
    await app.start()
    await start_gui(app)
