# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de


from pitnode.core.probe import NtcProbe

def setup_probes(ctrl):
    if len(ctrl.cfg.PROBES) != ctrl.num_probe_ch:
        raise ValueError("Probe count does not match hardware channels")

    for ch, p in enumerate(ctrl.cfg.PROBES):
        if p != "NTC":
            raise ValueError("Unsupported probe type")

        probe = NtcProbe(
            ctrl.cfg.T_NTC_0_MK[ch],
            ctrl.cfg.BETA_K[ch],
            ctrl.cfg.R_NTC_0_OHM[ch],
        )

        if not ctrl.register_probe(ch, probe):
            raise ValueError(f"Probe registration failed for channel {ch}")
