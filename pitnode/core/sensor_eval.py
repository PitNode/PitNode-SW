# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

from pitnode.core.probe import ProbeState
import pitnode.driver.hw_config as hw_cfg

def eval_resistance_raw(raw, r_series):
    mv = (raw * hw_cfg.V_ADC_REF_MV) // 65535

    if mv <= hw_cfg.ADC_MIN_MV:
        return None, ProbeState.SHORT

    if mv >= hw_cfg.ADC_MAX_MV:
        return None, ProbeState.OPEN

    denom = hw_cfg.V_ADC_REF_MV - mv
    if denom <= 0:
        return None, ProbeState.INVALID

    r_ntc = (r_series * mv) // denom

    if r_ntc <= 0 or r_ntc > hw_cfg.R_MAX_OHM:
        return None, ProbeState.OPEN

    return r_ntc, ProbeState.OK
