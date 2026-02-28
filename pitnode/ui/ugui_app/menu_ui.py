# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import asyncio

from gui.core.tgui import Screen, Window
from gui.widgets import Label, Button, Pad
from pitnode.ui.ugui_app.ugui_init import wrt_icon
from pitnode.ui.ugui_app.ugui_init import UIPositions as Pos
from gui.core.colors import *
from pitnode.ui.ugui_app.colors import *
from pitnode.ui.ugui_app.screen_config import ConfigScreen
from pitnode.log.log import error, info

class Menu:
    def __init__(self, presenter, screen) -> None:
        self.presenter = presenter
        self.screen = screen
        # WiFi icon
        lbl_wifi = Label(
            wrt_icon,
            4+Pos.menu_row,
            Pos.menu_col,
            "D", # Wifi Icon
        )
        self.wifi_label = lbl_wifi

        # Invisible Button for setup
        btn_cfg = Pad(
            wrt_icon,
            4+Pos.menu_row,
            lbl_wifi.mcol+10,
            callback=self._config_screen,
            height=40,
            width=40
        )
        self.config_button = btn_cfg
        
        # Setup icon
        Label(
            wrt_icon,
            4+Pos.menu_row,
            lbl_wifi.mcol+10,
            text="B"
        )

        self.screen.reg_task(self._update_status(), on_change=False)

    async def _update_status(self):
        try:
            last_wifi = None
            while True:
                status = self.presenter.get_status()
                if status:
                    wifi = status.wifi.connected
                    if wifi != last_wifi:
                        self.wifi_label.value(
                            fgcolor=GREEN if wifi else GREY
                        )
                        last_wifi = wifi
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            info("[GUI] Status update task stopped")
            raise

    def _config_screen(self, _):
        ConfigScreen.set_presenter(self.presenter)
        Screen.change(ConfigScreen)