# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import gui.fonts.roboto_thin48_temp as font_lg_temp
import gui.fonts.roboto_thin26_red as font_md_red
import gui.fonts.freesans20_ext as font_keyboard
import gui.fonts.icons as icons

from gui.core.colors import *
from pitnode.ui.ugui_app.colors import *
from gui.core.tgui import ssd

wrt_lg_temp = CWriter(ssd, font_lg_temp, TEXT_MAIN, BG, False)
wrt_md_red = CWriter(ssd, font_md_red, TEXT_MAIN, BG, False)
wrt_icon = CWriter(ssd, icons, TEXT_MAIN, BG, False)
wrt_keyboard = CWriter(ssd, font_keyboard, TEXT_MAIN, BG, False)