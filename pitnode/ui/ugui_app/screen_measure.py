# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import asyncio
import gc
import time
from math import sin
from micropython import const

import touch_setup as touch_setup
from gui.core.tgui import Screen, ssd
#from gui.core.writer import CWriter
#from gui.widgets import Label, CloseButton
#from gui.core.colors import *

from pitnode.ui.ugui_app.ugui_init import wrt_lg_temp, wrt_md_red, wrt_icon
from pitnode.ui.ugui_app.ugui_init import UIPositions as Pos
from pitnode.ui.ugui_app.channel_ui import ChannelUI, BBQchUI
from pitnode.ui.ugui_app.menu_ui import Menu
import config as cfg
from pitnode.core.probe import ProbeState
from pitnode.log.log import error, info
from pitnode.ui.ugui_app.colors import *


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
        self._pulse_tasks = [None] * self.presenter.get_num_probe_channels()
        self.ch_color = [CH1_COL, CH2_COL, CH3_COL]
        self.ch_rgb = [CH_1_RGB, CH_2_RGB, CH_3_RGB]
        self.temp_labels = []
        self.target_labels = []
        self.tc_temp_label = None
        self.ledbars = []
        self.inc_buttons = []
        self.dec_buttons = []
        self.config_button = None
        self.num_channels_pp = Pos.ch_per_page
        self._create_layout()
        

    def after_open(self):
        gc.collect()
        # Background image
        fn = "bg_img.bin"
        with open(fn, "rb") as f:
            _ = f.read(4)
            f.readinto(ssd.mvb)
        
        # Then draw layout overlaying
        self.show(True)
        self.presenter.screen_attached() # type:ignore

    #--- LCD Layout ---#
    def _create_layout(self):
        """
        Static elements: title, separators, column headers
        """
        self._create_channels()
        self._side_menu()

    def _side_menu(self):
        sm = Menu(self.presenter, self)

    def _create_channels(self):
        """
        Per-channel rows: temperature, target, +/- buttons
        """
        ch_ui_list = [None] * Pos.ch_per_page
        for ch in range(Pos.ch_per_page): # type:ignore
            ch_ui_list[ch] = ChannelUI(ch, self.presenter)  # type:ignore
            ch_ui_list[ch].ch_card(Pos.ch_start_row, # type:ignore
                                    0+(ch*Pos.ch_width),
                                    Pos.ch_height,
                                    Pos.ch_width,
                                    self.ch_color[ch])
            self.temp_labels.append(ch_ui_list[ch].temp_label) # type:ignore
            self.target_labels.append(ch_ui_list[ch].target_label) # type:ignore
            self.ledbars.append(ch_ui_list[ch].ledbar) # type:ignore
        
        bbq_ui = BBQchUI()
        bbq_ui.bbq_card(4+Pos.margin, 4+Pos.margin)
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
    def set_alarm(self, ch, alarm_state):
        #self.temp_labels[ch].value(invert=bool(state))
        if alarm_state:
            if self._pulse_tasks[ch] is None:
                self._pulse_tasks[ch] = self.reg_task(self._pulse_ledbar(ch),  on_change=False)
        else:
            task = self._pulse_tasks[ch]
            if task is not None:
                task.cancel()
                self._pulse_tasks[ch] = None

    def update_tc_temp(self, value, state):
        if value is None:
            self.tc_temp_label.value("---.-") # type: ignore
        if state != ProbeState.OK:
            self.tc_temp_label.value("---.-") # type: ignore
        else:
            self.tc_temp_label.value("{:.0f}".format(value)) # type: ignore

    def update_temp(self, ch, value, state):
        if value is None:
            self.temp_labels[ch].value("---")
        if state != ProbeState.OK:
            self.temp_labels[ch].value("---")
        else:
            new_text = "{:.0f}".format(value)
            if self.temp_labels[ch].value() != new_text:
                self.temp_labels[ch].value(new_text)

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

    async def _pulse_ledbar(self, ch):
        def triangle_wave(period_ms=1000):
            t = time.ticks_ms() % period_ms
            half = period_ms // 2

            if t < half:
                return (t * 255) // half
            else:
                return ((half - (t - half)) * 255) // half

        try:
            info("[SCR] Pulse lable task started")
            while True:
                brightness = triangle_wave(1000)
                min_brightness = 80
                brightness = min_brightness + ((brightness * (255 - min_brightness)) // 255)
                base = self.ch_rgb[ch]
                r = (base[0] * brightness) // 255
                g = (base[1] * brightness) // 255
                b = (base[2] * brightness) // 255
                self.ledbars[ch].color(SSD.rgb(r, g, b))
                await asyncio.sleep_ms(50)
        except asyncio.CancelledError:
            info("[SCR] Pulse lable task stopped")
            self.ledbars[ch].color(self.ch_color[ch])
            raise
