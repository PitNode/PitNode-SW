# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import time
import asyncio

from gui.core.tgui import Screen
from gui.widgets import Label, Button, CloseButton
#from gui.core.colors import *

from pitnode.ui.ugui_app.ugui_init import wrt_keyboard, wrt_md_red
from pitnode.storage.secrets import save_password, save_ssid
import config as cfg
from pitnode.log.log import error, info
from pitnode.ui.ugui_app.screen_wifi import WLANsetupScreen
from pitnode.ui.ugui_app.ugui_init import UIPositions as Pos

class ConfigScreen(Screen):
    presenter = None

    @classmethod
    def set_presenter(cls, presenter):
        cls.presenter = presenter

    def __init__(self):
        super().__init__()
        assert self.presenter is not None # type: ignore
        gap_entries = 14
        row = Pos.margin
        col = Pos.margin
        config_entries = ["WLAN:"]
                
        lbl_config = Label(
            wrt_md_red,
            row,
            col,
            "Configuration",
        )

        lbl_ip = Label(
            wrt_keyboard,
            lbl_config.mrow+gap_entries,
            col,
            Pos.lcd_width-2*Pos.margin
        )
        lbl_ip.value(f"IP: {self.presenter.get_ip()}")

        for idx, entry in enumerate(config_entries):
            entry_label = Label(
                wrt_md_red,
                lbl_ip.mrow+idx*gap_entries,
                col,
                entry,
            )
            Button(
                wrt_md_red,
                lbl_ip.mrow-4+idx*gap_entries,
                220,
                text="Change",
                callback=self._open_wlan_config,
                height=30,
                width=50
            )
        CloseButton(wrt_md_red)

    def _open_wlan_config(self, *_):
        WlanConfig.set_presenter(self.presenter)
        Screen.change(WlanConfig)

    def _open_wlan_screen(self, *_):
        WLANsetupScreen.set_presenter(self.presenter)
        Screen.change(WLANsetupScreen)


class WlanConfig(Screen):
    presenter = None

    @classmethod
    def set_presenter(cls, presenter):
        cls.presenter = presenter

    def __init__(self):
        super().__init__()
        assert self.presenter is not None # type: ignore
        self._net_labels = []
        self._shown = False
        gap_entries = 4
        row = 10
        col = 10

        self.presenter.request_wifi_config()
        self.reg_task(self._update_networks(), on_change=False)

        Label(
            wrt_md_red,
            row,
            col,
            "WLAN Configuration",
        )
        CloseButton(wrt_md_red, callback=self._on_close)

    def _on_close(self, *_):
        self.presenter.abort_wifi_config() #type:ignore

    async def _update_networks(self):
        last_networks = None
        try:
            while True:
                networks = self.presenter.get_wifi_networks()  # type: ignore

                if networks and networks != last_networks:
                    self._net_labels.clear()

                    Label(wrt_md_red, 30, 10, "Available networks")

                    for idx, net in enumerate(networks):
                        btn = Button(
                            wrt_keyboard,
                            54 + idx * 28,
                            20,
                            height=26,
                            text=net,
                            callback=self._on_select,
                        )
                        self._net_labels.append(btn)

                    last_networks = list(networks)

                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            raise

    def _on_select(self, btn, *_):
        if not cfg.DEV_MODE:
            save_ssid(btn.text)
        self.presenter.set_selected_ssid(btn.text) #type:ignore
        WLANsetupScreen.set_presenter(self.presenter)
        Screen.change(WLANsetupScreen)