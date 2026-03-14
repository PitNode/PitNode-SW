# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de


from pitnode.log.log import info, warn, error
from config import UNIT


class PitNodePresenter:
    def __init__(self, system_status, wifi_view, ctrl):
        self._on_gui_ready = None
        self.screen = None
        self._status = system_status
        self._wifi_view = wifi_view
        self._on_reboot = None
        self.websockets = []
        self._ctrl = ctrl
        self._wifi_config_handler = None
        self._selected_ssid = None
        self._wifi_abort_handler = None
        self.unit = None

        if UNIT == "cel":
            self.unit = "°C"
        elif UNIT == "far":
            self.unit = "°F"
        else:
            error("Not a valid unit in config file")

    # Handler
    def set_wifi_abort_handler(self, handler):
        self._wifi_abort_handler = handler

    def abort_wifi_config(self):
        if self._wifi_abort_handler:
            self._wifi_abort_handler()

    def set_wifi_config_handler(self, handler):
        self._wifi_config_handler = handler

    def request_wifi_config(self):
        if self._wifi_config_handler:
            self._wifi_config_handler()

    def set_reboot_handler(self, fn):
        self._on_reboot = fn

    def request_reboot(self):
        if self._on_reboot:
            self._on_reboot()

    # API
    def get_unit(self):
        return self.unit

    def set_selected_ssid(self, ssid):
        self._selected_ssid = ssid

    def get_selected_ssid(self):
        return self._selected_ssid

    def get_wifi_networks(self):
        return self._wifi_view.get_scan_result()
    
    def get_ip(self):
        ip = self._status.wifi.ip
        return ip

    def get_status(self):
        return self._status
    
    def get_num_probe_channels(self):
        return self._ctrl.num_probe_ch

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
        return self._ctrl.get_tc_temp()

    def get_temps(self):
        return self._ctrl.get_temps()
    
    def get_probe_states(self):
        return self._ctrl.get_probe_states()

    def get_tc_probe_state(self):
        return self._ctrl.get_tc_probe_state()

    def get_targets(self):
        return self._ctrl.get_target_temps()
    
    def get_target(self, ch):
        return self._ctrl.get_target_temp(ch)
    
    def get_alarms(self):
        return [self._ctrl.is_alarm_active(ch) for ch in range(self._ctrl.hw.num_probe_channels)]

    def inc_target(self, ch):
        tt = self._ctrl.get_target_temp(ch)
        if tt != None and self._ctrl.increase_target_temp(ch, 1):
            screen=self.screen
            if screen:
                screen.update_target(ch, self._ctrl.get_target_temp(ch)) # type: ignore

    def dec_target(self, ch):
        tt = self._ctrl.get_target_temp(ch)
        if tt != None and self._ctrl.decrease_target_temp(ch, 1):
            screen=self.screen
            if screen:
                screen.update_target(ch, self._ctrl.get_target_temp(ch)) # type: ignore

    def set_target_temp(self, ch, temp):
        self._ctrl.set_target_temp(ch, temp)
        screen=self.screen
        if screen:
            self.screen.update_target(ch, temp) # type: ignore

    def set_target_temps(self, target_temps):
        status = self._ctrl.set_target_temps(target_temps)
        screen=self.screen
        for ch, tt, st in zip(range(screen.num_channels_pp), target_temps, status): # type: ignore
            if st:
                if screen:
                    self.screen.update_target(ch, tt) # type: ignore

    def reset_alarm(self, ch):
        self._ctrl.reset_alarm(ch)
        if self.screen:
            self.screen.set_alarm(ch, False) # type: ignore

    def confirm_alarm(self, ch):
        info(f"Presenter confirm_alarm called with: {ch}")
        self._ctrl.confirm_alarm(ch)

    def is_alarm_active(self, ch):
        return self._ctrl.is_alarm_active(ch)
    
    def is_alarm_confirmed(self, ch):
        return self._ctrl.is_alarm_confirmed(ch)
