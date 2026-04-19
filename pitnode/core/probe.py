# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de


from math import log
try:
    from micropython import const # type:ignore
except ImportError:
    def const(x): return x

from pitnode.log.log import info, warn, error

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
        A,
        B,
        C,
        name="NTC std probe",
    ):
        self.name = name
        self.A = A
        self.B = B
        self.C = C

    def resistance_to_k(self, r_ohm:float):
        L = log(r_ohm)
        inv_T = self.A + self.B * L + self.C * (L**3)
        return 1 / inv_T

    def resistance_to_deg_c(self, r_ohm: float):
        return round(self.resistance_to_k(r_ohm) - 273.15, 1)

    def resistance_to_deg_f(self, r_ohm: float):
        return round(self.resistance_to_deg_c(r_ohm) * 9 / 5 + 32, 1)