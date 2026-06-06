# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import time
from pitnode.log.log import info, warn, error

MAX_HISTORY = 100

class MinuteHistory:
    """
    Stores one averaged value per minute.

    Samples received within the same minute are averaged and added
    to the history when the minute changes. Intended for long-term
    trend data with predictable memory usage.
    """
    
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
                self._history.append(
                    self._sum / self._count
                )

                if len(self._history) > MAX_HISTORY:
                    self._history.pop(0)

            self._current_minute = minute
            self._sum = 0
            self._count = 0

        self._sum += value
        self._count += 1

    @property
    def history(self):
        return self._history