# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import pytest
from pitnode.core.controller import PitNodeCtrl, NtcProbe
from pitnode.driver.mock_hw import MockHw
from pitnode.core import config_parser
from pitnode.core.config_parser import Config
from pitnode.core.calibration import CalibrationWizard

T_NTC_0_MK = [298150, 298150, 298150] # in mK
BETA_MK = [3977, 3977, 3977] # in mK
R_NTC_0_MILOHM = [100000, 100000, 100000] # in Ohm
R_SERIES_MILOHM = [47000, 47000, 47000] # in Ohm

@pytest.fixture
def setup_mock():
    hw = MockHw()
    cfg = config_parser.Config("config_linux.txt")
    ctrl = PitNodeCtrl(hw, cfg)
    for ch in range(ctrl.num_probe_ch):
        probe = NtcProbe(T_NTC_0_MK[ch], BETA_MK[ch], R_NTC_0_MILOHM[ch], f"NTC Probe CH{ch}")
        ctrl.register_probe(ch, probe)
    return ctrl, cfg

def test_calibration():
    #ctrl, cfg = setup_mock
    channel_idxs_to_cal = [0]
    num_probe_channels = 3
    wiz = CalibrationWizard(channel_idxs_to_cal, num_probe_channels)
    state, instruction = wiz.start()
    assert state == "WAIT_FOR_COLD"
    resistances = [200000, 0, 0]
    state, inst = wiz.confirm(resistances)
    assert state == "WAIT_FOR_AMB"
    resistances = [100000, 0, 0]
    state, inst = wiz.confirm(resistances)
    assert state == "WAIT_FOR_HOT"
    resistances = [10000, 0, 0]
    state, inst = wiz.confirm(resistances)
    assert wiz._beta == [3415, None, None]

    channel_idxs_to_cal = [0, 1, 2]
    num_probe_channels = 3
    wiz = CalibrationWizard(channel_idxs_to_cal, num_probe_channels)
    state, instruction = wiz.start()
    assert state == "WAIT_FOR_COLD"
    resistances = [200000, 200000, 200000]
    state, inst = wiz.confirm(resistances)
    assert state == "WAIT_FOR_AMB"
    resistances = [100000, 100000, 100000]
    state, inst = wiz.confirm(resistances)
    assert state == "WAIT_FOR_HOT"
    resistances = [10000, 10000, 10000]
    state, inst = wiz.confirm(resistances)
    assert wiz._beta == [3415, 3415, 3415]
    assert wiz._ntc_coef == [3415, 3415, 3415]




