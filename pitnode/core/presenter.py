# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de


from pitnode.log.log import info, warn, error

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from pitnode.core.controller import PitNodeCtrl
    from pitnode.app.app import WifiView, SystemStatus


class PitNodePresenter:
    def __init__(self, system_status: "SystemStatus", wifi_view: "WifiView", ctrl: "PitNodeCtrl"):
        self._on_gui_ready = None
        self.screen = None
        self._status = system_status
        self._wifi_view = wifi_view
        self._on_reboot = None
        self.websockets = []
        self._ctrl = ctrl
        self._cfg = self._ctrl.cfg
        self._wifi_config_handler = None
        self._selected_ssid = None
        self._wifi_abort_handler = None
        self.unit = None
        self._ch_to_cal = range(self.get_num_probe_channels()+1)

        if self._cfg.UNIT == "cel":
            self.unit = "°C"
        elif self._cfg.UNIT == "far":
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
    def get_cfg(self):
        return self._cfg

    def get_wifi_cfg_path(self):
        return self._ctrl.hw.wlan_cfg_path
    
    def get_hw_uid(self):
        return self._ctrl.hw.uid

    def get_unit(self):
        return self.unit

    def set_selected_ssid(self, ssid):
        self._selected_ssid = ssid

    def get_selected_ssid(self):
        return self._selected_ssid

    def get_wifi_networks(self):
        return self._wifi_view.get_scan_result()
    
    def get_ip(self):
        return self._status.wifi.ip
    
    def get_connected_ssid(self):
        return self._wifi_view.get_connected_ssid()
    
    def get_rssi(self):
        return self._wifi_view.get_rssi()

    def get_status(self):
        return self._status
    
    def get_num_probe_channels(self):
        return self._ctrl.num_probe_ch
    
    def get_probe_types(self):
        return self._cfg.PROBES
    
    def get_probe_model(self):
        return self._cfg.PROBE_MODEL

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
    
    def get_resistances(self):
        return self._ctrl.read_res_ohm()
    
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

    def set_ch_to_cal(self, ch_list):
        self._ch_to_cal = ch_list

    def start_calibration(self):
        _, instruction = self._ctrl.start_calibration(self.get_unit())
        return instruction
    
    def cal_confirm(self):
        state, instruction = self._ctrl.cal_confirm(self._ch_to_cal)

        if state == "ERROR":
            return ["Cal. not successful. Restart..."]

        if state == "DONE":
            return instruction

        return instruction
    
    def cal_close(self):
        self._ctrl.cal_close()