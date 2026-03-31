# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import pytest
from math import log
from pitnode.core.controller import NtcProbe


def calc_steinhart(R1, T1, R2, T2, R3, T3):
    L1, L2, L3 = log(R1), log(R2), log(R3)
    Y1, Y2, Y3 = 1/T1, 1/T2, 1/T3

    g2 = (Y2 - Y1) / (L2 - L1)
    g3 = (Y3 - Y1) / (L3 - L1)

    C = (g3 - g2) / (L3 - L2) / (L1 + L2 + L3)
    B = g2 - C * (L1**2 + L1*L2 + L2**2)
    A = Y1 - (B + C * L1**2) * L1
    return A, B, C

@pytest.fixture
def setup_ntc_probe():
    A, B, C = calc_steinhart(
    R1=32650, T1=273.15,
    R2=10000, T2=298.15,
    R3=1200,  T3=373.15,
    )
    ntc_probe = NtcProbe(A, B, C, "NTC Test Probe")
    return ntc_probe

def test_calibration(setup_ntc_probe):
    ntc_probe = setup_ntc_probe
    deg_c = ntc_probe.resistance_to_deg_c(32650)
    assert deg_c == pytest.approx(0, abs=0.5)
    deg_c = ntc_probe.resistance_to_deg_c(10000)
    assert deg_c == pytest.approx(25, abs=0.5)
    deg_c = ntc_probe.resistance_to_deg_c(1200)
    assert deg_c == pytest.approx(100, abs=0.5)
