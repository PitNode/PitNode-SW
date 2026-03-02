# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import pitnode.driver.hw_config as hw_cfg
import pitnode.storage.secrets as secret
from pitnode.log.log import error, info

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

    _temp_c = 20.0
    _direction = 1  # 1 = hoch, -1 = runter

    T_MIN = 20.0
    T_MAX = 120.0
    STEP = 0.5  # °C pro Aufruf

    @classmethod
    def _next_temp(cls):
        cls._temp_c += cls._direction * cls.STEP

        if cls._temp_c >= cls.T_MAX:
            cls._temp_c = cls.T_MAX
            cls._direction = -1
        elif cls._temp_c <= cls.T_MIN:
            cls._temp_c = cls.T_MIN
            cls._direction = 1

        return cls._temp_c

    @classmethod
    def _temp_to_mv(cls, temp_c):
        """
        Beispiel: 10 mV pro °C (z.B. LM35-ähnlich).
        Falls du NTC oder Thermocouple simulierst,
        musst du hier deine Kennlinie einsetzen.
        """
        return temp_c * 10.0

    @classmethod
    def read_raw(cls):
        temp_c = cls._next_temp()

        mv = cls._temp_to_mv(temp_c)

        raw = int((mv * 65535) / hw_cfg.V_ADC_REF_MV)

        # drei Kanäle identisch
        return [raw, raw, raw]

class MockHw:
    _buzzer = DummyBuzzer()
    _wlan = MockWiFiDriver()
    _temp_mock = TempMock
    _wlan_cfg_path  = "/mnt/synology/philipp/Bastel_Projekte/Elektro-Bauprojekte/PitNode/FW/pitnode/tests"

    @classmethod
    def set_mock_pw(cls):
        secret.save_password("TestPw")

    @classmethod
    def wlan(cls):
        return cls._wlan
    
    @classmethod
    def read_raw(cls):
        return cls._temp_mock.read_raw()
    
    @classmethod
    def read_tc(cls) -> float | None:
        return 100.0

    @classmethod
    def buzzer_on(cls):
        pass
    
    @classmethod
    def buzzer_off(cls):
        pass
    
    @classmethod
    def reboot(cls):
        pass
    
    @classmethod
    def unique_id(cls):
        return b"pitnode-dev-uid"