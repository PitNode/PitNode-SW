# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import pytest
from pitnode.core.controller import PitNodeCtrl
from pitnode.core.probe import NtcProbe
from tests.conftest import Config


def test_probe_registration(ctrl: PitNodeCtrl, config: Config):
    result = []
    for ch in range(3):
        probe = NtcProbe(config.T_NTC_0_MK[ch], config.BETA_K[ch], config.R_NTC_0_OHM[ch], f"NTC Probe CH{ch}")
        result.append(ctrl.register_probe(ch, probe))
    assert result == [True, True, True]
    
    result.append(ctrl.register_probe(3, "Bad probe"))
    assert result[3] == False
    assert len(ctrl._probes) == 3

def test_get_temp(ctrl_ready: PitNodeCtrl):
    raws = [30000, 30000, 30000]
    resistances = [47928, 47928, 47928]
    temps = [25.0, 25.0, 25.0]
    ctrl_ready.hw._raw_temps = raws
    result = ctrl_ready.read_res_ohm()
    assert result == resistances
    ctrl_ready._probe_deg_c_value = temps
    ctrl_ready._probe_deg_c_valid |= 1 << 0
    assert ctrl_ready.get_temps() == temps

def test_set_target_temp_deg(valid_controller: PitNodeCtrl):
    ctrl = valid_controller
    ctrl._probe_target_valid = 0b000
    ctrl.set_target_temp(1, 100)
    assert ctrl._probe_target_deg_c_value[1] == 100.0
    assert ctrl._probe_target_valid == 0b010
    assert ctrl.is_temp_valid(1) == True

def test_invalid_channel_negative():
    config.UNIT = "cel"
    assert PitNodeCtrl.set_target_temp(-1, 100) is False

def test_invalid_temp_type():
    config.UNIT = "cel"
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