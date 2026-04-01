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
        self._cal_path = "/calibration.txt"
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
                self._cal_path,
                self._ntc_coef,
            )

            if not ok:
                self._instruction.append("Save failed!")

        return self._state, self._instruction

    def calculate(self):
        # global check
        for res in self._resistance_results:
            if res is None:
                self._state = "ERROR"
                info("[CAL] Res. is None")
                return

        # reset nur selektierte Channels
        for ch in self._channel_idxs:
            self._beta[ch] = None
            self._ntc_coef[ch] = None

        # --- strikt rechnen ---
        for ch in self._channel_idxs:
            r0 = self._resistance_results[0][ch] #type:ignore
            r1 = self._resistance_results[1][ch] #type:ignore
            r2 = self._resistance_results[2][ch] #type:ignore

            if (
                r0 is None or r1 is None or r2 is None or
                r0 <= 0 or r1 <= 0 or r2 <= 0
            ):
                info(f"[CAL] CH{ch}: invalid measurement")
                self._state = "ERROR"
                return

            if abs(r2 - r1) / r1 < 0.02:
                info(f"[CAL] CH{ch}: delta too small")
                self._state = "ERROR"
                return

            beta_val = self._calc_beta(
                r1,
                self._ref_temps_K[1],
                r2,
                self._ref_temps_K[2],
            )

            coef_val = self._calc_steinhart(
                r0,
                self._ref_temps_K[0],
                r1,
                self._ref_temps_K[1],
                r2,
                self._ref_temps_K[2]
            )

            if beta_val is None or coef_val is None:
                info(f"[CAL] CH{ch}: calc failed")
                self._state = "ERROR"
                return

            self._beta[ch] = beta_val #type:ignore
            self._ntc_coef[ch] = coef_val

        self._state = "DONE"

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
            def fmt_list(lst):
                out = []
                for v in lst:
                    if v is None:
                        out.append("None")
                    else:
                        out.append("{:.6e}".format(v))
                return ", ".join(out)

            # A/B/C extrahieren
            A = []
            B = []
            C = []

            for coef in self._ntc_coef:
                if coef is None:
                    A.append(None)
                    B.append(None)
                    C.append(None)
                else:
                    a, b, c = coef #type:ignore
                    A.append(a)
                    B.append(b)
                    C.append(c)

            with open(path, "w") as f:
                f.write("SH_A = " + fmt_list(A) + "\n")
                f.write("SH_B = " + fmt_list(B) + "\n")
                f.write("SH_C = " + fmt_list(C) + "\n")

            return True

        except Exception as e:
            print("Save error:", e)
            return False