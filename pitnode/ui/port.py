# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

#from pitnode.ui.impl_ugui import start_gui
from pitnode.log.log import logger, info, warn, error
import asyncio
import sys
from pitnode.core import config_parser

def start():
    if sys.implementation.name == "micropython":
        info("port.py start()")
        cfg = config_parser.Config()
        logger.set_mode(cfg.DEV_MODE) # type: ignore
        info("Running on MicroPython")
        if cfg.BOARD == "PITNODEPICOTOUCH": # type: ignore
            asyncio.run(start_pitnode_pico_touch_app(cfg))
    else:
        cfg = config_parser.Config("config_linux.txt")
        logger.set_mode(cfg.DEV_MODE) # type: ignore
        info("Running on CPython (Linux/dev)")
        asyncio.run(start_local(cfg)) 

async def start_pitnode_pico_touch_app(cfg):
    from pitnode.ui.impl_ugui import start_gui
    from pitnode.app.app import App
    from pitnode.driver.init_pitnode_pico_touch import hw
    app = App(cfg=cfg, hw=hw)
    await app.start()
    await start_gui(app)

async def start_local(cfg):
    from pitnode.app.app import App
    from pitnode.driver.init_pitnode_mock import hw
    hw.set_mock_pw() # type: ignore
    app = App(cfg=cfg, hw=hw)
    await app.start()
    app._on_gui_ready()
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Stopping local run")