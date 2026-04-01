# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import pytest
from pitnode.core.calibration import CalibrationWizard

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CalibrationCase:
    channels: List[int]
    inputs: List[List[Optional[int]]]
    expected_beta: List[Optional[int]]

COLD = 200_000
AMB = 100_000
HOT = 10_000

@pytest.fixture
def wizard(tmp_path):
    wiz = CalibrationWizard(3, "cel")
    wiz._cal_path = tmp_path / "calibration_test.txt"
    return wiz

@pytest.mark.parametrize(
    "case",
    [
        CalibrationCase(
            channels=[0],
            inputs=[
                [None, None, None],
                [COLD, None, 0],
                [AMB, 0, 0],
                [HOT, 0, 0],
            ],
            expected_beta=[5235, None, None],
        ),
        CalibrationCase(
            channels=[0, 1, 2],
            inputs=[
                [None, None, None],
                [COLD, COLD, COLD],
                [AMB, AMB, AMB],
                [HOT, HOT, HOT],
            ],
            expected_beta=[5235, 5235, 5235],
        ),
    ],
)

def test_calibration_flow(wizard, case: CalibrationCase):
    state, _ = wizard.start()
    assert state == "CONFIG"

    expected_states = [
        "WAIT_FOR_COLD",
        "WAIT_FOR_AMB",
        "WAIT_FOR_HOT",
        None,  # letzter Schritt
    ]

    for resistances, expected_state in zip(case.inputs, expected_states):
        state, _ = wizard.confirm(case.channels, resistances)
        if expected_state:
            assert state == expected_state

    assert wizard._beta == case.expected_beta


def test_steinhart_coefficients(wizard):
    wizard.start()
    wizard.confirm([0,1,2], [None]*3)
    wizard.confirm([0,1,2], [200000]*3)
    wizard.confirm([0,1,2], [100000]*3)
    wizard.confirm([0,1,2], [10000]*3)

    A, B, C = wizard._ntc_coef[0]

    assert A == pytest.approx(0.0063358854061730235, rel=1e-2)
    assert B == pytest.approx(-0.0005715167659476293, rel=1e-2)
    assert C == pytest.approx(2.3577587605046423e-06, rel=1e-2)

def test_calibration_invalid_values(wizard):
    wizard.start()
    wizard.confirm([0], [None]*3)
    wizard.confirm([0], [200000, 0, 0])
    wizard.confirm([0], [200000, 0, 0])
    state, inst = wizard.confirm([0], [200000, 0, 0])

    assert wizard._beta == [None, None, None]
    assert wizard._ntc_coef[0] is None
    assert inst == ['Error during calibration.']

def test_steinhart_repeat(wizard):
    T1 = 274.15
    T2 = 298.15
    T3 = 343.15
    results = []

    for _ in range(100000):
        A, B, C = wizard._calc_steinhart(
            200000, T1,
            100000, T2,
            10000, T3
        )
        results.append(B)

    assert max(results) - min(results) < 1e-9
