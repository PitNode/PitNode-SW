# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

from machine import ADC, SoftSPI, Pin, PWM, SPI, reset, unique_id
import network
import pitnode.driver.max6675 as max6675
from pitnode.driver.base_board import BaseBoard
from pitnode.core.config_parser import HWConfig

#for pin in hw_cfg.GPIO_PINS:
#   Pin(pin, Pin.IN, Pin.PULL_DOWN)

class PicoTouch(BaseBoard):
    def __init__(self) -> None:
        self._hw_cfg = HWConfig(path="/pitnode/hw_config/pitnode_pico_touch_config.txt")
        self._uid = unique_id()
        
        Pin(17, Pin.OUT, value=0)
        
        self._adc_list = [ADC(pin) for pin in self._hw_cfg.PROBE_PINS] # type: ignore

        # Pins for Touch
        self._pin_touch_cs = Pin(self._hw_cfg.PIN_TOUCH_CS, Pin.OUT, value=1) # type: ignore

        # Pins for LCD
        self._pin_lcd_data = Pin(self._hw_cfg.PIN_LCD_DC, Pin.OUT, value=0) # type: ignore
        self._pin_lcd_rst = Pin(self._hw_cfg.PIN_LCD_RST, Pin.OUT, value=1) # type: ignore
        self._pin_lcd_cs = Pin(self._hw_cfg.PIN_LCD_CS, Pin.OUT, value=1) # type: ignore

        self._spi_lcd = SPI(0,
            sck=Pin(self._hw_cfg.PIN_LCD_CLK), # type: ignore
            mosi=Pin(self._hw_cfg.PIN_LCD_MOSI), # type: ignore
            miso=Pin(self._hw_cfg.PIN_LCD_MISO), # type: ignore
            baudrate=self._hw_cfg.LCD_BAUD) # type: ignore

        self._spi_touch = SPI(
            1,
            sck=Pin(self._hw_cfg.PIN_TOUCH_CLK), # type: ignore
            mosi=Pin(self._hw_cfg.PIN_TOUCH_MOSI), # type: ignore
            miso=Pin(self._hw_cfg.PIN_TOUCH_MISO), # type: ignore
            baudrate=self._hw_cfg.TOUCH_BAUD) # type: ignore

        self._buzzer = PWM(
            Pin(self._hw_cfg.PIN_BUZZER), # type: ignore
            freq=4000,
            duty_u16=0
            )
        
        self._spi_tc_sensor = SoftSPI(
            baudrate=500_000,
            sck=Pin(self._hw_cfg.PIN_SPI2_CLK), # type: ignore
            mosi=Pin(self._hw_cfg.PIN_SPI2_MOSI), # type: ignore
            miso=Pin(self._hw_cfg.PIN_SPI2_MISO) # type: ignore
            )
        
        self._pincs = Pin(
            self.hw_cfg.PIN_K_PROBE_CS, # type: ignore
            Pin.OUT,
            value=1,
            pull=Pin.PULL_UP
            )
        
        self._wlan = network.WLAN(network.STA_IF)
        self._wlan.active(False)
        
        self.wlan_cfg_path  = "/"

    @property
    def uid(self):
        return self._uid

    @property
    def num_probe_channels(self):
        return self._hw_cfg.PROBE_CHANNELS # type: ignore

    @property
    def hw_cfg(self):
        return self._hw_cfg
    
    @property
    def spi_lcd(self):
        return self._spi_lcd, self._pin_lcd_cs, self._pin_lcd_data, self._pin_lcd_rst, self._hw_cfg.LCD_HEIGHT, self._hw_cfg.LCD_WIDTH #type:ignore
    
    @property
    def spi_touch(self):
        return self._spi_touch, self._pin_touch_cs

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
