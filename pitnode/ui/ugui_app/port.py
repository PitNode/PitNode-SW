# pitnode/ui/ugui/port.py
import gc

import gui.touch_setup as touch_setup
import pitnode.ui.ugui_app.ugui_init
import pitnode.ui.ugui_app.screen_measure as screen_measure
import pitnode.ui.ugui_app.screen_wifi
import pitnode.ui.ugui_app.screen_config

async def _start_gui(app):
    gc.collect()
    # This call never returns – and that's OK
    await screen_measure.start_gui(app.presenter)
