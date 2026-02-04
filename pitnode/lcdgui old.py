# Based on templates from Peter Hinch's micro-gui
# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2019-2021 Peter Hinch

# Created on Sun Jan 18 2026
# All original firmware source code developed as part of the PitNode project
# is licensed under the:
# GNU Affero General Public License v3.0 or later (AGPL-3.0-or-later)
# Copyright (c) 2026 Philipp Geisseler

#ToDos
# Confirm alarm
# Delay between Set Target Temp and alarm to make sute that alarm
# is not triggered while setting target temp.
# Character ° to include in small font
# Refactoring: Own class for measurement handling including alarms
# Separte GUI update from measure class
# Split GUI build into different functions inside class
# Repleace CH-<n> by only number maybe in an inverted color schema
# Check for mp RAM optimization.

import touch_setup as touch_setup  # Instantiate display, setup color LUT (if present)
from gui.core.tgui import Screen, ssd

import asyncio

from gui.core.writer import CWriter
from gui.widgets import Label, Button

# Font for CWriter
import gui.fonts.freesans_ext_25 as freesans_ext_25
import gui.fonts.freesans20 as freesans20
from gui.core.colors import *
from pitnode.config import *
from pitnode.ui.presenter import PitNodePresenter as Pres

# GUI definitions
BG_COLOR = BLACK # Background color
LINE_COLOR = GREY # Color of GUI lines
CH_COLORS = [YELLOW, GREEN, MAGENTA]
CH_SPACING = int((ssd.height - (HEADER_H + 2)) / CH_PPAGE)

async def update_temps(lbls):
   """Updates temperature on GUI"""
   while True:
      # Update GUI
      for ch, label in enumerate(lbls):
         if Ctrl.is_temp_valid(ch):
            label.value(text=f"{Ctrl.get_temp(ch):,.2f} °C")
         else:
            label.value(text="--.-- °C")
      await asyncio.sleep(1.0)

async def trigger_alarm(lbls):
   """Triggers alarms"""
   invert = [False, False, False]
   while True:
      for idx, alarm in enumerate(Ctrl.alarms):
         if alarm:
            invert[idx] = not invert[idx]
            lbls[idx].value(invert=invert[idx])
         else:
            invert[idx] = False
            lbls[idx].value(invert=False)
      await asyncio.sleep(0.5)

class BaseScreen(Screen):
   """Base Class for GUI"""
   def __init__(self):
      super().__init__()
      #target_temp = Ctrl._probe_target_deg_c_value[]
      wri1 = CWriter(ssd, freesans_ext_25, GREEN, BLACK)
      wri2 = CWriter(ssd, freesans20, GREEN, BLACK)
      lblsmeas = []
      lblstrgt = []
      col1pos = CH_COL_START
      col2pos = CH_COL_START+COL1_W
      col3pos = CH_COL_START+COL1_W+COL2_W
      Button.long_press_time = 500
      self.btn_prev_long = [False, False, False]
      for i, _ in enumerate(Ctrl._probes):
         rowchtop = CH_ROW_START+i*CH_SPACING
         rowchmid = CH_ROW_START+i*CH_SPACING+int(CH_SPACING/2)
         Label(wri1,
               rowchtop+MARGIN_TB,
               col1pos, f"CH-{i+1}",
               fgcolor=CH_COLORS[i])
         lbltrgt = Label(wri2,
                         rowchtop+MARGIN_TB+freesans_ext_25.height()+4,
                         col2pos, f"Target: {Ctrl.get_temp(i)} °C",
                         fgcolor=CH_COLORS[i])
         lblstrgt.append(lbltrgt)
         lblmeas = Label(wri1,
                         rowchtop+MARGIN_TB,
                         col2pos, f"--.--    °C",
                         justify=Label.RIGHT,
                         fgcolor=CH_COLORS[i])
         lblsmeas.append(lblmeas)
         Button(wri1, rowchmid-15, col3pos, height=30, width=40,
                text="-", callback=self.set_target_temp, lp_callback=self.set_target_temp,
                fgcolor=CH_COLORS[i], args=(i,lbltrgt, 1), lp_args=(i,lbltrgt, 10),
                onrelease=True)
         Button(wri1, rowchmid-15, col3pos+60, height=30, width=40,
                text="+", callback=self.set_target_temp, lp_callback=self.set_target_temp,
                fgcolor=CH_COLORS[i], args=(i,lbltrgt, 1), lp_args=(i,lbltrgt, 10),
                onrelease=True)
         
      self.reg_task(update_temps(lblsmeas))
      self.reg_task(trigger_alarm(lblstrgt))

   def after_open(self):
      """Creates header area"""
      w = ssd.width
      ssd.hline(0, HEADER_H, w, LINE_COLOR)
      ssd.hline(0, HEADER_H+1, w, LINE_COLOR)
      for i in range(CH_PPAGE-1):
         rowpos = CH_ROW_START+((i+1)*CH_SPACING)
         ssd.hline(0, rowpos-MARGIN_TB, w, LINE_COLOR)

   def set_target_temp(self, button, ch, lbl, inc):
      """Sets the target temperature"""
      if button.text is "+":
         # Workaround to prevent button pressed after long press
         if self.btn_prev_long[ch] is True and inc == 1:
            self.btn_prev_long[ch] = False
         else:
            Ctrl.increase_target_temp(ch, inc)
         lbl.value(text=f"Target: {Ctrl._probe_target_deg_c_value[ch]} °C")
      else:
         # Workaround to prevent button pressed after long press
         if self.btn_prev_long[ch] is True and inc == 1:
            self.btn_prev_long[ch] = False
         else:
            Ctrl.decrease_target_temp(ch, inc)
         lbl.value(text=f"Target: {Ctrl._probe_target_deg_c_value[ch]} °C")
      # Workaround to prevent button pressed after long press
      if inc > 1:
            self.btn_prev_long[ch] = True
      Ctrl.alarms[ch] = False

def start_gui():
    Screen.change(BaseScreen)

if __name__ == "__main__":
   start_gui()