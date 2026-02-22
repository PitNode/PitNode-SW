# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

from machine import SPI, Pin
import time

from pitnode.log.log import info, warn, error

def read_max6675(spi: SPI, cs: Pin) -> float | None:
    try:
        cs.off()
        time.sleep_us(10)
        raw = spi.read(2)
    finally:
        cs.on()

    value = (raw[0] << 8) | raw[1]

    # Bit D2 = TC open
    if value & 0x04:
        return None

    temp_raw = value >> 3
    return temp_raw * 0.25
