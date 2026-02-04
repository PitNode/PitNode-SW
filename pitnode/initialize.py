# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import gui.fonts.freesans25_temp as font_lg_temp
import gui.fonts.freesans14_red as font_md_red
import gui.fonts.freesans20_ext as font_keyboard
import gui.fonts.icons as icons
from gui.core.colors import *
from gui.core.tgui import ssd

import pitnode.hw_config as hw_cfg
import pitnode.config as cfg
from pitnode.controller import PitNodeCtrl as Ctrl
from pitnode.controller import NtcProbe

assert len(cfg.T_NTC_0_MK) == hw_cfg.PROBE_CHANNELS
assert len(cfg.BETA_K) == hw_cfg.PROBE_CHANNELS
assert len(cfg.R_NTC_0_OHM) == hw_cfg.PROBE_CHANNELS

for ch in range(hw_cfg.PROBE_CHANNELS):
    probe = NtcProbe(cfg.T_NTC_0_MK[ch], cfg.BETA_K[ch], cfg.R_NTC_0_OHM[ch], f"NTC Probe CH{ch}")
    reg_status = Ctrl.register_probe(ch, probe)
    if not reg_status:
        raise ValueError
    
wrt_lg_temp = CWriter(ssd, font_lg_temp, WHITE, BLACK, False)
wrt_md_red = CWriter(ssd, font_md_red, WHITE, BLACK, False)
wrt_icon = CWriter(ssd, icons, WHITE, BLACK, False)
wrt_keyboard = CWriter(ssd, font_keyboard, WHITE, BLACK, False)