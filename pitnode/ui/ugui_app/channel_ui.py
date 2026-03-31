# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import gc

from gui.core.tgui import Screen, Window
from gui.widgets import Label, Button, Pad
from pitnode.ui.ugui_app.ugui_init import wrt_lg_temp, wrt_md_red, wrt_icon
from pitnode.ui.ugui_app.ugui_init import UIPositions as Pos
from pitnode.ui.ugui_app.colors import *
from pitnode.log.log import error, info
from pitnode.ui.ugui_app.widgets.led_bar import LEDBAR

class ChannelUI:
    def __init__(self, ch, presenter) -> None:
        self.temp_label = None
        self.target_label = None
        self.ch = ch
        self.ledbar = None
        self.presenter = presenter

    def ch_card(self, row, col, height, width, ch_color):
        ledbar_start_row = row+10
        card_col_middle = col + width // 2
        ledbar_start_col = card_col_middle - (Pos.ledbar_width //2)

        # CH marker
        self.ledbar = LEDBAR(wrt_md_red,
                             ledbar_start_row,
                             ledbar_start_col,
                             height=Pos.ledbar_height,
                             width=Pos.ledbar_width,
                             color=ch_color)
        self.ledbar.value(True)
        
        # Card
        btn=Pad(
            wrt_md_red,
            row,
            col,
            height=height,
            width=width,
            callback=self._on_channel
        )

        unit_label_width = 40
        unit_label_start_row = self.ledbar.mrow + 14
        unit_label_start_col = card_col_middle - unit_label_width//2
        # Unit
        lbl_meas_unit=Label(
            wrt_md_red,
            unit_label_start_row,
            unit_label_start_col,
            unit_label_width,
            justify=Label.CENTRE
        )

        lbl_meas_unit.value(self.presenter.unit)

        temp_label_width = 70
        temp_label_start_row = lbl_meas_unit.mrow + 10
        temp_label_start_col = card_col_middle - temp_label_width // 2        
        # Meas Temp
        lbl_meas=Label(
            wrt_lg_temp,
            temp_label_start_row,
            temp_label_start_col,
            temp_label_width,
            justify=Label.CENTRE,
        )
        self.temp_label = lbl_meas

        target_label_start_row = self.temp_label.mrow + 10
        target_label_start_col = card_col_middle - 80 // 2    
        # Target arrow
        lbl_arrow=Label(
            wrt_icon,
            target_label_start_row,
            target_label_start_col,
            "A",
        )

        # Target temp
        lbl_trgt=Label(
            wrt_md_red,
            target_label_start_row,
            lbl_arrow.mcol+4,
            50,
        )
        self.target_label = lbl_trgt
        self.target_label.value("--")

    def _on_channel(self, btn, *args):
        # Guard: active but NOT confirmed → only confirm
        if self.presenter.is_alarm_active(self.ch) and \
        not self.presenter.is_alarm_confirmed(self.ch):
            self.presenter.confirm_alarm(self.ch)
            return

        # Otherwise open target temp window
        Screen.change(
            TargetTempWindow,
            args=(10, 10, 220, 300, self.ch, self.presenter)
        )
    
class BBQchUI:
    def __init__(self, presenter) -> None:
        self.temp_label = None
        self.presenter = presenter

    def bbq_card(self, row, col):
        # Title
        lbl_bbq = Label(
            wrt_md_red,
            row,
            col,
            "BBQ: ",
            justify=Label.LEFT,
            fgcolor=ACCENT_GRILL
        )

        # BBQ Measurement
        lbl_bbq_meas=Label(
            wrt_md_red,
            row,
            lbl_bbq.mcol,
            60,
            justify=Label.LEFT,
            fgcolor=ACCENT_GRILL
        )
        self.temp_label = lbl_bbq_meas

        # BBQ unit
        lbl_meas_unit=Label(
            wrt_md_red,
            row,
            lbl_bbq_meas.mcol,
            self.presenter.unit,
            fgcolor=ACCENT_GRILL
        )
        return self

class TargetTempWindow(Window):
    def __init__(self, col, row, w, h, ch, presenter):
        self.presenter = presenter
        super().__init__(col, row, w, h, bgcolor=DEF_BG)

        def on_value(value):
            if value is not None:
                presenter.set_target_temp(ch, value)
            info(f"Target temperature: {value}")
            Screen.back()
        
        self.numpad = NumPad(
            wrt_md_red,
            wrt_md_red,
            row=10,
            col=10,
            initial=str(int(presenter.get_target(ch))),
            unit=self.presenter.unit,
            on_ok=on_value,
        )

class NumPad:
    """
    Reusable numeric keypad widget for uGUI (compatible with older versions).
    """
    def __init__(
        self,
        writer_pad,
        writer_lbl,
        row,
        col,
        *,
        initial="0",
        unit="",
        on_ok=None,
    ):
        self.writer_pad = writer_pad
        self.on_ok = on_ok
        self.unit = unit
        self.buf = str(initial)
        self._fresh = True

        # Temp
        self.label = Label(
            writer_lbl,
            row+60,
            col+10,
            60,
        )
        self.label.value(self.buf)
        # Unit
        Label(
            writer_pad,
            row+60,
            self.label.mcol+ 4,
            self.unit,
        )

        # Layout
        bw, bh = 45, 45
        gap = 5
        by = row + 40

        keys = (
            "7", "8", "9",
            "4", "5", "6",
            "1", "2", "3",
            "0", "<"
        )

        self.buttons = []

        for i, key in enumerate(keys):
            pad_col = i % 3
            pad_row = i // 3

            btn = Button(
                writer_pad,
                #by + row * (bh + gap),
                row + 16 + pad_row * (bh + gap),
                col + 130 + pad_col * (bw + gap),
                text=key,
                width=bw,
                height=bh,
                shape=CLIPPED_RECT,
                callback=self._make_key_cb(key),
            )
            self.buttons.append(btn)

        # OK button
        self.ok_btn = Button(
            writer_pad,
            120,
            26,
            text="OK",
            width=80,
            height=bh,
            shape=CLIPPED_RECT,
            callback=self._ok,
        )

    def _make_key_cb(self, key):
        def cb(btn):
            # First key press overwrites initial value
            if self._fresh:
                self.buf = "0"
                self._fresh = False

            if key == "<":
                self.buf = self.buf[:-1] or "0"
            else:
                if len(self.buf) >= 3:
                    return

                if self.buf == "0":
                    self.buf = ""

                self.buf += key

            self.label.value(self.buf)
        return cb


    def _update_label(self):
        self.label.value(self.buf)

    def _on_key(self, key):
        if key == "C":
            self.buf = ""
        elif key == "OK":
            if self.on_ok:
                self.on_ok(self.value) # type:ignore
            return
        else:
            self.buf += key

        self.label.value(self.buf + self.unit)

    def _ok(self, btn):
        try:
            value = int(self.buf)
        except ValueError:
            return

        if self.on_ok:
            self.on_ok(value)
