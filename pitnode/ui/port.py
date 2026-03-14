# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import asyncio
import sys

from pitnode.app.app import App
from pitnode.core import config_parser
from pitnode.log.log import info, warn, error

def start():
    if sys.implementation.name == "micropython":
        info("Running on MicroPython")
        cfg = config_parser.Config()
        if cfg.BOARD == "PITNODEPICOTOUCH": # type: ignore
            asyncio.run(start_pitnode_pico_touch_app(cfg))
    else:
        info("Running on CPython (Linux/dev)")
        cfg = config_parser.Config("config_linux.txt")
        asyncio.run(start_local(cfg))    

async def start_pitnode_pico_touch_app(cfg):
    from pitnode.core.init_pitnode_pico_touch import hw
    from pitnode.ui.impl_ugui import start_gui
    
    app = App(cfg=cfg, hw=hw)
    await app.start()
    await start_gui(app)

async def start_local(cfg):
    import pitnode.driver.hw_config as hw_cfg
    from pitnode.driver.mock_hw import MockHw
    
    hw_cfg.BASE_PATH = "/mnt/synology/philipp/Bastel_Projekte/Elektro-Bauprojekte/PitNode/FW"
    hw = MockHw(hw_cfg)  # type: ignore
    hw.set_mock_pw() # type: ignore
    app = App(hw=hw)
    await app.start()
    app._on_gui_ready()
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Stopping local run")