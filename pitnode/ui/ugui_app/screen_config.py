# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import asyncio

from gui.core.tgui import Screen
from gui.widgets import Label, Button, CloseButton

from pitnode.ui.ugui_app.ugui_init import wrt_keyboard, wrt_md_red
from pitnode.storage.secrets import save_password, save_ssid
from pitnode.log.log import error, info
from pitnode.ui.ugui_app.screen_wifi import WLANsetupScreen
from pitnode.ui.ugui_app.ugui_init import UIPositions as Pos
from pitnode.ui.ugui_app.colors import *

# Header
def header_label(label_text):
    Label(wrt_md_red, 0, Pos.margin, label_text)

class ConfigScreen(Screen):
    presenter = None

    @classmethod
    def set_presenter(cls, presenter):
        cls.presenter = presenter

    def __init__(self):
        super().__init__()
        assert self.presenter is not None # type: ignore
        gap_entries = 14
                
        # Header
        header_label("Configuration")

        row=48
        col = Pos.margin
        Label(
            wrt_keyboard,
            row,
            col,
            "WiFi",
        )
        
        Button(
                wrt_keyboard,
                row,
                Pos.lcd_width-110,
                text="Config",
                callback=self._open_wlan_config,
                height=30,
                width=50
            )
        
        row = row+30+gap_entries
        Label(
            wrt_keyboard,
            row,
            col,
            "Probes",
        )

        Button(
            wrt_keyboard,
            row,
            Pos.lcd_width-110,
            text="Calibration",
            callback=self._start_cal,
            height=30,
            width=50
        )
        CloseButton(wrt_keyboard)

    def _open_wlan_config(self, *_):
        WlanConfig.set_presenter(self.presenter)
        Screen.change(WlanConfig)

    def _open_wlan_screen(self, *_):
        WLANsetupScreen.set_presenter(self.presenter)
        Screen.change(WLANsetupScreen)

    def _start_cal(self, *_):
        CalWizard.set_presenter(self.presenter)
        Screen.change(CalWizard)

class WlanConfig(Screen):
    presenter = None

    @classmethod
    def set_presenter(cls, presenter):
        cls.presenter = presenter

    def __init__(self):
        super().__init__()
        assert self.presenter is not None # type: ignore

        header_label("WiFi-Configuration")

        row=48
        col = Pos.margin

        Label(
            wrt_keyboard,
            row,
            col,
            "PitNode Webserver"
        )

        row = row+20
        lbl_ip = Label(
            wrt_keyboard,
            row,
            col+Pos.margin,
            Pos.lcd_width-3*Pos.margin
        )
        lbl_ip.value(f"IP: {self.presenter.get_ip()}")

        row = row+20
        lbl_ssid = Label(
            wrt_keyboard,
            row,
            col+Pos.margin,
            Pos.lcd_width-3*Pos.margin
        )
        lbl_ssid.value(f"SSID: {self.presenter.get_connected_ssid()}")
        
        row = row+30
        Button(
                wrt_keyboard,
                row,
                2*Pos.margin,
                text="Start Scan",
                callback=self._open_wlan_scan,
                height=30,
                width=50
            )
        
        CloseButton(wrt_keyboard)
        
    def _open_wlan_scan(self, *_):
        WlanScan.set_presenter(self.presenter)
        Screen.change(WlanScan)

class WlanScan(Screen):
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

        header_label("WiFi-Scan")

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

                    Label(wrt_keyboard, 30, Pos.margin, "Available networks")

                    for idx, net in enumerate(networks):
                        btn = Button(
                            wrt_keyboard,
                            54 + idx * 28,
                            2*Pos.margin,
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
        if not self.presenter.get_cfg().DEV_MODE: #type:ignore
            info(f"Save SSID under {self.presenter.get_wifi_cfg_path()}") #type:ignore
            save_ssid(btn.text, self.presenter.get_wifi_cfg_path()) #type:ignore
        self.presenter.set_selected_ssid(btn.text) #type:ignore
        WLANsetupScreen.set_presenter(self.presenter)
        Screen.change(WLANsetupScreen)

class CalWizard(Screen):
    presenter = None

    @classmethod
    def set_presenter(cls, presenter):
        cls.presenter = presenter

    def __init__(self):
        super().__init__()
        assert self.presenter is not None # type: ignore
        self._num_of_lines = range(5)
        self._lbls = [None] * len(self._num_of_lines)
        self._btns_list = [None] * self.presenter.get_num_probe_channels()
        self._ch_to_cal_state = [False] * self.presenter.get_num_probe_channels()
        self._ch_to_cal_list = [None] * self.presenter.get_num_probe_channels()
        self._ch_colors = [CH1_COL, CH2_COL, CH3_COL]
        
        # Header
        header_label("Calibration-Wizard")
        
        # Textbox
        row=30
        for line in self._num_of_lines:
            self._lbls[line] = Label(wrt_keyboard, row, Pos.margin, Pos.lcd_width-2*Pos.margin)
            row = self._lbls[line].mrow + 2 # type: ignore

        # Buttons
        self._btn = Button(
            wrt_keyboard,
            row+4,
            Pos.margin,
            text="Confirm",
            callback=self._on_confirm,
            height=36,
            width=60
        )
        start_col = self._btn.mcol
        for ch in range(len(self._btns_list)):
            self._btns_list[ch] = Button(
                wrt_keyboard,
                row+4,
                start_col+10+ch*30,
                text=f"{ch+1}",
                callback=self._on_select,
                height=26,
                width=26,
                )

        self._instruction_txt = self.presenter.start_calibration()
        self._update_instruction_text(self._instruction_txt)

        CloseButton(wrt_keyboard, callback=self._on_close)

    def _update_instruction_text(self, lines):
        for idx in self._num_of_lines:
            if idx < len(lines):
                self._lbls[idx].value(lines[idx]) # type: ignore
            else:
                self._lbls[idx].value("") # type: ignore
    
    def _on_confirm(self, *_):
        for btn in self._btns_list:
            btn.greyed_out(True)
        self._instruction_txt = self.presenter.cal_confirm() # type:ignore
        self._update_instruction_text(self._instruction_txt)
        
    def _on_select(self, btn, *_):
        # Callback should give an argument as parameter which indicates which channel was pressed
        # Then The button shall be shown as active + the idx of the channel shall be added to a list
        
        ch_idx = int(btn.text) - 1
        info(f"[CAL] Button pressed for {ch_idx}")

        if self._ch_to_cal_state[ch_idx] is False:
            self._ch_to_cal_state[ch_idx] = True
            self._ch_to_cal_list[ch_idx] = ch_idx
            self._btns_list[ch_idx].bgcolor = self._ch_colors[ch_idx]
        else:
            self._ch_to_cal_state[ch_idx] = False
            self._ch_to_cal_list[ch_idx] = None
            self._btns_list[ch_idx].bgcolor = DEF_BG
        
        self.presenter.set_ch_to_cal( #type:ignore
            [ch for ch in self._ch_to_cal_list if ch is not None]
        )
        btn.show()

    def _on_close(self, *_):
        self.presenter.cal_close() # type: ignore
        #Screen.change(ConfigScreen)