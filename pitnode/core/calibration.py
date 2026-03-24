# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

from math import log

from pitnode.log.log import info, warn, error

class CalibrationWizard:
    def __init__(self, ch_to_cal_idxs, num_probe_ch):
        self._channel_idxs = ch_to_cal_idxs
        self._num_probe_ch = num_probe_ch
        self._state = "IDLE"
        self._instruction = ""
        self._resistance_results = [None] * 3
        self._beta = [None] * self._num_probe_ch
        self._ntc_coef = [None] * self._num_probe_ch
        self._ref_temps_K = [273.15, 298.15, 373.15]

    def start(self):
        self._state = "WAIT_FOR_COLD"
        self._instruction = f"Put probe {self._channel_idxs} into ice water."\
                            "Wait until reference probe shows {(self._ref_temps_K[0] - 273.15)} deg C."\
                            "Wait 10 sec. until temperature has stabilized"\
                            "Press Confirm"
        return self._state, self._instruction

    def confirm(self, resistances):

        if self._state == "WAIT_FOR_COLD":
            self._resistance_results[0] = resistances
            self._state = "WAIT_FOR_AMB"
            self._instruction = f"Slowly heat up water"\
                                "Wait until reference probe shows {(self._ref_temps_K[1] - 273.15)} deg C."\
                                "Wait 10 sec. until temperature has stabilized"\
                                "Press Confirm"

        elif self._state == "WAIT_FOR_AMB":
            self._resistance_results[1] = resistances
            self._state = "WAIT_FOR_HOT"
            self._instruction = f"Slowly heat up water."\
                                "Wait until reference probe shows {(self._ref_temps_K[2] - 273.15)} deg C."\
                                "Wait 10 sec. until temperature has stabilized"\
                                "Press Confirm"

        elif self._state == "WAIT_FOR_HOT":
            self._resistance_results[2] = resistances
            self._state = "CALCULATE"
            self._instruction = f"Calibration done!"
            self.calculate()

        return self._state, self._instruction

    def calculate(self):
        self._state = "DONE"
        for ch in self._channel_idxs:
            self._beta[ch] = self._calc_beta( #type:ignore
                self._resistance_results[1][ch], #type:ignore
                self._ref_temps_K[1],
                self._resistance_results[2][ch], #type:ignore
                self._ref_temps_K[2],
            )
            self._ntc_coef[ch] = self._calc_steinhart( #type:ignore
                self._resistance_results[0][ch], #type:ignore
                self._ref_temps_K[0],
                self._resistance_results[1][ch], #type:ignore
                self._ref_temps_K[1],
                self._resistance_results[2][ch], #type:ignore
                self._ref_temps_K[2]
            )
        info(f"[CAL] Calculated beta: {self._beta}")
        info(f"[CAL] Calculated Steinhart Coef.: {self._ntc_coef}")

    def _calc_beta(self, r25, t25, r100, t100):
        beta = log(r25 / r100) / (1/t25 - 1/t100)
        return int(beta)
    
    def _calc_steinhart(self, R1, T1, R2, T2, R3, T3):
        L1, L2, L3 = log(R1), log(R2), log(R3)
        Y1, Y2, Y3 = 1/T1, 1/T2, 1/T3

        g2 = (Y2 - Y1) / (L2 - L1)
        g3 = (Y3 - Y1) / (L3 - L1)

        C = (g3 - g2) / (L3 - L2)
        B = g2 - C * (L1**2 + L1*L2 + L2**2)
        A = Y1 - (B + C * L1**2) * L1

        return A, B, C
