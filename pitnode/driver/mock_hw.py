# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import pitnode.driver.hw_config as hw_cfg

class DummyBuzzer():
    pass

class MockHw:
    def __init__(self):
        self._buzzer = DummyBuzzer()
        pass

    def read_raw(self):
        mv_list = [2244, 2244, 2244]
        raw = [int((mv*65535/hw_cfg.V_ADC_REF_MV)) for mv in mv_list]
        return raw

    def buzzer_on(self):
        pass

    def buzzer_off(self):
        pass

    def reboot(self):
        pass