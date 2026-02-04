# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import asyncio
import gc
import time
from micropython import const

import touch_setup as touch_setup
from gui.core.tgui import Screen, ssd
from gui.core.writer import CWriter
from gui.widgets import Label, CloseButton
from gui.core.colors import *

from pitnode.initialize import wrt_lg_temp, wrt_md_red, wrt_icon
from pitnode.ui.channel_ui import ChannelUI, BBQchUI
from pitnode.ui.side_menu_ui import SideMenu
import pitnode.config as cfg
from pitnode.hw_config import ProbeState
from pitnode.log.log import error, info


# GUI definitions
HEADER_H = const(24)  # Header height in px
CH_PPAGE = const(3)  # Number of channels to display per page
PAGES = const(1)  # Number of pages
MARGIN_LR = const(6)  # Margin to left and right side in px
MARGIN_TB = const(6)
COL1_W = const(70)  # Column 1 width in px
COL2_W = const(130)  # Column 1 width in px
CH_ROW_START = HEADER_H + 2
CH_COL_START = MARGIN_LR
BG_COLOR = BLACK  # Background color
LINE_COLOR = GREY  # Color of GUI lines
CH_COLORS = [YELLOW, GREEN, MAGENTA]
CH_SPACING = int((ssd.height - (HEADER_H + 2)) / CH_PPAGE)

async def start_gui(presenter):
    MeasureScreen.set_app(presenter)
    Screen.change(MeasureScreen)

class MeasureScreen(Screen):
    presenter = None

    @classmethod
    def set_app(cls, presenter):
        cls.presenter = presenter
    
    def __init__(self):
        super().__init__()
        assert self.presenter is not None
        # UI wiring
        self.presenter.attach_screen(self)
        self.reg_task(self._get_temp_loop(), on_change=False)
        self.reg_task(self._get_alarms_loop(), on_change=False)

        self.num_channels_pp = CH_PPAGE
        self.temp_labels = []
        self.target_labels = []
        self.tc_temp_label = None
        self.inc_buttons = []
        self.dec_buttons = []
        self.config_button = None
        
        self.width = ssd.width
        self._create_layout()
        # self._create_buttons()
        # self._bind_events()

    def after_open(self):
        #self._header()
        pass

    #--- LCD Layout ---#
    def _create_layout(self):
        """
        Static elements: title, separators, column headers
        """
        self._create_channels()
        self._side_menu()

    def _side_menu(self):
        sm = SideMenu(self.presenter, self)

    def _create_channels(self):
        """
        Per-channel rows: temperature, target, +/- buttons
        """
        num_ch = self.presenter.get_num_probe_channels() # type:ignore
        start_col = ssd.width - (num_ch * 90) # type:ignore
        fgcolor = [WHITE, WHITE, WHITE]
        bgcolor = [MAGENTA, GREEN, BLUE]
        for ch in range(num_ch): # type:ignore
            ch_ui = ChannelUI(ch, self.presenter)
            ch_ui.ch_card(10, start_col+(ch*88), fgcolor[ch], bgcolor[ch])
            self.temp_labels.append(ch_ui.temp_label)
            self.target_labels.append(ch_ui.target_label)
        
        bbq_ui = BBQchUI()
        bbq_ui.bbq_card(170, start_col, WHITE, BLACK)
        self.tc_temp_label = bbq_ui.temp_label

    def _create_buttons(self):
        """
        Global buttons (alarm reset, menu, etc.)
        Left intentionally minimal – extend with your existing code.
        """
        pass

    def _bind_events(self):
        """
        Touch / long-press handling.
        Existing logic should stay here unchanged.
        """
        pass

    #--- Callbacks ---#
    def _on_target_inc(self, _, ch):
        self.presenter.inc_target(ch) # type: ignore

    def _on_target_dec(self, _, ch):
        self.presenter.dec_target(ch) # type: ignore

    def _on_alarm_reset(self, _, ch):
        self.presenter.reset_alarm(ch) # type: ignore

    #--- Update functions ---#
    def set_alarm(self, ch, state):
        self.temp_labels[ch].value(invert=bool(state))

    def update_tc_temp(self, value, state):
        if value is None:
            self.tc_temp_label.value("---.-") # type: ignore
        if state != ProbeState.OK:
            self.tc_temp_label.value("---.-") # type: ignore
        else:
            self.tc_temp_label.value("{:.1f}".format(value)) # type: ignore

    def update_temp(self, ch, value, state):
        if value is None:
            self.temp_labels[ch].value("--.-")
        if state != ProbeState.OK:
            self.temp_labels[ch].value("--.-")
        else:
            self.temp_labels[ch].value("{:.1f}".format(value))

    def update_target(self, ch, value):
        # f"{Ctrl.get_temp(ch):,.2f}
        value = str(round(value, 1))
        self.target_labels[ch].value(value)

    #--- Tasks ---#
    async def _get_temp_loop(self):
        try:
            info("[SCR] Temp update task started")
            while True:
                temps = self.presenter.get_temps() # type:ignore
                tc_temp = self.presenter.get_tc_temp() # type:ignore
                probe_states = self.presenter.get_probe_states() #type:ignore
                tc_probe_state = self.presenter.get_tc_probe_state() #type:ignore
                self.update_tc_temp(tc_temp, tc_probe_state)
                for ch, temp in enumerate(temps):
                    self.update_temp(ch, temp, probe_states[ch])
                await asyncio.sleep_ms(500)
        except asyncio.CancelledError:
            info("[SCR] Temp update task stopped")
            raise

    async def _get_alarms_loop(self):
        try:
            info("[SCR] Alarm update task started")
            while True:
                alarms = self.presenter.get_alarms() # type:ignore
                for ch, alarm in enumerate(alarms):
                    self.set_alarm(ch, alarm)
                await asyncio.sleep_ms(500)
        except asyncio.CancelledError:
            info("[SCR] Alarm update task stopped")
            raise
