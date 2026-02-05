# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import time
import asyncio
from math import log
import config as cfg
from pitnode.driver.hw_config import ProbeState
import pitnode.driver.hw_config as hw_cfg
from pitnode.log.log import info, warn, error

# Validation helper functions
def _is_valid_channel(ch:int) -> bool:
    """Return True if the channel is valid."""
    return isinstance(ch, int) and 0 <= ch < hw_cfg.PROBE_CHANNELS

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

class PitNodeCtrl:
    """Class for controlling the PitNode"""
    hw = None # type: ignore
    _running = False
    _tasks = []
    _probes = [None] * hw_cfg.PROBE_CHANNELS # type: list[NtcProbe | None]
    _probe_raw_value = [0] * hw_cfg.PROBE_CHANNELS
    _probe_raw_valid = 0
    _probe_mv_value = [0] * hw_cfg.PROBE_CHANNELS
    _probe_mv_valid = 0
    _probe_deg_c_value = [0.0] * hw_cfg.PROBE_CHANNELS
    _probe_deg_c_valid = 0
    _probe_resistance_value = [0] * hw_cfg.PROBE_CHANNELS
    _probe_resistance_valid = 0
    _probe_state = [ProbeState.OPEN] * hw_cfg.PROBE_CHANNELS
    _tc_raw = 0
    _tc_deg_c_value = None
    _tc_deg_c_valid = 0
    _tc_probe_state = ProbeState.OPEN
    _tc_open_cnt = 0
    _tc_valid_cnt = 0
    _probe_target_deg_c_value = [50.0] * hw_cfg.PROBE_CHANNELS
    _probe_target_valid = 0b111
    alarms = [False] * hw_cfg.PROBE_CHANNELS
    _buzzer = False
    _alarm_acked_flag = 0
    _num_channels = hw_cfg.PROBE_CHANNELS

    @classmethod
    def num_channels(cls):
        return cls._num_channels

    @classmethod
    async def start_pitnode_ctrl(cls):
        if cls._running:
            return
        if not cls._probes:
            return
        cls._running = True
        cls._tasks = [
            asyncio.create_task(cls._measure_loop()),
            asyncio.create_task(cls._alarm_task())
        ]

    @classmethod
    async def stop_pitnode_ctrl(cls):
        if not cls._running:
            return
        cls._running = False
        for t in cls._tasks:
            try:
                await t
            except asyncio.CancelledError:
                pass
        cls._tasks.clear()

    @classmethod
    def register_probe(cls, ch: int, probe) -> bool:
        """
        Register a probe to HW channel.
        Returns True if register was successful. Otherwise returns False.
        """
        if not _is_valid_channel(ch):
            warn("Invalid channel given to register_probe")
            return False

        if not _is_valid_probe(probe):
            warn("Invalid probe type given to register_probe")
            return False

        cls._probes[ch] = probe
        return True

    @classmethod
    def get_tc_temp(cls):
        if not cls._tc_deg_c_valid or cls._tc_deg_c_value is None:
            return None
        t = cls._tc_deg_c_value
        return t if cfg.UNIT == "deg" else (t * 9 / 5 + 32)

    @classmethod
    def get_temp(cls, ch: int) -> None | bool | float:
        """
        Return the temperature for given channel.
        Return False if channel invalid.
        Return None if tempeature is not valid.
        """

        if not _is_valid_channel(ch):
            warn("Invalid channel given to get_temp()")
            return False
        if not _is_valid_temp(cls._probe_deg_c_valid, ch):
            warn("Temperature is not valid")
            return None
        t = cls._probe_deg_c_value[ch]
        return t if cfg.UNIT == "deg" else (t * 9 / 5 + 32)

    @classmethod
    def get_temps(cls) -> list:
        """Return all temperatures as list."""
        temps = cls._probe_deg_c_value
        return temps if cfg.UNIT == "deg" else ([(t * 9 / 5 + 32) for t in temps])

    @classmethod
    def get_probe_states(cls) -> list:
        """Return all probe states as list."""
        return cls._probe_state

    @classmethod
    def get_tc_probe_state(cls):
        """Return TC probe state."""
        return cls._tc_probe_state

    @classmethod
    def is_temp_valid(cls, ch: int) -> bool | None:
        """Return True if temperature is valid"""
        if not _is_valid_channel(ch):
            warn("Invalid channel given to is_temp_valid()")
            return None
        return _is_valid_temp(cls._probe_deg_c_valid, ch)

    @classmethod
    def set_target_temp(cls, ch: int, temp: float | int) -> bool:
        """Return True if temperature was set successfully"""
        ch = int(ch)
        if ch < 0 or ch >= len(cls._probe_target_deg_c_value):
            return False
        
        if not isinstance(temp, (int, float)):
            return False
    
        if cfg.UNIT == "deg":
            cls._probe_target_deg_c_value[ch] = temp
        elif cfg.UNIT == "f":
            cls._probe_target_deg_c_value[ch] = (temp - 32) * 5 / 9
        else:
            return False
        
        cls._probe_target_valid |= 1 << ch
        return True

    @classmethod
    def set_target_temps(cls, values: list[float | int]) -> list[bool]:
        """Sets all target temperatures."""
        status = []
        for ch, temp in enumerate(values):
            status.append(cls.set_target_temp(ch, temp))
        return status

    @classmethod
    def get_target_temp(cls, ch: int) -> None | bool | float:
        """
        Return target temp of channel.
        Return False if ch invalid.
        Return None if target temp invalid
        """
        if not _is_valid_channel(ch):
            warn("Invalid channel given to get_target_temp()")
            return False
        if not _is_valid_target(cls._probe_target_valid, ch):
            return None
        t = cls._probe_target_deg_c_value[ch]
        return t if cfg.UNIT == "deg" else (t * 9 / 5 + 32)

    @classmethod
    def get_target_temps(cls) -> list:
        """Return all target temperatures as list."""
        return [cls.get_target_temp(ch)
                for ch in range(len(cls._probe_target_deg_c_value))]

    @classmethod
    def increase_target_temp(cls, ch: int, step: int) -> bool:
        """
        Return True if target temperature was incremented successfully.
        Otherwise False.
        """
        if not _is_valid_channel(ch):
            warn("Invalid channel given to increase_target_temp()")
            return False
        if not isinstance(step, int):
            warn("Stepsize for target temp is not int")
            return False
        
        # Reset confirm alarm flag
        cls._alarm_acked_flag |= 0 << ch

        step_c = step if cfg.UNIT == "deg" else step * 5 / 9
        cls._probe_target_deg_c_value[ch] += step_c
        cls._probe_target_valid |= 1 << ch
        return True

    @classmethod
    def decrease_target_temp(cls, ch: int, step: int) -> bool:
        """
        Return True if target temperature was decremented successfully.
        Otherwise False.
        """
        if not _is_valid_channel(ch):
            warn("Invalid channel given to decrease_target_temp()")
            return False
        if not isinstance(step, int):
            warn("Stepsize for target temp is not int")
            return False
        
        # Reset confirm alarm flag
        cls._alarm_acked_flag |= 0 << ch

        step_c = step if cfg.UNIT == "deg" else step * 5 / 9
        cls._probe_target_deg_c_value[ch] -= step_c
        cls._probe_target_valid |= 1 << ch
        return True

    @classmethod
    def _eval_temp(cls, ch: int) -> None:
        """Evaluates if target temperature is reached and sets alarm."""
        # measurement invalid → no alarm
        if not _is_valid_temp(cls._probe_deg_c_valid, ch):
            cls.alarms[ch] = False
            cls._alarm_acked_flag &= ~(1 << ch)
            return
        # no target configured → no alarm
        if not _is_valid_target(cls._probe_target_valid, ch):
            cls.alarms[ch] = False
            cls._alarm_acked_flag &= ~(1 << ch)
            return
        temp_meas = cls._probe_deg_c_value[ch]
        temp_target = cls._probe_target_deg_c_value[ch]
        if temp_meas >= temp_target:
            cls.alarms[ch] = True
            # do NOT touch ack here
        else:
            cls.alarms[ch] = False
            cls._alarm_acked_flag &= ~(1 << ch)

    @classmethod
    def _any_unacked_alarm(cls) -> bool:
        for ch, active in enumerate(cls.alarms):
            if active and not (cls._alarm_acked_flag & (1 << ch)):
                return True
        return False

    @classmethod
    def confirm_alarm(cls, ch: int):
        if not _is_valid_channel(ch):
            return False
        cls._alarm_acked_flag |= 1 << ch
        return True

    @classmethod
    def any_alarm_active(cls):
        """Return True if an alarm is active."""
        return any(cls.alarms)
    
    @classmethod
    def is_alarm_active(cls, ch: int) -> bool | None:
        """Return True if alarm of channel is active."""
        if not _is_valid_channel(ch):
            warn("Invalid channel given to is_alarm_active()")
            return None
        return cls.alarms[ch]

    @classmethod
    def is_alarm_confirmed(cls, ch: int) -> bool | None:
        """Return True if alarm of channel is active and confirmed."""
        if not _is_valid_channel(ch):
            warn("Invalid channel given to is_alarm_confirmed()")
            return None
        if not cls.alarms[ch]:
            return False
        return bool(cls._alarm_acked_flag & (1 << ch))

    @classmethod
    def reset_alarms(cls):
        """Reset all alarms."""
        cls.alarms = [False] * hw_cfg.PROBE_CHANNELS

    @classmethod
    def reset_alarm(cls, ch: int):
        """
        Reset alarm of given channel.
        Returns None in case of invalid channel.
        """
        if not _is_valid_channel(ch):
            warn("Invalid channel given to reset_alarm()")
            return None
        cls.alarms[ch] = False

    @classmethod
    async def _alarm_task(cls):
        try:
            while cls._running:
                if cls._any_unacked_alarm():
                    await cls.trigger_buzzer()
                else:
                    if cls.hw and cls.hw._buzzer:
                        cls.hw.buzzer_off()  # ensure silence
                await asyncio.sleep(0.5)
        finally:
            info("Controller alarm task stopped")
            if cls.hw and cls.hw._buzzer:
                cls.hw.buzzer_off()

    @classmethod
    async def trigger_buzzer(cls):
        assert cls.hw is not None, "HW not set"
        cls.hw.buzzer_on()
        await asyncio.sleep(0.3)
        cls.hw.buzzer_off()

    @classmethod
    def read_tc_deg(cls):
        assert cls.hw is not None, error("HW not set")

        try:
            raw = cls.hw.read_tc()
        except Exception:
            cls._tc_probe_state = ProbeState.INVALID
            cls._tc_deg_c_valid = 0
            return cls._tc_deg_c_value

        # ---- OPEN DETECTION ----
        if raw is None:
            cls._tc_open_cnt += 1
            cls._tc_valid_cnt = 0

            if cls._tc_open_cnt >= hw_cfg.OPEN_THRESHOLD:
                cls._tc_probe_state = ProbeState.OPEN
                cls._tc_deg_c_valid = 0

            return cls._tc_deg_c_value

        # ---- VALID SAMPLE ----
        cls._tc_open_cnt = 0
        cls._tc_valid_cnt += 1

        # Reconnect / first stable value
        if cls._tc_probe_state == ProbeState.OPEN or cls._tc_deg_c_value is None:
            if cls._tc_valid_cnt >= hw_cfg.VALID_THRESHOLD:
                cls._tc_deg_c_value = raw
                cls._tc_probe_state = ProbeState.OK
                cls._tc_deg_c_valid = 1
            return cls._tc_deg_c_value

        # ---- GLITCH FILTER (only when connected) ----
        if abs(raw - cls._tc_deg_c_value) > 3.0:
            return cls._tc_deg_c_value

        # ---- EMA ----
        cls._tc_deg_c_value += 0.1 * (raw - cls._tc_deg_c_value)
        cls._tc_probe_state = ProbeState.OK
        cls._tc_deg_c_valid = 1
        return cls._tc_deg_c_value

    @classmethod
    def read_res_ohm(cls):
        assert cls.hw is not None, error("HW not set")

        res = [None] * hw_cfg.PROBE_CHANNELS
        raw_values = cls.hw.read_raw()

        for ch, (raw, r_series_ohm) in enumerate(
            zip(raw_values, hw_cfg.R_SERIES_OHM)
        ):
            mv = (raw * hw_cfg.V_ADC_REF_MV) // 65535

            # Short
            if mv <= hw_cfg.ADC_MIN_MV:
                cls._probe_state[ch] = ProbeState.SHORT
                continue

            # Open / no probe
            if mv >= hw_cfg.ADC_MAX_MV:
                cls._probe_state[ch] = ProbeState.OPEN
                continue

            # Invalid
            denom = hw_cfg.V_ADC_REF_MV - mv
            if denom <= 0:
                cls._probe_state[ch] = ProbeState.INVALID
                continue

            r_ntc_ohm = (r_series_ohm * mv) // denom

            # Plausibility
            if r_ntc_ohm <= 0 or r_ntc_ohm > hw_cfg.R_MAX_OHM:
                cls._probe_state[ch] = ProbeState.OPEN
                continue

            # OK
            res[ch] = r_ntc_ohm
            cls._probe_state[ch] = ProbeState.OK
            cls._probe_resistance_value[ch] = r_ntc_ohm
            cls._probe_resistance_valid |= 1 << ch
        return res

    @classmethod
    async def _measure_loop(cls):
        period_ms = 500
        next_t = time.ticks_ms()
        try:
            while cls._running:
                now = time.ticks_ms()
                late = time.ticks_diff(now, next_t)
                if late > 50:   # z. B. 50 ms Toleranz
                    if cfg.DEV_MODE is True:
                        warn(f"Measurement late: {late} ms")
                try:
                    cls._probe_deg_c_valid = 0
                    cls._probe_resistance_valid = 0
                    resistances = cls.read_res_ohm()
                    cls.read_tc_deg()
                    for ch, res in enumerate(resistances):
                        probe = cls._probes[ch]
                        if probe is None:
                            continue

                        if cls._probe_state[ch] != ProbeState.OK:
                            cls._probe_deg_c_valid &= ~(1 << ch)
                            continue

                        cls._probe_deg_c_value[ch] = probe.resistance_to_deg_c(res) #type:ignore
                        cls._probe_deg_c_valid |= 1 << ch
                        cls._eval_temp(ch)
                except Exception as e:
                    error(f"Error during measurement: {e}")
                
                next_t = time.ticks_add(next_t, period_ms)
                await asyncio.sleep_ms(
                    max(0, time.ticks_diff(next_t, time.ticks_ms()))
                )
        finally:
            info("Measurement task stopped")

class NtcProbe:
    def __init__(
        self,
        t_ntc_0_mk=298150,  # 25°C in milli-Kelvin
        beta_k=3380,  # Beta in Kelvin
        r_ntc_0_ohm=100000,  # 100kΩ in Ohm
        name="NTC std probe",
    ):
        self.name = name
        self._t0 = t_ntc_0_mk / 1000.0  # K
        self._beta = beta_k  # K
        self._r0 = r_ntc_0_ohm  # Ω

    def resistance_to_k(self, r_ohm:int):
        r = r_ohm
        return 1.0 / ((1.0 / self._t0) + (1.0 / self._beta) * log(r / self._r0))

    def resistance_to_deg_c(self, r_ohm: int):
        return round(self.resistance_to_k(r_ohm) - 273.15, 1)

    def resistance_to_deg_f(self, r_ohm):
        return round(self.resistance_to_deg_c(r_ohm) * 9 / 5 + 32, 1)


