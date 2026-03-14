# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

try:
    from micropython import const  # type: ignore
except ImportError:

    def const(x):
        return x

BASE_PATH = "."

# Init HW
GPIO_PINS = (
    0,
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    10,
    11,
    12,
    13,
    14,
    15,
    16,
    17,
    18,
    19,
    20,
    21,
    22,
    26,
    27,
    28,
)

# Number of probe channels
PROBE_CHANNELS = const(3)

# Number of K-Type channels
K_CHANNELS = const(1)

# Pins for probes
PROBE_PINS = (28, 27, 26)

# Series resistor values for ADC
R_SERIES_OHM = [47000, 47000, 47000]  # in Ohm

# Pins for SPI K-Type probe
PIN_K_PROBE_CS = const(21)

# Pins for SD-Card
PIN_SD_CS = const(19)

# Pins for LCD
PIN_LCD_DC = const(3)
PIN_LCD_RST = const(2)
PIN_LCD_CS = const(1)
PIN_LCD_CLK = const(6)
PIN_LCD_MOSI = const(7)
PIN_LCD_MISO = const(4)

# Pins for Touch
PIN_TOUCH_CS = const(13)
PIN_TOUCH_CLK = const(10)
PIN_TOUCH_MOSI = const(11)
PIN_TOUCH_MISO = const(12)

# Pins for SPI2 (SD-Card and K-Type probe)
PIN_SPI2_CLK = const(22)
PIN_SPI2_MOSI = const(18)
PIN_SPI2_MISO = const(20)

# Pins for buzzer
PIN_BUZZER = const(16)

# ADC configuration
V_ADC_REF_MV = const(3300)  # in mV

# Baudrate LCD SPI interface
LCD_BAUD = const(30_000_000)

# Baudrate Touch SPI interface
TOUCH_BAUD = const(2_500_000)

# LCD pixel size definition
LCD_WIDTH = const(320)
LCD_HEIGHT = const(240)

# Limits for ADS to detect open, short, invalid
ADC_MIN_MV = 20 # ADC almost 0
ADC_MAX_MV = V_ADC_REF_MV - 20
R_MAX_OHM = 1_000_000  # 1 MOhm
