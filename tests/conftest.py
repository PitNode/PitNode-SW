# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import pytest
from pitnode.core.controller import PitNodeCtrl
from pitnode.driver.mock_hw import MockHw
from pitnode.core.probe import NtcProbe


class Config():
    def __init__(
            self,
            board: str,
            unit: str,
            probe_model: str,
            t_ntc_0_mk: list,
            beta_k: list,
            r_ntc_0_ohm: list,
            sh_a: list,
            sh_b: list,
            sh_c: list,
            probes: list,
            enable_wifi: bool,
            dev_mode: bool,
            web_port: int,
            web_port_dev: int
            ) -> None:
          self.BOARD = board
          self.UNIT = unit
          self.PROBE_MODEL = probe_model
          self.T_NTC_0_MK = t_ntc_0_mk
          self.BETA_K = beta_k
          self.R_NTC_0_OHM = r_ntc_0_ohm
          self.SH_A = sh_a
          self.SH_B = sh_b
          self.SH_C = sh_c
          self.PROBES = probes
          self.ENABLE_WIFI = enable_wifi
          self.DEV_MODE = dev_mode
          self.WEB_PORT = web_port
          self.WEB_PORT_DEV = web_port_dev

@pytest.fixture
def config():
    T_NTC_0_MK = [298150, 298150, 298150] # in mK
    BETA_MK = [3977, 3977, 3977] # in mK
    R_NTC_0_OHM = [100000, 100000, 100000] # in Ohm
    R_SERIES_OHM = [47000, 47000, 47000] # in Ohm
    SH_A = [1.40e-3, 1.40e-3, 1.40e-3]
    SH_B = [2.37e-4, 2.37e-4, 2.37e-4]
    SH_C = [9.90e-8, 9.90e-8, 9.90e-8]
    PROBES = ["NTC", "NTC", "NTC"]
    
    config = Config(
        board="LINUX",
        unit="cel",
        probe_model="BETA",
        t_ntc_0_mk=T_NTC_0_MK,
        beta_k=BETA_MK,
        r_ntc_0_ohm=R_NTC_0_OHM,
        sh_a=SH_A,
        sh_b=SH_B,
        sh_c=SH_C,
        probes=PROBES,
        enable_wifi=True,
        dev_mode=True,
        web_port=80,
        web_port_dev=8080
     )
    return config

@pytest.fixture
def mock_hw():
    mock_hw = MockHw()
    return mock_hw

@pytest.fixture
def ctrl(config, mock_hw):
    controller = PitNodeCtrl(
          hw=mock_hw,
          cfg=config
          )
    return controller

@pytest.fixture
def ctrl_ready(config, mock_hw):
    controller = PitNodeCtrl(
          hw=mock_hw,
          cfg=config
          )
    
    for ch in range(3):
        probe = NtcProbe(config.T_NTC_0_MK[ch], config.BETA_K[ch], config.R_NTC_0_OHM[ch], f"NTC Probe CH{ch}")
        controller.register_probe(ch, probe)
    
    return controller