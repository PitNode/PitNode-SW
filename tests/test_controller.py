# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import pytest
import config as config
from pitnode.core.controller import PitNodeCtrl, NtcProbe
from pitnode.driver.mock_hw import MockHw

T_NTC_0_MK = [298150, 298150, 298150] # in mK
BETA_MK = [3977, 3977, 3977] # in mK
R_NTC_0_MILOHM = [100000, 100000, 100000] # in mOhm
R_SERIES_MILOHM = [47000000, 47000000, 47000000] # in mOhm

@pytest.fixture
def valid_controller():
    for ch in range(3):
        probe = NtcProbe(T_NTC_0_MK[ch], BETA_MK[ch], R_NTC_0_MILOHM[ch], f"NTC Probe CH{ch}")
        PitNodeCtrl.register_probe(ch, probe)
    
    # Config auf Default setzen
    config.UNIT = "deg"

    # set values to valid temps
    PitNodeCtrl._probe_target_deg_c_value = [51.0, 52.0, 53.0]
    PitNodeCtrl._probe_deg_c_value = [31.0, 32.0, 33.0]
    PitNodeCtrl._probe_mv_value = [1001, 1002, 1003]
    PitNodeCtrl._probe_raw_value = [10001, 10002, 10003]
    PitNodeCtrl._probe_resistance_value = [5001, 5002, 5003]
    PitNodeCtrl._probe_mv_valid = 0b111
    PitNodeCtrl._probe_raw_valid = 0b111
    PitNodeCtrl._probe_target_valid = 0b111
    PitNodeCtrl._probe_resistance_valid = 0b111
    PitNodeCtrl._probe_deg_c_valid = 0b111

    return PitNodeCtrl

@pytest.fixture
def valid_no_probes_controller():
    # Config auf Default setzen
    config.UNIT = "deg"

    # set values to valid temps
    PitNodeCtrl._probe_target_deg_c_value = [51.0, 52.0, 53.0]
    PitNodeCtrl._probe_mv_value = [1001, 1002, 1003]
    PitNodeCtrl._probe_raw_value = [10001, 10002, 10003]
    PitNodeCtrl._probe_resistance_value = [5001, 5002, 5003]
    PitNodeCtrl._probe_mv_valid = 0b111
    PitNodeCtrl._probe_raw_valid = 0b111
    PitNodeCtrl._probe_target_valid = 0b111
    PitNodeCtrl._probe_resistance_valid = 0b111
    PitNodeCtrl._probe_deg_c_valid = 0b111

    return PitNodeCtrl

def test_probe_reg(valid_no_probes_controller: PitNodeCtrl):
    ctrl = valid_no_probes_controller
    reg_res = []
    for ch in range(3):
        probe = NtcProbe(T_NTC_0_MK[ch], BETA_MK[ch], R_NTC_0_MILOHM[ch], f"NTC Probe CH{ch}")
        reg_res.append(ctrl.register_probe(ch, probe))
    assert reg_res == [True, True, True]
    
    reg_res.append(ctrl.register_probe(3, "Bad probe"))
    assert reg_res[3] == False

def test_get_temp(valid_controller: PitNodeCtrl):
    ctrl = valid_controller
    temps = [ctrl.get_temp(ch) for ch in range(3)]
    assert temps == [31.0, 32.0, 33.0]
    temps = []
    temps = ctrl.get_temps()
    assert temps == [31.0, 32.0, 33.0]
    temp = ctrl.get_temp(3)
    assert temp == False

def test_set_target_temp_deg(valid_controller: PitNodeCtrl):
    ctrl = valid_controller
    ctrl._probe_target_valid = 0b000
    ctrl.set_target_temp(1, 100)
    assert ctrl._probe_target_deg_c_value[1] == 100.0
    assert ctrl._probe_target_valid == 0b010
    assert ctrl.is_temp_valid(1) == True

def test_invalid_channel_negative():
    config.UNIT = "deg"
    assert PitNodeCtrl.set_target_temp(-1, 100) is False

def test_invalid_temp_type():
    config.UNIT = "deg"
    assert PitNodeCtrl.set_target_temp(0, "hot") is False #type:ignore


def test_invalid_unit():
    config.UNIT = "kelvin"
    assert PitNodeCtrl.set_target_temp(0, 100) is False

# Integration tests
def test_trigger_measurement_loop(valid_controller):
    Ctrl = valid_controller
    Ctrl.hw = MockHw()
    resistances = Ctrl.read_res_ohm()
    assert resistances == pytest.approx([100000, 100000, 100000], abs=300)
    assert Ctrl._probes[0].resistance_to_deg_c(resistances[0]) == pytest.approx(25, abs=0.11)

@pytest.mark.asyncio
async def test_controller_lifecycle(valid_controller):
    Ctrl = valid_controller
    Ctrl.hw = MockHw()
    await Ctrl.start_pitnode_ctrl()
    await Ctrl.stop_pitnode_ctrl()
    assert Ctrl._running is False
    assert Ctrl._tasks == []

# Integration tests
@pytest.mark.asyncio
async def test_start_is_idempotent(valid_controller):
    Ctrl = valid_controller
    Ctrl.hw = MockHw()
    await Ctrl.start_pitnode_ctrl()
    await Ctrl.start_pitnode_ctrl()
    assert len(Ctrl._tasks) == 2