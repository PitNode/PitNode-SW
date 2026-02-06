from gui.core.tgui import Screen, Window
from gui.widgets import Label, Button, CloseButton
from pitnode.ui.ugui_app.ugui_init import wrt_lg_temp, wrt_md_red, wrt_icon
from gui.core.colors import *

class ChannelUI:
    def __init__(self, ch, presenter) -> None:
        self.temp_label = None
        self.target_label = None
        self.ch = ch
        self.presenter = presenter

    def ch_card(self, row, col, fgcolor, bgcolor):
        f_lg_h = wrt_lg_temp.height
        
        # Card
        btn=Button(
            wrt_md_red,
            row,
            col,
            height=150,
            width=86,
            shape=CLIPPED_RECT,
            bdcolor=False,
            bgcolor=bgcolor,
            fgcolor=fgcolor,
            callback=self._on_channel
        )
        
        # Probe Icon
        lbl_head_meas=Label(
            wrt_icon,
            row+10,
            col+16,
            "C", # Icon thermometer
            fgcolor=fgcolor,
            bgcolor=bgcolor,
        )

        # Unit
        lbl_meas_unit=Label(
            wrt_md_red,
            row+14,
            col+44,
            "°C",
            fgcolor=fgcolor,
            bgcolor=bgcolor,
        )

        # Meas Temp
        lbl_meas=Label(
            wrt_lg_temp,
            lbl_head_meas.mrow + 2,
            col + 20,
            60,
            fgcolor=fgcolor,
            justify=Label.LEFT,
            bgcolor=bgcolor,
        )
        self.temp_label = lbl_meas

        # Target Icon
        lbl_head_trgt=Label(
            wrt_icon,
            row+80,
            col + 16,
            "A",
            fgcolor=fgcolor,
            bgcolor=bgcolor,
        )

        # Target unit
        lbl_unit_trgt=Label(
            wrt_md_red,
            row+80,
            col + 44,
            "°C",
            fgcolor=fgcolor,
            bgcolor=bgcolor,
        )
        self.target_unit_label = lbl_unit_trgt

        # Target temp
        lbl_trgt=Label(
            wrt_md_red,
            row + 110,
            col + 30,
            "----.--",
            fgcolor=fgcolor,
            bgcolor=bgcolor,
        )
        self.target_label = lbl_trgt

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
    def __init__(self) -> None:
        self.temp_label = None

    def bbq_card(self, row, col, fgcolor, bgcolor):
        
        # Card
        btn=Button(
            wrt_md_red,
            row, col,
            height=60,
            width=265,
            shape=CLIPPED_RECT,
            bdcolor=False,
            bgcolor=bgcolor,
            fgcolor=fgcolor,
        )

        # BBQ Icon
        lbl_icon_bbq=Label(
            wrt_icon,
            row + 4,
            col + 6,
            "E",
            fgcolor=fgcolor,
            bgcolor=bgcolor,
        )

        # BBQ Measurement
        lbl_bbq_meas=Label(
            wrt_lg_temp,
            row+20,
            col + 100,
            70,
            fgcolor=fgcolor,
            justify=Label.LEFT,
            bgcolor=bgcolor,
        )
        self.temp_label = lbl_bbq_meas

        # BBQ unit
        lbl_meas_unit=Label(
            wrt_md_red,
            row+20,
            col+190,
            "°C",
            fgcolor=fgcolor,
            bgcolor=bgcolor,
        )
        return self

class TargetTempWindow(Window):
    def __init__(self, col, row, w, h, ch, presenter):
        bgcolor = [MAGENTA, GREEN, BLUE]
        super().__init__(col, row, w, h, bgcolor=bgcolor[ch])

        def on_value(value):
            if value is not None:
                presenter.set_target_temp(ch, value)
            print("Target temperature:", value)
            Screen.back()

        self.numpad = NumPad(
            wrt_md_red,
            wrt_lg_temp,
            row=10,
            col=10,
            width=w - 20,
            initial=str(int(presenter.get_target(ch))),
            unit=" °C",
            on_ok=on_value,
            bgcolor=bgcolor[ch]
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
        width,
        *,
        initial="0",
        unit="",
        on_ok=None,
        bgcolor=BLACK
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
            col+24,
            60,
            bgcolor=bgcolor
        )
        self.label.value(self.buf)
        # Unit
        Label(
            writer_pad,
            row+60,
            self.label.mcol+ 4,
            self.unit,
            bgcolor=bgcolor
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
                bgcolor=bgcolor
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
            bgcolor=bgcolor
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
