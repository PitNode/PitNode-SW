# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de


from pitnode.core.probe import ProbeState

# def eval_resistance_raw(raw, r_series, hw_cfg):
#     mv = (raw * hw_cfg.V_ADC_REF_MV) // 65535

#     if mv <= hw_cfg.ADC_MIN_MV:
#         return None, ProbeState.SHORT

#     if mv >= hw_cfg.ADC_MAX_MV:
#         return None, ProbeState.OPEN

#     denom = hw_cfg.V_ADC_REF_MV - mv
#     if denom <= 0:
#         return None, ProbeState.INVALID

#     r_ntc = (r_series * mv) // denom

#     if r_ntc <= 0 or r_ntc > hw_cfg.R_MAX_OHM:
#         return None, ProbeState.OPEN

#     return r_ntc, ProbeState.OK

def eval_resistance_raw(raw, r_series, hw_cfg):
    if raw <= hw_cfg.ADC_MIN_RAW:
        return None, ProbeState.SHORT

    if raw >= hw_cfg.ADC_MAX_RAW:
        return None, ProbeState.OPEN

    raw_corr = (raw * 3300) // hw_cfg.V_REF_MV
    denom = 65535 - raw_corr
    if denom <= 0:
        return None, ProbeState.INVALID
    
    r_ntc = (r_series * raw_corr) // denom

    if r_ntc <= 0 or r_ntc > hw_cfg.R_MAX_OHM:
        return None, ProbeState.OPEN

    return r_ntc, ProbeState.OK