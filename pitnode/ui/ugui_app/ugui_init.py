# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import gui.fonts.roboto_thin48_temp as font_lg_temp
import gui.fonts.roboto_thin26_red as font_md_red
import gui.fonts.roboto_thin18_ext as font_keyboard
import gui.fonts.icons as icons
from gui.core.tgui import ssd

from pitnode.ui.ugui_app.colors import *
from pitnode.driver.hw_config import LCD_WIDTH, LCD_HEIGHT, PROBE_CHANNELS

wrt_lg_temp = CWriter(ssd, font_lg_temp, TEXT_MAIN, DEF_BG, False)
wrt_md_red = CWriter(ssd, font_md_red, TEXT_MAIN, DEF_BG, False)
wrt_icon = CWriter(ssd, icons, TEXT_MAIN, DEF_BG, False)
wrt_keyboard = CWriter(ssd, font_keyboard, TEXT_MAIN, DEF_BG, False)

class UIPositions:
    lcd_width = LCD_WIDTH
    lcd_height = LCD_HEIGHT
    probe_channels = PROBE_CHANNELS
    header_height = const(40)
    margin = const(2)
    ch_width = const(106)
    ch_per_page = lcd_width // ch_width
    no_of_pages = round(probe_channels/ch_per_page)
    ch_start_row = header_height + 10
    ch_height = lcd_height - ch_start_row - margin
    ledbar_width = ch_width - 20
    ledbar_height = const(6)
    menu_row = 0 + margin
    menu_col = lcd_width - 80
    