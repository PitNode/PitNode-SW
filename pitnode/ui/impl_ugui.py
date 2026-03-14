# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import gc

import gui.touch_setup as touch_setup
import pitnode.ui.ugui_app.screen_measure as screen_measure

async def start_gui(app):
    gc.collect()
    await screen_measure.start_gui(app._presenter)
