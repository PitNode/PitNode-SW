# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import time
import asyncio

from gui.core.tgui import Screen, ssd
from gui.core.writer import CWriter
from gui.widgets import Label, Button, CloseButton, Pad, Dropdown, Grid
from gui.core.colors import *

from pitnode.ui.ugui_app.ugui_init import wrt_icon, wrt_keyboard
from pitnode.storage.secrets import save_password
import config as cfg
from pitnode.log.log import error, info

class WLANsetupScreen(Screen):
    
    presenter = None

    @classmethod
    def set_presenter(cls, presenter):
        cls.presenter = presenter

    def __init__(self):

        super().__init__()
        assert self.presenter is not None # type: ignore
        
        col = 10
        row = 46
        self.rows = 4  # Grid dimensions in cells
        self.cols = 10
        colwidth = 25  # Column width

        Label(wrt_keyboard, 10, 10, f"Enter WLAN PW")
        
        self.grid = Grid(wrt_keyboard, row, col, colwidth, self.rows, self.cols, justify=Label.CENTRE)
        self.populate(self.grid, 0)
        self.grid[0, 0] = {"bgcolor": RED}  # Initial grid currency
        self.last = (0, 0)  # Last cell touched
        ch = round((gh := self.grid.height) / self.rows)  # Height & width of a cell
        cw = round((gw := self.grid.width) / self.cols)
        self.pad = Pad(wrt_keyboard, row, col, height=gh, width=gw, callback=self.adjust, args=(ch, cw))
        row = self.grid.mrow + 5
        els = ("lower", "upper", "symbols")
        dd = Dropdown(wrt_keyboard, row, col, elements=els, callback=self.ddcb, bdcolor=YELLOW)
        b = Button(wrt_keyboard, row, dd.mcol + 5, text="Space", callback=self.space, bdcolor=WHITE)
        b = Button(wrt_keyboard, row, b.mcol + 5, text="bsp", callback=self.bsp, bdcolor=WHITE)

        self.lbltxt = Label(wrt_keyboard, 174, col, text=ssd.width - col - 10, fgcolor=WHITE, bdcolor=False)
        self.lbltxt.value("")

        Button(wrt_keyboard, 208, col, text= "OK", callback=self.on_ok, bdcolor=WHITE)
        Label(wrt_keyboard, 208, col+64, self.presenter.get_selected_ssid())
        CloseButton(wrt_keyboard)

    def on_ok(self, _):
        Label(wrt_keyboard, 100, 10, text="Rebooting in 3 seconds...", fgcolor=WHITE, bgcolor=RED, bdcolor=False)
        if not cfg.DEV_MODE:
            save_password(self.lbltxt.value()[:-1])
        asyncio.create_task(self._delayed_reboot())

    async def _delayed_reboot(self):
        await asyncio.sleep(3)
        self.presenter.request_reboot() #type:ignore

    def adjust(self, pad, ch, cw):
        g = self.grid
        crl, ccl = self.last  # Remove highlight from previous currency
        g[crl, ccl] = {"bgcolor": BLACK}

        cr = pad.rr // ch  # Get grid coordinates of current touch
        cc = pad.rc // cw
        cl = next(g[cr, cc])  # Touched Label
        self.lbltxt.value("".join((self.lbltxt.value()[:-1], cl(), "_")))
        g[cr, cc] = {"bgcolor": RED}  # Highlight
        self.last = (cr, cc)

    def ddcb(self, dd):
        self.populate(self.grid, dd.value())

    def space(self, _):
        self.lbltxt.value("".join((self.lbltxt.value()[:-1], " _")))

    def bsp(self, _):
        v = self.lbltxt.value().rstrip("_")
        if len(v) > 0:
            v = v[:-1]
        self.lbltxt.value(v + "_")

    def populate(self, g, level):
        if level == 0:
            g[0, 0:10] = iter("1234567890")
            g[1, 0:10] = iter("qwertyuiop")
            g[2, 0:10] = iter("asdfghjkl;")
            g[3, 0:10] = iter("zxcvbnm,./")
        elif level == 1:
            g[0, 0:10] = iter("1234567890")
            g[1, 0:10] = iter("QWERTYUIOP")
            g[2, 0:10] = iter("ASDFGHJKL;")
            g[3, 0:9] = iter("ZXCVBNM,.")
            g[3, 9] = "sp"  # Special char: space
        else:
            g[0, 0:10] = iter('!"£$%^&*()')
            g[1, 0:10] = iter(";:@'#<>?/\\")
            g[2, 0:10] = iter(",.-_+=[]{}")
            g[3, 0:10] = iter("°μπωϕθαβγδ")

    def on_hide(self):
        #import sys, gc
        #if "gui.fonts.freesans20_ext" in sys.modules:
        #    del sys.modules["gui.fonts.freesans20_ext"]
        #    info("Keyboard font removed")
        #gc.collect()
        pass