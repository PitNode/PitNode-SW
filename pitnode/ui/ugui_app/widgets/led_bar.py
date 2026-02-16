# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2021 Peter Hinch

# Base class from Peter Hinch modified to get led bar

from gui.core.tgui import Widget, display
from gui.core.colors import *


class LEDBAR(Widget):
    def __init__(
        self, writer, row, col, *, height=10, width=30, fgcolor=None, bgcolor=None, bdcolor=False, color=RED
    ):
        super().__init__(writer, row, col, height, width, fgcolor, bgcolor, bdcolor, False)
        self._value = False
        self._color = color
        self.x = col
        self.y = row

    def show(self):
        if super().show():  # Draw or erase border
            color = self._color if self._value else BLACK
            display.fill_rect(int(self.x), int(self.y), self.width, self.height, color)

    def color(self, color):
        self._color = color
        self.draw = True