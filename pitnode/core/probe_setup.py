# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import pitnode.driver.hw_config as hw_cfg
import config as cfg
from pitnode.core.probe import NtcProbe

def setup_probes(ctrl):
    if len(cfg.PROBES) != hw_cfg.PROBE_CHANNELS:
        raise ValueError("Probe count does not match hardware channels")

    for ch, p in enumerate(cfg.PROBES):
        if p != "NTC":
            raise ValueError("Unsupported probe type")

        probe = NtcProbe(
            cfg.T_NTC_0_MK[ch],
            cfg.BETA_K[ch],
            cfg.R_NTC_0_OHM[ch],
        )

        if not ctrl.register_probe(ch, probe):
            raise ValueError(f"Probe registration failed for channel {ch}")
