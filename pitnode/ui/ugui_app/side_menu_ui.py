import asyncio

from gui.core.tgui import Screen, Window
from gui.widgets import Label, Button
from pitnode.ui.ugui_app.ugui_init import wrt_icon
from gui.core.colors import *
from pitnode.ui.ugui_app.screen_config import ConfigScreen
from pitnode.log.log import error, info

class SideMenu:
    def __init__(self, presenter, screen) -> None:
        self.presenter = presenter
        self.screen = screen
        row=2
        col=200
        
        lbl_wifi = Label(
            wrt_icon,
            row,
            col,
            "D", # Wifi Icon
        )
        self.wifi_label = lbl_wifi

        btn_cfg = Button(
            wrt_icon,
            row,
            lbl_wifi.mcol+4,
            text="B",
            callback=self._config_screen,
            height=40,
            width=40
        )
        self.config_button = btn_cfg

        self.screen.reg_task(self._update_status(), on_change=False)

    async def _update_status(self):
        try:
            last_wifi = None
            while True:
                status = self.presenter.get_status()
                if status:
                    wifi = status.wifi_connected
                    if wifi != last_wifi:
                        self.wifi_label.value(
                            fgcolor=GREEN if wifi else GREY
                        )
                        last_wifi = wifi
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            info("[GUI] Status update task stopped")
            raise

    def _config_screen(self, _):
        ConfigScreen.set_presenter(self.presenter)
        Screen.change(ConfigScreen)