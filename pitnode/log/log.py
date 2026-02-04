# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

INFO  = 1
WARN  = 2
ERROR = 3

_level = INFO

def set_level(level):
    global _level
    _level = level

def _log(level, tag, msg):
    if level < _level:
        return
    print("[%s] %s" % (tag, msg))

def info(msg):
    _log(INFO, "I", msg)

def warn(msg):
    _log(WARN, "W", msg)

def error(msg):
    _log(ERROR, "E", msg)

#set_level(_level)