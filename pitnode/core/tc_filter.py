# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

from pitnode.core.probe import ProbeState, OPEN_THRESHOLD, VALID_THRESHOLD

class TcFilter:
    def __init__(self):
        self.value = None
        self.state = ProbeState.OPEN
        self._open_cnt = 0
        self._valid_cnt = 0

    def update(self, raw):
        if raw is None:
            self._open_cnt += 1
            self._valid_cnt = 0
            if self._open_cnt >= OPEN_THRESHOLD:
                self.state = ProbeState.OPEN
            return self.value

        self._open_cnt = 0
        self._valid_cnt += 1

        if self.value is None or self.state == ProbeState.OPEN:
            if self._valid_cnt >= VALID_THRESHOLD:
                self.value = raw
                self.state = ProbeState.OK
            return self.value

        if abs(raw - self.value) > 3.0:
            return self.value

        self.value += 0.1 * (raw - self.value)
        self.state = ProbeState.OK
        return self.value
