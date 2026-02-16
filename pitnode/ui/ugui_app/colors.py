# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

from gui.core.colors import *  # Imports the create_color function

#PALE_YELLOW = create_color(12, 150, 150, 0)  # index, r, g, b
CH_1_RGB = [255, 255, 68]
CH_2_RGB = [98, 255, 98]
CH_3_RGB = [65, 65, 255]

DEF_BG             = SSD.rgb(18, 18, 20)      # #121214
TEXT_MAIN          = SSD.rgb(235, 235, 235)   # fast weiß
#TEXT_DIM           = SSD.rgb(120, 120, 125)
CH1_COL            = SSD.rgb(CH_1_RGB[0], CH_1_RGB[1], CH_1_RGB[2])
CH2_COL            = SSD.rgb(CH_2_RGB[0], CH_2_RGB[1], CH_2_RGB[2])
CH3_COL            = SSD.rgb(CH_3_RGB[0], CH_3_RGB[1], CH_3_RGB[2])
ACCENT_GRILL       = SSD.rgb(255, 140, 40)    # Orange
#GREEN_OK           = SSD.rgb(80, 220, 120)
#RED_OVER           = SSD.rgb(255, 80, 80)
DYNAMIC_PULSE_1    = SSD.rgb(235, 235, 235)
DYNAMIC_PULSE_2    = SSD.rgb(235, 235, 235)
DYNAMIC_PULSE_3    = SSD.rgb(235, 235, 235)

DIVIDER_1          = SSD.rgb(50, 50, 55)
DIVIDER_2          = SSD.rgb(30, 30, 35)

color_map[BG] = DEF_BG