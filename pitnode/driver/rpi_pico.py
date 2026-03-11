# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

from machine import ADC, SoftSPI, Pin, PWM, reset, unique_id
import network
import pitnode.driver.max6675 as max6675
from pitnode.driver.base_board import BaseBoard
#import pitnode.driver.hw_config as hw_cfg

#for pin in hw_cfg.GPIO_PINS:
#   Pin(pin, Pin.IN, Pin.PULL_DOWN)

class RPiPico(BaseBoard):
    def __init__(self, hw_cfg) -> None:
        super().__init__(hw_cfg)

        self._adc_list = [ADC(pin) for pin in self._hw_cfg.PROBE_PINS]
        
        self._buzzer = PWM(
            Pin(self._hw_cfg.PIN_BUZZER),
            freq=4000,
            duty_u16=0
            )
        
        self._spi_tc_sensor = SoftSPI(
            baudrate=500_000,
            sck=Pin(self._hw_cfg.PIN_SPI2_CLK),
            mosi=Pin(self._hw_cfg.PIN_SPI2_MOSI),
            miso=Pin(self._hw_cfg.PIN_SPI2_MISO))
        
        self._pincs = Pin(
            self.hw_cfg.PIN_K_PROBE_CS,
            Pin.OUT,
            value=1,
            pull=Pin.PULL_UP
            )
        
        self._wlan = network.WLAN(network.STA_IF)
        self._wlan.active(False)
        
        self.wlan_cfg_path  = "."

    @property
    def num_probe_channels(self):
        return self._hw_cfg.PROBE_CHANNELS

    @property
    def hw_cfg(self):
        return self._hw_cfg

    def wlan(self):
        return self._wlan

    def read_raw(self) -> list[int]:
        return [adc.read_u16() for adc in self._adc_list]

    def read_tc(self) -> float | None:
        return max6675.read_max6675(self._spi_tc_sensor, self._pincs)

    def buzzer_on(self):
        self._buzzer.duty_u16(32000)

    def buzzer_off(self):
        self._buzzer.duty_u16(0)

    def reboot(self):
        reset()
    
    def unique_id(self):
        return unique_id()
