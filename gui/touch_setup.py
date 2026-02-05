# ili9341_xpt2046_pico.py

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2021-2024 Peter Hinch

from machine import Pin, SPI
import gc
from drivers.ili93xx.ili9341 import ILI9341 as SSD
import pitnode.driver.hw_config as hw_cfg

#freq(250_000_000)  # RP2 overclock
# Create and export an SSD instance

# Pins for LCD
pdc = Pin(hw_cfg.PIN_LCD_DC, Pin.OUT, value=0)
prst = Pin(hw_cfg.PIN_LCD_RST, Pin.OUT, value=1)
pcs = Pin(hw_cfg.PIN_LCD_CS, Pin.OUT, value=1)
# Pins for Touch
ptscs = Pin(hw_cfg.PIN_TOUCH_CS, Pin.OUT, value=1)

spi0 = SPI(0,
           sck=Pin(hw_cfg.PIN_LCD_CLK),
           mosi=Pin(hw_cfg.PIN_LCD_MOSI),
           miso=Pin(hw_cfg.PIN_LCD_MISO),
           baudrate=hw_cfg.LCD_BAUD)

spi1 = SPI(1,
           sck=Pin(hw_cfg.PIN_TOUCH_CLK),
           mosi=Pin(hw_cfg.PIN_TOUCH_MOSI),
           miso=Pin(hw_cfg.PIN_TOUCH_MISO),
           baudrate=hw_cfg.TOUCH_BAUD)

gc.collect()  # Precaution before instantiating framebuf

ssd = SSD(spi0, pcs, pdc, prst, height=hw_cfg.LCD_HEIGHT, width=hw_cfg.LCD_WIDTH, usd=False)
from gui.core.tgui import Display, quiet
quiet()  # Comment this out for periodic free RAM messages

# Touch configuration
from gui.touch.xpt2046 import XPT2046
tpad = XPT2046(spi1, ptscs, ssd)
# To create a tpad.init line for your displays please read SETUP.md
tpad.init(240, 320, 336, 223, 3786, 3856, True, False, False)
display = Display(ssd, tpad)
