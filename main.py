# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de


# import gc
# # Allocate large static objects early to avoid heap fragmentation
# import ui.ugui.touch_setup as touch_setup # Framebuffer
# import pitnode.core.initialize # Fonts
# import pitnode.ui.ugui_app.screen_measure as screen_measure
# import pitnode.ui.ugui_app.screen_wifi
# import pitnode.ui.ugui_app.screen_config

# gc.collect()

# import asyncio

# from pitnode.app.app import App
# from pitnode.core.controller import PitNodeCtrl as Ctrl
# from pitnode.driver.rpi_pico import RPiPico


# async def main():
#     Ctrl.hw = RPiPico # type:ignore
#     app = App()
#     await app.start()
#     await screen_measure.start_gui(app.presenter)  # never returns
# if __name__ == "__main__":
#     asyncio.run(main())


# main.py
import asyncio
from pitnode.ui.port import start_ui

if __name__ == "__main__":
    asyncio.run(start_ui())
