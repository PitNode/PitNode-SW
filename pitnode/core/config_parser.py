# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de


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

    def __init__(self, path="/config.txt"):
        self._config_path = path
        self._load()
        self._apply_defaults()
        self._validate()

    @property
    def num_channels(self):
        if self.PROBE_MODEL == "BETA":
            return len(self.T_NTC_0_MK)
        else:
            return len(self.SH_A)

    # -----------------------------------------------------
    # LOAD
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # VALUE PARSER
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # DEFAULTS
    # -----------------------------------------------------

    def _apply_defaults(self):

        for key, (_, required, default) in self.SCHEMA.items():

            if not hasattr(self, key):

                if required and default is None:
                    raise ConfigError("Missing required key: {}".format(key))

                setattr(self, key, default)

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    def _validate(self):

        model = getattr(self, "PROBE_MODEL", "BETA")

        if model == "BETA":

            if not all([
                self.T_NTC_0_MK,
                self.BETA_K,
                self.R_NTC_0_OHM
            ]):
                raise ConfigError("Missing Beta parameters")

            if len(self.T_NTC_0_MK) != len(self.BETA_K):
                raise ConfigError("Mismatch length")

            if len(self.T_NTC_0_MK) != len(self.R_NTC_0_OHM):
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
        self._postprocess()
        self._validate()

    # -----------------------------------------------------
    # LOAD
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # VALUE PARSER
    # -----------------------------------------------------

    def _parse_value(self, value):

        value = value.replace("_", "")  # erlaubt 1_000_000

        if "," in value:
            return [int(v.strip()) for v in value.split(",")]
        else:
            return int(value)

    # -----------------------------------------------------
    # DEFAULTS
    # -----------------------------------------------------

    def _apply_defaults(self):

        for key, (_, required, default) in self.SCHEMA.items():

            if not hasattr(self, key):

                if required and default is None:
                    raise ConfigError("Missing required key: {}".format(key))

                setattr(self, key, default)

    # -----------------------------------------------------
    # DERIVED VALUES
    # -----------------------------------------------------

    def _postprocess(self):

        # Derived ADC max
        #self.ADC_MAX_MV = self.V_ADC_REF_MV - 20 #type:ignore
        pass

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

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