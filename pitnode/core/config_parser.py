# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

from math import log, exp

class ConfigError(Exception):
    pass


class Config:
    SCHEMA = {
        "BOARD": (str, True, None), 
        "UNIT": (str, True, None),

        # NEU
        "PROBE_MODEL": (str, False, "BETA"),

        # Beta Mode
        "T_NTC_0_MK": (list, False, None),
        "BETA_K": (list, False, None),
        "R_NTC_0_OHM": (list, False, None),

        # Steinhart-Hart Mode
        "SH_A": (list, False, None),
        "SH_B": (list, False, None),
        "SH_C": (list, False, None),

        "PROBES": (list, True, None),
        "ENABLE_WIFI": (bool, False, True),
        "DEV_MODE": (bool, False, False),
        "WEB_PORT": (int, False, 80),
        "WEB_PORT_DEV": (int, False, 8080),
    }

    def __init__(self, path="/config.txt", cal_path="/calibration.txt"):
        self._config_path = path
        self._cal_path = cal_path
        self._load()
        self._load_calibration_override()
        self._apply_defaults()
        self._validate()

    # API
    @property
    def num_channels(self):
        if self.PROBE_MODEL == "BETA":
            return len(self.T_NTC_0_MK) #type:ignore
        else:
            return len(self.SH_A)

    # Helper functions
    def get_sh_coeff(self):
        if self.PROBE_MODEL == "SH":
            return self.SH_A, self.SH_B, self.SH_C

        elif self.PROBE_MODEL == "BETA":
            A_list, B_list, C_list = [], [], []

            for ch in range(len(self.BETA_K)): #type:ignore
                A, B, C = self.beta_to_sh(
                    R0=self.R_NTC_0_OHM[ch], #type:ignore
                    T0=self.T_NTC_0_MK[ch] / 1000, #type:ignore
                    beta=self.BETA_K[ch] #type:ignore
                )
                A_list.append(A)
                B_list.append(B)
                C_list.append(C)

            return A_list, B_list, C_list

    def calc_steinhart(self, R1, T1, R2, T2, R3, T3):
        L1, L2, L3 = log(R1), log(R2), log(R3)
        Y1, Y2, Y3 = 1/T1, 1/T2, 1/T3

        g2 = (Y2 - Y1) / (L2 - L1)
        g3 = (Y3 - Y1) / (L3 - L1)

        C = (g3 - g2) / (L3 - L2) / (L1 + L2 + L3)
        B = g2 - C * (L1**2 + L1*L2 + L2**2)
        A = Y1 - (B + C * L1**2) * L1
        return A, B, C

    def beta_to_sh(self, R0, T0, beta):
        """
        R0: Widerstand bei T0 (Ohm)
        T0: Referenztemperatur (Kelvin)
        beta: Beta-Wert (Kelvin)
        """

        # Zieltemperaturen
        T1 = 273.15   # 0°C
        T2 = T0       # z. B. 25°C
        T3 = 373.15   # 100°C

        # Widerstände berechnen
        def R(T):
            return R0 * exp(beta * (1/T - 1/T0))

        R1 = R(T1)
        R2 = R(T2)  # = R0
        R3 = R(T3)

        # Steinhart-Hart berechnen (deine korrigierte Version!)
        return self.calc_steinhart(R1, T1, R2, T2, R3, T3)

    # LOAD
    def _load(self):
        try:
            with open(self._config_path) as f:
                for line in f:
                    line = line.strip()

                    if not line or line.startswith("#"):
                        continue

                    if "=" not in line:
                        raise ConfigError("Invalid line: {}".format(line))

                    key, value = [x.strip() for x in line.split("=", 1)]

                    if key not in self.SCHEMA:
                        raise ConfigError("Unknown config key: {}".format(key))

                    expected_type, _, _ = self.SCHEMA[key]

                    parsed = self._parse_value(value, expected_type)

                    setattr(self, key, parsed)

        except OSError:
            raise ConfigError("Config file not found")

    def _load_calibration_override(self):
        try:
            with open(self._cal_path) as f:
                cal_data = {}

                for line in f:
                    line = line.strip()

                    if not line or line.startswith("#"):
                        continue

                    if "=" not in line:
                        continue

                    key, value = [x.strip() for x in line.split("=", 1)]

                    if key not in ("SH_A", "SH_B", "SH_C"):
                        continue

                    cal_data[key] = self._parse_value(value, list)

            # nur wenn zumindest teilweise vorhanden
            if not cal_data:
                return

            # Basis holen (wichtig!)
            base_A, base_B, base_C = self.get_sh_coeff() # type:ignore

            # Merge vorbereiten
            new_A = list(base_A)
            new_B = list(base_B)
            new_C = list(base_C)

            # pro Kanal überschreiben wenn vorhanden
            for i in range(len(new_A)):
                try:
                    if "SH_A" in cal_data and cal_data["SH_A"][i] is not None:
                        new_A[i] = cal_data["SH_A"][i]
                    if "SH_B" in cal_data and cal_data["SH_B"][i] is not None:
                        new_B[i] = cal_data["SH_B"][i]
                    if "SH_C" in cal_data and cal_data["SH_C"][i] is not None:
                        new_C[i] = cal_data["SH_C"][i]
                except IndexError:
                    # calibration file kürzer → ignorieren
                    pass

            # übernehmen
            self.SH_A = new_A
            self.SH_B = new_B
            self.SH_C = new_C
            self.PROBE_MODEL = "SH"

        except OSError:
            pass

    # VALUE PARSER
    def _parse_value(self, value, expected_type):
        
        value = value.replace("_", "")

        if expected_type == list:

            parts = [v.strip() for v in value.split(",")]

            parsed = []
            for p in parts:
                parsed.append(self._parse_scalar(p))

            return parsed

        return self._parse_scalar(value)

    def _parse_scalar(self, value):

        if value == "True":
            return True
        if value == "False":
            return False
        if value == "None":
            return None

        # int
        try:
            return int(value)
        except ValueError:
            pass

        # float
        try:
            return float(value)
        except ValueError:
            pass

        return value

    # DEFAULTS
    def _apply_defaults(self):

        for key, (_, required, default) in self.SCHEMA.items():

            if not hasattr(self, key):

                if required and default is None:
                    raise ConfigError("Missing required key: {}".format(key))

                setattr(self, key, default)

    # VALIDATION
    def _validate(self):

        model = getattr(self, "PROBE_MODEL", "BETA")

        if model == "BETA":

            if not all([
                self.T_NTC_0_MK, #type:ignore
                self.BETA_K, #type:ignore
                self.R_NTC_0_OHM #type:ignore
            ]):
                raise ConfigError("Missing Beta parameters")

            if len(self.T_NTC_0_MK) != len(self.BETA_K): #type:ignore
                raise ConfigError("Mismatch length")

            if len(self.T_NTC_0_MK) != len(self.R_NTC_0_OHM): #type:ignore
                raise ConfigError("Mismatch length")

        elif model == "SH":

            if not all([
                self.SH_A,
                self.SH_B,
                self.SH_C
            ]):
                raise ConfigError("Missing Steinhart-Hart parameters")

            if len(self.SH_A) != len(self.SH_B):
                raise ConfigError("Mismatch length")

            if len(self.SH_A) != len(self.SH_C):
                raise ConfigError("Mismatch length")

        else:
            raise ConfigError(f"Unknown PROBE_MODEL: {model}")


class HWConfig:
    SCHEMA = {
        # --- probe ---
        "PROBE_CHANNELS": (int, True, None),
        "K_CHANNELS": (int, False, 0),
        "PROBE_PINS": (list, True, None),
        "R_SERIES_OHM": (list, True, None),

        # --- LCD ---
        "PIN_LCD_DC": (int, True, None),
        "PIN_LCD_RST": (int, True, None),
        "PIN_LCD_CS": (int, True, None),
        "PIN_LCD_CLK": (int, True, None),
        "PIN_LCD_MOSI": (int, True, None),
        "PIN_LCD_MISO": (int, True, None),

        # --- Touch ---
        "PIN_TOUCH_CS": (int, True, None),
        "PIN_TOUCH_CLK": (int, True, None),
        "PIN_TOUCH_MOSI": (int, True, None),
        "PIN_TOUCH_MISO": (int, True, None),

        # --- K-Type ---
        "PIN_K_PROBE_CS": (int, True, None),

        # --- SPI2 ---
        "PIN_SPI2_CLK": (int, True, None),
        "PIN_SPI2_MOSI": (int, True, None),
        "PIN_SPI2_MISO": (int, True, None),

        # --- Buzzer ---
        "PIN_BUZZER": (int, True, None),

        # --- ADC ---
        "V_REF_MV": (int, True, None),
        "ADC_MIN_RAW": (int, False, 100),
        "ADC_MAX_RAW": (int, False, 65000),
        "R_MAX_OHM": (int, False, 1_000_000),

        # --- SPI Speed ---
        "LCD_BAUD": (int, False, 30_000_000),
        "TOUCH_BAUD": (int, False, 2_500_000),

        # --- LCD Geometry ---
        "LCD_WIDTH": (int, False, 320),
        "LCD_HEIGHT": (int, False, 240),
    }

    def __init__(self, path="/pitnode/hw_config/pitnode_pico_touch_config.txt"):
        self._hw_config_path = path
        self._load()
        self._apply_defaults()
        self._validate()

    # LOAD
    def _load(self):

        try:
            with open(self._hw_config_path) as f:
                for line in f:

                    line = line.strip()

                    if not line or line.startswith("#"):
                        continue

                    if "=" not in line:
                        raise ConfigError("Invalid line: {}".format(line))

                    key, value = [x.strip() for x in line.split("=", 1)]

                    if key not in self.SCHEMA:
                        raise ConfigError("Unknown config key: {}".format(key))

                    parsed = self._parse_value(value)
                    setattr(self, key, parsed)

        except OSError:
            raise ConfigError("Config file not found")

    # VALUE PARSER
    def _parse_value(self, value):

        value = value.replace("_", "")  # erlaubt 1_000_000

        if "," in value:
            return [int(v.strip()) for v in value.split(",")]
        else:
            return int(value)

    # DEFAULTS
    def _apply_defaults(self):

        for key, (_, required, default) in self.SCHEMA.items():

            if not hasattr(self, key):

                if required and default is None:
                    raise ConfigError("Missing required key: {}".format(key))

                setattr(self, key, default)

    # VALIDATION
    def _validate(self):

        # Channel consistency
        if self.PROBE_CHANNELS != len(self.PROBE_PINS): #type:ignore
            raise ConfigError("PROBE_CHANNELS mismatch PROBE_PINS")

        if self.PROBE_CHANNELS != len(self.R_SERIES_OHM): #type:ignore
            raise ConfigError("PROBE_CHANNELS mismatch R_SERIES_OHM")

        # Pin sanity
        all_pins = self.PROBE_PINS + [ #type:ignore
            self.PIN_LCD_DC, #type:ignore
            self.PIN_LCD_RST, #type:ignore
            self.PIN_LCD_CS, #type:ignore
            self.PIN_LCD_CLK, #type:ignore
            self.PIN_LCD_MOSI, #type:ignore
            self.PIN_LCD_MISO, #type:ignore
            self.PIN_TOUCH_CS, #type:ignore
            self.PIN_TOUCH_CLK, #type:ignore
            self.PIN_TOUCH_MOSI, #type:ignore
            self.PIN_TOUCH_MISO, #type:ignore
            self.PIN_SPI2_CLK, #type:ignore
            self.PIN_SPI2_MOSI, #type:ignore
            self.PIN_SPI2_MISO, #type:ignore
            self.PIN_BUZZER, #type:ignore
        ]

        if len(all_pins) != len(set(all_pins)):
            raise ConfigError("Duplicate GPIO pin detected")

        # ADC limits
        if not (0 < self.ADC_MIN_RAW < self.ADC_MAX_RAW): #type:ignore
            raise ConfigError("Invalid ADC limits")

        # SPI sanity
        if self.LCD_BAUD <= 0 or self.TOUCH_BAUD <= 0: #type:ignore
            raise ConfigError("Invalid SPI baudrate")

        # LCD geometry
        if self.LCD_WIDTH <= 0 or self.LCD_HEIGHT <= 0: #type:ignore
            raise ConfigError("Invalid LCD size")