# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

from math import log

from pitnode.log.log import info, warn, error

class CalibrationWizard:
    def __init__(self, num_probe_ch, unit):
        self._num_probe_ch = num_probe_ch
        self._unit = unit
        self._state = "IDLE"
        self._instruction = ""
        self._ref_temps_K = [274.15, 298.15, 343.15]
        self._resistance_results = [None] * len(self._ref_temps_K)
        self._beta = [None] * self._num_probe_ch
        self._ntc_coef = [None] * self._num_probe_ch
        

    def start(self):
        self._state = "CONFIG"
        self._resistance_results = [None] * self._num_probe_ch
        self._instruction = [
            f"Select channels to calibrate."
        ]
        return self._state, self._instruction

    def confirm(self, ch_to_cal_idxs, resistances):
        if self._state == "CONFIG":
            self._channel_idxs = ch_to_cal_idxs
            self._state = "WAIT_FOR_COLD"
            self._instruction = [
                f"Put probe {self._channel_idxs} into ice water.",
                "Put ref. probe into ice water.",
                f"Wait until ref. probe shows {(self._ref_temps_K[0] - 273.15)} {self._unit}.",
                "Wait until temp. has stabilized",
                "Press Confirm"
        ]
        elif self._state == "WAIT_FOR_COLD":
            self._resistance_results[0] = resistances
            self._state = "WAIT_FOR_AMB"
            self._instruction = [
                f"Slowly heat up water",
                f"Wait until ref. probe shows {(self._ref_temps_K[1] - 273.15)}  {self._unit}.",
                "Wait until temp. has stabilized",
                "Press Confirm"
            ]

        elif self._state == "WAIT_FOR_AMB":
            self._resistance_results[1] = resistances
            self._state = "WAIT_FOR_HOT"
            self._instruction = [
                f"Slowly heat up water.",
                f"Wait until ref. probe shows {(self._ref_temps_K[2] - 273.15)}  {self._unit}",
                "Wait until temp. has stabilized",
                "Press Confirm"
            ]

        elif self._state == "WAIT_FOR_HOT":
            self._resistance_results[2] = resistances
            self.calculate()
            if self._state == "ERROR":
                self._instruction = ["Error during calibration."]
                return self._state, self._instruction

            self._state = "DONE"
            self._instruction = ["Calibration done!"]
            ok = self.save_calibration_config(
                "/calibration.txt",
                self._ntc_coef,
            )

            if not ok:
                self._instruction.append("Save failed!")

        return self._state, self._instruction

    def calculate(self):
        for res in self._resistance_results:
            if res is None:
                self._state = "ERROR"
                info("[CAL] Res. is None")
                return
            
        for ch in self._channel_idxs:
            if ch is not None:
                self._beta[ch] = None
                self._ntc_coef[ch] = None
        
        for ch in self._channel_idxs:
            if ch is not None:
                r0 = self._resistance_results[0][ch] #type:ignore
                r1 = self._resistance_results[1][ch] #type:ignore
                r2 = self._resistance_results[2][ch] #type:ignore
                if (
                    r0 is None or r1 is None or r2 is None or
                    r0 <= 0 or r1 <= 0 or r2 <= 0
                ):
                    info("Invalid measurement")
                    self._state = "ERROR"
                    return
                
                if r0 <= 0 or r1 <= 0 or r2 <= 0:
                    self._state = "ERROR"
                    info("[CAL] Res. is neg.")
                    return

                if abs(r2 - r1) / r1 < 0.02:
                    self._state = "ERROR"
                    info("[CAL] Res. dif. to small")
                    return
                
                beta_val = self._calc_beta(
                    self._resistance_results[1][ch], #type:ignore
                    self._ref_temps_K[1],
                    self._resistance_results[2][ch], #type:ignore
                    self._ref_temps_K[2],
                )

                coef_val = self._calc_steinhart(
                    self._resistance_results[0][ch], #type:ignore
                    self._ref_temps_K[0],
                    self._resistance_results[1][ch], #type:ignore
                    self._ref_temps_K[1],
                    self._resistance_results[2][ch], #type:ignore
                    self._ref_temps_K[2]
                )

                if beta_val is None or coef_val is None:
                    self._state = "ERROR"
                    info("[CAL] Calc. coef. is None")
                    self._beta[ch] = None
                    self._ntc_coef[ch] = None
                    return
                
                self._beta[ch] = beta_val #type:ignore
                self._ntc_coef[ch] = coef_val

        info(f"[CAL] Calculated beta: {self._beta}")
        info(f"[CAL] Calculated Steinhart Coef.: {self._ntc_coef}")

        

    def _calc_beta(self, r25, t25, r100, t100):
        # --- Guards ---
        if r25 <= 0 or r100 <= 0:
            info("Invalid resistance")
            return None

        if t25 <= 0 or t100 <= 0:
            raise ValueError("Invalid temperature")

        # gleiche Temperaturen verhindern
        if abs(t25 - t100) < 1e-6:
            info("Temperatures too similar")
            return None

        # gleiche Widerstände verhindern
        if abs(r25 - r100) / r25 < 0.01:  # <1%
            info("Resistances too similar")
            return None

        denom = (1/t25 - 1/t100)
        if abs(denom) < 1e-12:
            info("Invalid denominator")
            return None

        beta = log(r25 / r100) / denom

        # optional sanity check
        if beta < 1000 or beta > 10000:
            info("Beta out of expected range")
            return None

        return int(beta)
    
    def _calc_steinhart(self, R1, T1, R2, T2, R3, T3):
        # --- Guards ---
        if R1 <= 0 or R2 <= 0 or R3 <= 0:
            info("Invalid resistance (<=0)")
            return None

        # gleiche Widerstände verhindern
        if abs(R1 - R2) < 1e-6 or abs(R1 - R3) < 1e-6 or abs(R2 - R3) < 1e-6:
            info("Duplicate resistance values")
            return None

        L1, L2, L3 = log(R1), log(R2), log(R3)
        Y1, Y2, Y3 = 1/T1, 1/T2, 1/T3

        # Denominator Checks
        if abs(L2 - L1) < 1e-12 or abs(L3 - L1) < 1e-12 or abs(L3 - L2) < 1e-12:
            info("Invalid log spacing")
            return None

        g2 = (Y2 - Y1) / (L2 - L1)
        g3 = (Y3 - Y1) / (L3 - L1)

        denom = (L1 + L2 + L3)
        if abs(denom) < 1e-12:
            info("Invalid denominator")
            return None

        C = (g3 - g2) / (L3 - L2) / denom
        B = g2 - C * (L1**2 + L1*L2 + L2**2)
        A = Y1 - (B + C * L1**2) * L1

        return (A, B, C)

    def save_calibration_config(self, path, coef):
        try:
            num_ch = len(coef)

            A_vals = []
            B_vals = []
            C_vals = []

            for ch in range(num_ch):
                if coef[ch] is None:
                    A=0
                    B=0
                    C=0
                else:
                    A, B, C = coef[ch]

                A_vals.append(f"{A:.8e}")
                B_vals.append(f"{B:.8e}")
                C_vals.append(f"{C:.8e}")

            with open(path, "w") as f:
                f.write("# Steinhart-Hart calibration\n")
                f.write("SH_A = " + ", ".join(A_vals) + "\n")
                f.write("SH_B = " + ", ".join(B_vals) + "\n")
                f.write("SH_C = " + ", ".join(C_vals) + "\n")

            return True

        except Exception as e:
            print("Save error:", e)
            return False