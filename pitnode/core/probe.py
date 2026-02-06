# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

from math import log
try:
    from micropython import const # type:ignore
except ImportError:
    def const(x): return x

OPEN_THRESHOLD = const(3)
VALID_THRESHOLD = const(2)

class ProbeState:
    OK = const(0)
    OPEN = const(1)
    SHORT = const(2)
    INVALID = const(3)

class NtcProbe:
    def __init__(
        self,
        t_ntc_0_mk=298150,  # 25°C in milli-Kelvin
        beta_k=3380,  # Beta in Kelvin
        r_ntc_0_ohm=100000,  # 100kΩ in Ohm
        name="NTC std probe",
    ):
        self.name = name
        self._t0 = t_ntc_0_mk / 1000.0  # K
        self._beta = beta_k  # K
        self._r0 = r_ntc_0_ohm  # Ω

    def resistance_to_k(self, r_ohm:int):
        r = r_ohm
        return 1.0 / ((1.0 / self._t0) + (1.0 / self._beta) * log(r / self._r0))

    def resistance_to_deg_c(self, r_ohm: int):
        return round(self.resistance_to_k(r_ohm) - 273.15, 1)

    def resistance_to_deg_f(self, r_ohm):
        return round(self.resistance_to_deg_c(r_ohm) * 9 / 5 + 32, 1)