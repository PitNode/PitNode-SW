# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

# base_board.py

class BaseBoard:
    """Base class for all PitNode hardware boards."""

    def __init__(self, hw_cfg) -> None:
        self._hw_cfg = hw_cfg

    # --- configuration access ---
    @property
    def hw_cfg(self):
        return self._hw_cfg

    # --- wlan ---
    def wlan(self):
        raise NotImplementedError

    # --- temperature ---
    def read_raw(self) -> list[int]:
        raise NotImplementedError

    def read_tc(self) -> float | None:
        raise NotImplementedError

    # --- buzzer ---
    def buzzer_on(self):
        raise NotImplementedError

    def buzzer_off(self):
        raise NotImplementedError

    # --- system ---
    def reboot(self):
        raise NotImplementedError

    def unique_id(self):
        raise NotImplementedError