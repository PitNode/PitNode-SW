# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de


try:
    from time import ticks_ms, ticks_diff, ticks_add #type:ignore
except ImportError:
    import time

    def ticks_ms():
        return int(time.monotonic() * 1000) #type:ignore

    def ticks_diff(a, b):
        return a - b
    
    def ticks_add(a, b):
        return a + b

try:
    import uasyncio as asyncio
    sleep_ms = asyncio.sleep_ms #type:ignore
except ImportError:
    import asyncio

    async def sleep_ms(ms: int):
        await asyncio.sleep(ms / 1000)

from pitnode.core.probe import ProbeState, OPEN_THRESHOLD, VALID_THRESHOLD, NtcProbe
from pitnode.core.sensor_eval import eval_resistance_raw
from pitnode.core.tc_filter import TcFilter
from pitnode.core.calibration import CalibrationWizard
from pitnode.log.log import info, warn, error


class PitNodeCtrl:
    """Class for controlling the PitNode"""
    def __init__(self, hw=None, cfg=None) -> None:
        self._hw = hw
        self._cfg = cfg
        self._probe_channels = hw.hw_cfg.PROBE_CHANNELS #type:ignore
        self._running = False
        self._tasks = []
        self._probes = [None] * self._probe_channels
        self._probe_raw_value = [0] * self._probe_channels
        self._probe_raw_valid = 0
        self._probe_mv_value = [0] * self._probe_channels
        self._probe_mv_valid = 0
        self._probe_deg_c_value = [0.0] * self._probe_channels
        self._probe_deg_c_valid = 0
        self._probe_resistance_value = [0] * self._probe_channels
        self._probe_resistance_valid = 0
        self._probe_state = [ProbeState.OPEN] * self._probe_channels
        self._tc_raw = 0
        self._tc_deg_c_value = None
        self._tc_deg_c_valid = 0
        self._tc_probe_state = ProbeState.OPEN
        self._tc_open_cnt = 0
        self._tc_valid_cnt = 0
        self._probe_target_deg_c_value = [50.0] * self._probe_channels
        self._probe_target_valid = 0b111
        self._alarms = [False] * self._probe_channels
        self._buzzer = False
        self._alarm_acked_flag = 0
        self._num_channels = self._probe_channels

    @property
    def num_probe_ch(self):
        return self._probe_channels

    @property
    def cfg(self):
        return self._cfg

    @property
    def hw(self):
        return self._hw

    @property
    def alarms(self):
        return self._alarms
     
    async def start_pitnode_ctrl(self):
        if self._running:
            return
        if not self._probes:
            return
        self._tc_filter = TcFilter()
        self._running = True
        self._tasks = [
            asyncio.create_task(self._measure_loop()),
            asyncio.create_task(self._alarm_task())
        ]

    async def stop_pitnode_ctrl(self):
        if not self._running:
            return
        self._running = False
        for t in self._tasks:
            try:
                await t
            except asyncio.CancelledError:
                pass
        self._tasks.clear()

    def register_probe(self, ch: int, probe) -> bool:
        """
        Register a probe to HW channel.
        Returns True if register was successful. Otherwise returns False.
        """
        if not _is_valid_channel(ch, self._probe_channels):
            warn("Invalid channel given to register_probe")
            return False

        if not _is_valid_probe(probe):
            warn("Invalid probe type given to register_probe")
            return False

        self._probes[ch] = probe
        return True

    def get_tc_temp(self):
        if not self._tc_deg_c_valid or self._tc_deg_c_value is None:
            return None
        t = self._tc_deg_c_value
        return t if self._cfg.UNIT == "cel" else (t * 9 / 5 + 32) #type:ignore
    
    def get_temp(self, ch: int) -> None | bool | float:
        """
        Return the temperature for given channel.
        Return False if channel invalid.
        Return None if tempeature is not valid.
        """

        if not _is_valid_channel(ch, self._probe_channels):
            warn("Invalid channel given to get_temp()")
            return False
        if not _is_valid_temp(self._probe_deg_c_valid, ch):
            warn("Temperature is not valid")
            return None
        t = self._probe_deg_c_value[ch]
        return t if self._cfg.UNIT == "cel" else (t * 9 / 5 + 32) #type:ignore

    def get_temps(self) -> list:
        """Return all temperatures as list."""
        temps = self._probe_deg_c_value
        return temps if self._cfg.UNIT == "cel" else ([(t * 9 / 5 + 32) for t in temps]) #type:ignore

    def get_probe_states(self) -> list:
        """Return all probe states as list."""
        return self._probe_state

    def get_tc_probe_state(self):
        """Return TC probe state."""
        return self._tc_probe_state

    def get_target_temp(self, ch: int) -> None | bool | float:
        """
        Return target temp of channel.
        Return False if ch invalid.
        Return None if target temp invalid
        """
        if not _is_valid_channel(ch, self._probe_channels):
            warn("Invalid channel given to get_target_temp()")
            return False
        if not _is_valid_target(self._probe_target_valid, ch):
            return None
        t = self._probe_target_deg_c_value[ch]
        return t if self._cfg.UNIT == "cel" else (t * 9 / 5 + 32) #type:ignore

    def get_target_temps(self) -> list:
        """Return all target temperatures as list."""
        return [self.get_target_temp(ch)
                for ch in range(len(self._probe_target_deg_c_value))]

    def is_temp_valid(self, ch: int) -> bool | None:
        """Return True if temperature is valid"""
        if not _is_valid_channel(ch, self._probe_channels):
            warn("Invalid channel given to is_temp_valid()")
            return None
        return _is_valid_temp(self._probe_deg_c_valid, ch)
    
    def _any_unacked_alarm(self) -> bool:
        for ch, active in enumerate(self.alarms):
            if active and not (self._alarm_acked_flag & (1 << ch)):
                return True
        return False

    def any_alarm_active(self):
        """Return True if an alarm is active."""
        return any(self.alarms)
    
    def is_alarm_active(self, ch: int) -> bool | None:
        """Return True if alarm of channel is active."""
        if not _is_valid_channel(ch, self._probe_channels):
            warn("Invalid channel given to is_alarm_active()")
            return None
        return self.alarms[ch]

    def is_alarm_confirmed(self, ch: int) -> bool | None:
        """Return True if alarm of channel is active and confirmed."""
        if not _is_valid_channel(ch, self._probe_channels):
            warn("Invalid channel given to is_alarm_confirmed()")
            return None
        if not self.alarms[ch]:
            return False
        return bool(self._alarm_acked_flag & (1 << ch))

    def confirm_alarm(self, ch: int):
        info(f"[CTRL] Confirm alarm received with ch {ch}")
        if not _is_valid_channel(ch, self._probe_channels):
            return False
        self._alarm_acked_flag |= 1 << ch
        return True

    def reset_alarms(self):
        """Reset all alarms."""
        self._alarms = [False] * self._num_channels

    def reset_alarm(self, ch: int):
        """
        Reset alarm of given channel.
        Returns None in case of invalid channel.
        """
        if not _is_valid_channel(ch, self._probe_channels):
            warn("Invalid channel given to reset_alarm()")
            return None
        self.alarms[ch] = False

    def set_target_temp(self, ch: int, temp: float | int) -> bool:
        """Return True if temperature was set successfully"""
        ch = int(ch)
        if ch < 0 or ch >= len(self._probe_target_deg_c_value):
            return False
        
        if not isinstance(temp, (int, float)):
            return False
    
        if self._cfg.UNIT == "cel": #type:ignore
            self._probe_target_deg_c_value[ch] = temp
        elif self._cfg.UNIT == "far": #type:ignore
            self._probe_target_deg_c_value[ch] = (temp - 32) * 5 / 9
        else:
            return False
        
        self._probe_target_valid |= 1 << ch
        return True

    def set_target_temps(self, values: list[float | int]) -> list[bool]:
        """Sets all target temperatures."""
        status = []
        for ch, temp in enumerate(values):
            status.append(self.set_target_temp(ch, temp))
        return status

    def increase_target_temp(self, ch: int, step: int) -> bool:
        """
        Return True if target temperature was incremented successfully.
        Otherwise False.
        """
        if not _is_valid_channel(ch, self._probe_channels):
            warn("Invalid channel given to increase_target_temp()")
            return False
        if not isinstance(step, int):
            warn("Stepsize for target temp is not int")
            return False
        
        # Reset confirm alarm flag
        self._alarm_acked_flag &= ~(1 << ch)

        step_c = step if self._cfg.UNIT == "cel" else step * 5 / 9 #type:ignore
        self._probe_target_deg_c_value[ch] += step_c
        self._probe_target_valid |= 1 << ch
        return True

    def decrease_target_temp(self, ch: int, step: int) -> bool:
        """
        Return True if target temperature was decremented successfully.
        Otherwise False.
        """
        if not _is_valid_channel(ch, self._probe_channels):
            warn("Invalid channel given to decrease_target_temp()")
            return False
        if not isinstance(step, int):
            warn("Stepsize for target temp is not int")
            return False
        
        # Reset confirm alarm flag
        self._alarm_acked_flag &= ~(1 << ch)

        step_c = step if self._cfg.UNIT == "cel" else step * 5 / 9 #type:ignore
        self._probe_target_deg_c_value[ch] -= step_c
        self._probe_target_valid |= 1 << ch
        return True

    def _eval_temp(self, ch: int) -> None:
        """Evaluates if target temperature is reached and sets alarm."""
        # measurement invalid → no alarm
        if not _is_valid_temp(self._probe_deg_c_valid, ch):
            self.alarms[ch] = False
            self._alarm_acked_flag &= ~(1 << ch)
            return
        # no target configured → no alarm
        if not _is_valid_target(self._probe_target_valid, ch):
            self.alarms[ch] = False
            self._alarm_acked_flag &= ~(1 << ch)
            return
        temp_meas = self._probe_deg_c_value[ch]
        temp_target = self._probe_target_deg_c_value[ch]
        if temp_meas >= temp_target:
            self.alarms[ch] = True
            # do NOT touch ack here
        else:
            self.alarms[ch] = False
            self._alarm_acked_flag &= ~(1 << ch)

    async def _alarm_task(self):
        try:
            while self._running:
                if self._any_unacked_alarm():
                    await self.trigger_buzzer()
                else:
                    if self.hw and self.hw._buzzer:
                        self.hw.buzzer_off()  # ensure silence
                await asyncio.sleep(0.5)
        finally:
            info("Controller alarm task stopped")
            if self.hw and self.hw._buzzer:
                self.hw.buzzer_off()

    async def trigger_buzzer(self):
        assert self.hw is not None, "HW not set"
        self.hw.buzzer_on()
        await asyncio.sleep(0.3)
        self.hw.buzzer_off()

    def read_tc_deg(self):
        assert self.hw is not None, error("HW not set")

        try:
            raw = self.hw.read_tc()
        except Exception:
            self._tc_probe_state = ProbeState.INVALID
            self._tc_deg_c_valid = 0
            return self._tc_deg_c_value

        filt = self._tc_filter 
        value = filt.update(raw)

        self._tc_probe_state = filt.state

        if filt.state == ProbeState.OK and value is not None:
            self._tc_deg_c_value = value
            self._tc_deg_c_valid = 1
        else:
            self._tc_deg_c_valid = 0

        return self._tc_deg_c_value


    def read_res_ohm(self):
        assert self.hw is not None, error("HW not set")
        self._probe_resistance_valid = 0

        res = [None] * self._probe_channels
        raw_values = self.hw.read_raw()

        for ch, (raw, r_series_ohm) in enumerate(
            zip(raw_values, self.hw.hw_cfg.R_SERIES_OHM) #type:ignore
        ):
            r_ntc_ohm, state = eval_resistance_raw(raw, r_series_ohm, self.hw.hw_cfg)
            self._probe_state[ch] = state

            if state is not ProbeState.OK:
                continue
            res[ch] = r_ntc_ohm
            self._probe_state[ch] = ProbeState.OK
            self._probe_resistance_value[ch] = r_ntc_ohm #type:ignore
            self._probe_resistance_valid |= 1 << ch
        return res

    async def _measure_loop(self):
        period_ms = 500
        next_t = ticks_ms()
        try:
            while self._running:
                now = ticks_ms()
                late = ticks_diff(now, next_t)
                if late > 50:   # z. B. 50 ms Toleranz
                    if self._cfg.DEV_MODE is True: #type:ignore
                        warn(f"Measurement late: {late} ms")
                try:
                    self._probe_deg_c_valid = 0
                    resistances = self.read_res_ohm()
                    self.read_tc_deg()
                    for ch, res in enumerate(resistances):
                        probe = self._probes[ch]
                        if probe is None:
                            continue

                        if self._probe_state[ch] != ProbeState.OK:
                            self._probe_deg_c_valid &= ~(1 << ch)
                            continue

                        self._probe_deg_c_value[ch] = probe.resistance_to_deg_c(res) #type:ignore
                        self._probe_deg_c_valid |= 1 << ch
                        self._eval_temp(ch)
                except Exception as e:
                    error(f"Error during measurement: {e}")
                
                next_t = ticks_add(next_t, period_ms)
                await sleep_ms(
                    max(0, ticks_diff(next_t, ticks_ms()))
                )
        finally:
            info("Measurement task stopped")

    def start_calibration(self, unit):
        self._cal_wiz = CalibrationWizard(self._num_channels, unit)
        state, instruction = self._cal_wiz.start()
        return state, instruction
    
    def cal_confirm(self, ch_to_cal):
        state, instruction  = self._cal_wiz.confirm(ch_to_cal, self.read_res_ohm()) # type: ignore
        return state, instruction

    def cal_close(self):
        self._cal_wiz = None

# Validation helper functions
def _is_valid_channel(ch:int, num_channels) -> bool:
    """Return True if the channel is valid."""
    return isinstance(ch, int) and 0 <= ch < num_channels

def _is_valid_probe(probe) -> bool:
    """Return True if the probe is valid."""
    return probe is None or isinstance(probe, NtcProbe)

def _is_valid_temp(valid_temp_flag, ch: int) -> bool:
    """Return True if the temperature of channel is valid."""
    return bool((valid_temp_flag & (1 << ch)))

def _is_valid_target(valid_target_flag, ch: int) -> bool:
    """Return True if the target temperature of channel is valid. """
    return bool((valid_target_flag & (1 << ch)))

def _is_flag_valid(flags, ch: int):
    """Return True if the flag of channel is valid."""
    return bool((flags & (1 << ch)))    