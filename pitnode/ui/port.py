# pitnode/ui/port.py
from pitnode.ui.impl_ugui import start_gui

import asyncio
from pitnode.app.app import App
from pitnode.core.controller import PitNodeCtrl as Ctrl
from pitnode.driver.rpi_pico import RPiPico


async def start_ui():
    Ctrl.hw = RPiPico  # type: ignore

    app = App()
    await app.start()

    # Übergabe an GUI-Implementation
    await start_gui(app)
