# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import time
from pitnode.log.log import info, warn, error

class MinuteHistory:
    def __init__(self):
        self._current_minute = None
        self._sum = 0
        self._count = 0
        self._history = []

    def add_sample(self, value):
        minute = time.time() // 60

        if self._current_minute is None:
            self._current_minute = minute

        if minute != self._current_minute:

            if self._count:
                self._history.append(self._sum / self._count)

            self._current_minute = minute
            self._sum = 0
            self._count = 0

        self._sum += value
        self._count += 1

    @property
    def history(self):
        return self._history