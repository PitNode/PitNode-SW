# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import pytest
from pitnode.core.calibration import CalibrationWizard


def test_calibration():
    #ctrl, cfg = setup_mock
    channel_idxs_to_cal = [0]
    num_probe_channels = 3
    wiz = CalibrationWizard(num_probe_channels, "cel")
    state, instruction = wiz.start()
    assert state == "CONFIG"
    resistances = [None, None, None]
    state, inst = wiz.confirm(channel_idxs_to_cal, resistances)
    assert state == "WAIT_FOR_COLD"
    resistances = [200000, None, 0]
    state, inst = wiz.confirm(channel_idxs_to_cal, resistances)
    assert state == "WAIT_FOR_AMB"
    resistances = [100000, 0, 0]
    state, inst = wiz.confirm(channel_idxs_to_cal, resistances)
    assert state == "WAIT_FOR_HOT"
    resistances = [10000, 0, 0]
    state, inst = wiz.confirm(channel_idxs_to_cal, resistances)
    assert wiz._beta == [5235, None, None]

    channel_idxs_to_cal = [0, 1, 2]
    num_probe_channels = 3
    wiz = CalibrationWizard(num_probe_channels, "cel")
    state, instruction = wiz.start()
    assert state == "CONFIG"
    resistances = [None, None, None]
    state, inst = wiz.confirm(channel_idxs_to_cal, resistances)
    assert state == "WAIT_FOR_COLD"
    resistances = [200000, 200000, 200000]
    state, inst = wiz.confirm(channel_idxs_to_cal, resistances)
    assert state == "WAIT_FOR_AMB"
    resistances = [100000, 100000, 100000]
    state, inst = wiz.confirm(channel_idxs_to_cal, resistances)
    assert state == "WAIT_FOR_HOT"
    resistances = [10000, 10000, 10000]
    state, inst = wiz.confirm(channel_idxs_to_cal, resistances)
    assert wiz._beta == [5235, 5235, 5235]
    A, B, C = wiz._ntc_coef[0] #type:ignore
    assert A == pytest.approx(0.0063358854061730235, rel=1)
    assert B == pytest.approx(-0.0006346794085656607, rel=1)
    assert C == pytest.approx(2.553057337749313e-06, rel=1)

def test_calibration_neg():
    #ctrl, cfg = setup_mock
    channel_idxs_to_cal = [0]
    num_probe_channels = 3
    wiz = CalibrationWizard(num_probe_channels, "cel")
    state, instruction = wiz.start()
    assert state == "CONFIG"
    resistances = [None, None, None]
    state, inst = wiz.confirm(channel_idxs_to_cal, resistances)
    assert state == "WAIT_FOR_COLD"
    resistances = [200000, 0, 0]
    state, inst = wiz.confirm(channel_idxs_to_cal, resistances)
    assert state == "WAIT_FOR_AMB"
    resistances = [200000, 0, 0]
    state, inst = wiz.confirm(channel_idxs_to_cal, resistances)
    assert state == "WAIT_FOR_HOT"
    resistances = [200000, 0, 0]
    state, inst = wiz.confirm(channel_idxs_to_cal, resistances)
    assert wiz._beta == [None, None, None]
    assert wiz._ntc_coef[0] == None
    assert inst == ['Error during calibration.']