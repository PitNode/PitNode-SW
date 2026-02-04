# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de


import gc
# Allocate large static objects early to avoid heap fragmentation
import touch_setup as touch_setup # Framebuffer
import pitnode.initialize # Fonts
import pitnode.ui.screen_measure as screen_measure
import pitnode.ui.screen_wifi
import pitnode.ui.screen_config

gc.collect()

import asyncio

from pitnode.app import App
from pitnode.controller import PitNodeCtrl as Ctrl
from pitnode.driver.rpi_pico import RPiPico


async def main():
    Ctrl.hw = RPiPico # type:ignore
    app = App()
    await app.start()
    await screen_measure.start_gui(app.presenter)  # never returns
if __name__ == "__main__":
    asyncio.run(main())
