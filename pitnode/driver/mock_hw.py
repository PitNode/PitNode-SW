# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de


import pitnode.storage.secrets as secret
from pitnode.log.log import error, info
from pitnode.driver.base_board import BaseBoard

class MockHw(BaseBoard):
    def __init__(self, hw_cfg) -> None:
        super().__init__(hw_cfg)

        self._buzzer = DummyBuzzer()
        self._wlan = MockWiFiDriver()
        self._temp_mock = TempMock(self._hw_cfg)
        self.wlan_cfg_path  = self._join(self._hw_cfg.BASE_PATH, "pitnode/tests")

    @property
    def num_probe_channels(self):
        return self._hw_cfg.PROBE_CHANNELS

    def _join(self, base, rel):
        if base.endswith("/"):
            return base + rel
        return base + "/" + rel

    def set_mock_pw(self):
        secret.save_password("TestPw", self.wlan_cfg_path, self.unique_id())

    def wlan(self):
        return self._wlan
    
    def read_raw(self):
        return self._temp_mock.read_raw()
    
    def read_tc(self) -> float | None:
        return 100.0

    def buzzer_on(self):
        pass
    
    def buzzer_off(self):
        pass
    
    def reboot(self):
        pass
    
    def unique_id(self):
        return b"pitnode-dev-uid"
    
class DummyBuzzer():
    pass

class MockWiFiDriver:
    def __init__(self):
        self._connected = False
        self._active = False

    def active(self, state=None):
        if state is None:
            return self._active
        self._active = state
        info(f"MCK_WIFI: Active -> {state}")
        return self._active

    def connect(self, ssid, password):
        info("MCK_WIFI: Connect")
        self._connected = True

    def isconnected(self):
        info("MCK_WIFI: Is connected")
        return self._connected

    def disconnect(self):
        info("MCK_WIFI: Disconnect")
        self._connected = False

    def scan(self):
        return []

    def status(self, key=None):
        if key == "rssi":
            return -42
        return 0

    def ifconfig(self):
        return ("192.168.100.10", "255.255.255.0", "192.168.100.1", "8.8.8.8")

class TempMock:
    def __init__(self, hw_cfg) -> None:
        self._hw_cfg = hw_cfg
        self._temp_c = 20.0
        self._direction = 1  # 1 = hoch, -1 = runter
        self.T_MIN = 20.0
        self.T_MAX = 120.0
        self.STEP = 0.5  # °C pro Aufruf

    def _next_temp(self):
        self._temp_c += self._direction * self.STEP

        if self._temp_c >= self.T_MAX:
            self._temp_c = self.T_MAX
            self._direction = -1
        elif self._temp_c <= self.T_MIN:
            self._temp_c = self.T_MIN
            self._direction = 1

        return self._temp_c

    def _temp_to_mv(self, temp_c):
        """
        Beispiel: 10 mV pro °C (z.B. LM35-ähnlich).
        Falls du NTC oder Thermocouple simulierst,
        musst du hier deine Kennlinie einsetzen.
        """
        return temp_c * 10.0

    def read_raw(self):
        temp_c = self._next_temp()

        mv = self._temp_to_mv(temp_c)

        raw = int((mv * 65535) / self._hw_cfg.V_ADC_REF_MV)

        # drei Kanäle identisch
        return [raw, raw, raw]