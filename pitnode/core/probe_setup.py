# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de


from pitnode.core.probe import NtcProbe

def setup_probes(ctrl):
    if len(ctrl.cfg.PROBES) != ctrl.num_probe_ch:
        raise ValueError("Probe count does not match hardware channels")

    A, B, C = ctrl.cfg.get_sh_coeff()
    for ch, p in enumerate(ctrl.cfg.PROBES):
        if p != "NTC":
            raise ValueError("Unsupported probe type")

        probe = NtcProbe(
            A[ch],
            B[ch],
            C[ch],
        )

        if not ctrl.register_probe(ch, probe):
            raise ValueError(f"Probe registration failed for channel {ch}")
