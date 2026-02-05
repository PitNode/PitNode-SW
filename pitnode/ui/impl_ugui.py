# pitnode/ui/_impl.py   (uGUI Build)
import gc

import gui.touch_setup as touch_setup
import pitnode.ui.ugui_app.screen_measure as screen_measure
import pitnode.ui.ugui_app.screen_wifi
import pitnode.ui.ugui_app.screen_config


async def start_gui(app):
    gc.collect()
    await screen_measure.start_gui(app.presenter)  # blockiert
