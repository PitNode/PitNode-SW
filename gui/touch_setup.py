# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import gc
from drivers.ili93xx.ili9341_8bit import ILI9341 as SSD
from pitnode.driver.init_pitnode_pico_touch import hw

gc.collect()  # Precaution before instantiating framebuf
spi_lcd, pin_lcd_cs, pin_lcd_data, pin_lcd_rst, lcd_h, lcd_w = hw.spi_lcd
ssd = SSD(spi_lcd, pin_lcd_cs, pin_lcd_data, pin_lcd_rst, height=lcd_h, width=lcd_w, usd=False, bgr=False)
from gui.core.tgui import Display, quiet
quiet()  # Comment this out for periodic free RAM messages

# Touch configuration
from gui.touch.xpt2046 import XPT2046
spi_touch, pin_touch_cs = hw.spi_touch
tpad = XPT2046(spi_touch, pin_touch_cs, ssd)
tpad.init(240, 320, 336, 223, 3786, 3856, True, False, False)
display = Display(ssd, tpad)
