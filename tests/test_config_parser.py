# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import pytest
from pitnode.core import config_parser


@pytest.fixture
def cfg_no_cal():
    cfg = config_parser.Config("config_linux.txt")
    return cfg

@pytest.fixture
def cfg_cal():
    cfg = config_parser.Config("config_linux.txt", "./tests/calibration_test.txt")
    return cfg

@pytest.fixture
def cfg_cal_one_ch():
    cfg = config_parser.Config("config_linux.txt", "./tests/calibration_test_one_ch.txt")
    return cfg

def test_parser_simple(cfg_no_cal):
    assert cfg_no_cal.PROBE_MODEL == "BETA"
    assert cfg_no_cal.SH_A == [0.0014, 0.0014, 0.0014]

def test_parser_cal_simple(cfg_cal):
    assert cfg_cal.PROBE_MODEL == "SH"
    assert cfg_cal.SH_A == [6.335885e-03, 6.335885e-03, 6.335885e-03]
    assert cfg_cal.SH_B == [-5.715168e-04, -5.715168e-04, -5.715168e-04]
    assert cfg_cal.SH_C == [2.357759e-06, 2.357759e-06, 2.357759e-06]

def test_parser_cal_one_ch(cfg_cal_one_ch):
    assert cfg_cal_one_ch.PROBE_MODEL == "SH"
    assert cfg_cal_one_ch.SH_A == [0.00045913952621429166, 1.12345e-03, 0.00045913952621429166]
    assert cfg_cal_one_ch.SH_B == [0.0002514458134272065, 2.23456e-04, 0.0002514458134272065]
    assert cfg_cal_one_ch.SH_C == [0, 3.34567e-05, 0]

def test_parser_helper_functions(cfg_no_cal):
    cfg_no_cal.PROBE_MODEL = "SH"
    A, B, C = cfg_no_cal.get_sh_coeff()
    assert A == [1.40e-3, 1.40e-3, 1.40e-3]
    assert B == [2.37e-4, 2.37e-4, 2.37e-4]
    assert C == [9.90e-8, 9.90e-8, 9.90e-8]
    cfg_no_cal.PROBE_MODEL = "BETA"
    A, B, C = cfg_no_cal.get_sh_coeff()
    assert A == pytest.approx([0.00045913952621429166, 0.00045913952621429166, 0.00045913952621429166], rel=1)
    assert B == pytest.approx([0.0002514458134272065, 0.0002514458134272065, 0.0002514458134272065], rel=1)
    assert C == pytest.approx([0, 0, 0], rel=1)
