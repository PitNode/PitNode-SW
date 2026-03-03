# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

from machine import ADC, SoftSPI, Pin, PWM, reset, unique_id
import network
import pitnode.driver.max6675 as max6675
import pitnode.driver.hw_config as hw_cfg

#for pin in hw_cfg.GPIO_PINS:
#   Pin(pin, Pin.IN, Pin.PULL_DOWN)

# SPI2 configuration
#SPI2 = SoftSPI(baudrate=100_000, polarity=1,
#               phase=0, sck=Pin(hw_cfg.PIN_SPI2_CLK),
#               mosi=Pin(hw_cfg.PIN_SPI2_MOSI), miso=Pin(hw_cfg.PIN_SPI2_MISO))

class RPiPico:
    _adc_list = [ADC(pin) for pin in hw_cfg.PROBE_PINS]
    _buzzer = PWM(Pin(hw_cfg.PIN_BUZZER), freq=4000, duty_u16=0)
    _spi_tc_sensor = SoftSPI(baudrate=500_000,
                             sck=Pin(hw_cfg.PIN_SPI2_CLK),
                             mosi=Pin(hw_cfg.PIN_SPI2_MOSI),
                             miso=Pin(hw_cfg.PIN_SPI2_MISO))
    _pincs = Pin(hw_cfg.PIN_K_PROBE_CS, Pin.OUT, value=1, pull=Pin.PULL_UP)
    #wifi_driver = PicoWiFiDriver()
    _wlan = network.WLAN(network.STA_IF)
    _wlan.active(False)
    wlan_cfg_path  = "."
    num_probe_channels = hw_cfg.PROBE_CHANNELS

    @classmethod
    def wlan(cls):
        return cls._wlan

    @classmethod
    def read_raw(cls) -> list[int]:
        return [adc.read_u16() for adc in cls._adc_list]

    @classmethod
    def read_tc(cls) -> float | None:
        return max6675.read_max6675(cls._spi_tc_sensor, cls._pincs)

    @classmethod
    def buzzer_on(cls):
        cls._buzzer.duty_u16(32000)

    @classmethod
    def buzzer_off(cls):
        cls._buzzer.duty_u16(0)

    @classmethod
    def reboot(cls):
        reset()
    
    @classmethod
    def unique_id(cls):
        return unique_id()
