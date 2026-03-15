# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

INFO  = 1
WARN  = 2
ERROR = 3

class Logger:
    def __init__(self):
        self._level = ERROR
        self._dev_mode = False

    def set_mode(self, dev_mode):
        self._dev_mode = dev_mode

    def set_level(self, level):
        global _level
        _level = level

    def _log(self, level, tag, msg):
        if not self._dev_mode and level < self._level:
            return
        print("[%s] %s" % (tag, msg))

    def info(self, msg):
        self._log(INFO, "I", msg)
    
    def warn(self, msg):
        self._log(WARN, "W", msg)

    def error(self, msg):
        self._log(ERROR, "E", msg)

logger = Logger()
info = logger.info
error = logger.error
warn = logger.warn
