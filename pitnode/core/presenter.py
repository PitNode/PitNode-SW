# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de


import asyncio

from pitnode.core.controller import PitNodeCtrl as Ctrl
from pitnode.log.log import info, warn, error

class PitNodePresenter:
    def __init__(self, status, wifi):
        self._on_gui_ready = None
        self.screen = None
        self._status = status
        self._on_reboot = None
        self.websockets = []
        self.num_probe_channels = Ctrl.num_channels()
        self._wifi_config_handler = None
        self._wifi = wifi
        self._selected_ssid = None
        self._wifi_abort_handler = None

    def set_wifi_abort_handler(self, handler):
        self._wifi_abort_handler = handler

    def abort_wifi_config(self):
        if self._wifi_abort_handler:
            self._wifi_abort_handler()

    def set_selected_ssid(self, ssid):
        self._selected_ssid = ssid

    def get_selected_ssid(self):
        return self._selected_ssid

    def set_wifi_config_handler(self, handler):
        self._wifi_config_handler = handler

    def request_wifi_config(self):
        if self._wifi_config_handler:
            self._wifi_config_handler()

    def get_wifi_networks(self):
        return self._wifi.networks

    def get_status(self):
        return self._status
    
    def get_num_probe_channels(self):
        return self.num_probe_channels

    def set_gui_ready_callback(self, cb):
        self._on_gui_ready = cb

    def screen_attached(self):
        if self._on_gui_ready:
            self._on_gui_ready()

    def attach_screen(self, screen):
        self.screen = screen
        #self.screen_attached()

    def detach_screen(self):
        self.screen = None

    def attach_ws(self, ws):
        self.websockets.append(ws)

    def detach_ws(self, ws):
        if ws in self.websockets:
            self.websockets.remove(ws)

    def get_tc_temp(self):
        return Ctrl.get_tc_temp()

    def get_temps(self):
        return Ctrl.get_temps()
    
    def get_probe_states(self):
        return Ctrl.get_probe_states()

    def get_tc_probe_state(self):
        return Ctrl.get_tc_probe_state()

    def get_targets(self):
        return Ctrl.get_target_temps()
    
    def get_target(self, ch):
        return Ctrl.get_target_temp(ch)
    
    def get_alarms(self):
        return [Ctrl.is_alarm_active(ch) for ch in range(self.num_probe_channels)]

    # ---- user actions (called from lcdgui or websocket) -------------------------

    def set_reboot_handler(self, fn):
        self._on_reboot = fn

    def request_reboot(self):
        if self._on_reboot:
            self._on_reboot()

    def inc_target(self, ch):
        tt = Ctrl.get_target_temp(ch)
        if tt != None and Ctrl.increase_target_temp(ch, 1):
            screen=self.screen
            if screen:
                screen.update_target(ch, Ctrl.get_target_temp(ch)) # type: ignore

    def dec_target(self, ch):
        tt = Ctrl.get_target_temp(ch)
        if tt != None and Ctrl.decrease_target_temp(ch, 1):
            screen=self.screen
            if screen:
                screen.update_target(ch, Ctrl.get_target_temp(ch)) # type: ignore

    def set_target_temp(self, ch, temp):
        Ctrl.set_target_temp(ch, temp)
        screen=self.screen
        if screen:
            self.screen.update_target(ch, temp) # type: ignore

    def set_target_temps(self, target_temps):
        status = Ctrl.set_target_temps(target_temps)
        screen=self.screen
        for ch, tt, st in zip(range(screen.num_channels_pp), target_temps, status): # type: ignore
            if st:
                if screen:
                    self.screen.update_target(ch, tt) # type: ignore

    def reset_alarm(self, ch):
        Ctrl.reset_alarm(ch)
        if self.screen:
            self.screen.set_alarm(ch, False) # type: ignore

    def confirm_alarm(self, ch):
        Ctrl.confirm_alarm(ch)

    def is_alarm_active(self, ch):
        return Ctrl.is_alarm_active(ch)
    
    def is_alarm_confirmed(self, ch):
        return Ctrl.is_alarm_confirmed(ch)


