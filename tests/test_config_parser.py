# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import pytest
from pitnode.core import config_parser



@pytest.fixture
def load_cfg():
    cfg = config_parser.Config("config_linux.txt")
    return cfg

def test_parser_simple(load_cfg):
    cfg = load_cfg
    assert cfg.PROBE_MODEL == "BETA"
    assert cfg.SH_A == [0.0014, 0.0014, 0.0014]

def test_parser_helper_functions(load_cfg):
    cfg = load_cfg
    cfg.PROBE_MODEL = "SH"
    A, B, C = cfg.get_sh_coeff()
    assert A == [1.40e-3, 1.40e-3, 1.40e-3]
    assert B == [2.37e-4, 2.37e-4, 2.37e-4]
    assert C == [9.90e-8, 9.90e-8, 9.90e-8]
    cfg.PROBE_MODEL = "BETA"
    A, B, C = cfg.get_sh_coeff()
    assert A == pytest.approx([0.00045913952621429166, 0.00045913952621429166, 0.00045913952621429166], rel=1)
    assert B == pytest.approx([0.0002514458134272065, 0.0002514458134272065, 0.0002514458134272065], rel=1)
    assert C == pytest.approx([0, 0, 0], rel=1)
