# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de

import time
import gc

import pitnode.config as cfg
from pitnode.log.log import error, info

JITTER_WARN_MS = 10
LOW_HEAP = 40_000

# ---- Laufzeit-Metriken ----
_loop_jitter_max = 0
_missed_deadlines = 0
_last_heartbeat = 0
_low_heap_events = 0

# ---- Scheduler / Loop Monitoring ----
def record_jitter(jitter_ms):
    global _loop_jitter_max, _missed_deadlines
    if jitter_ms > _loop_jitter_max:
        _loop_jitter_max = jitter_ms
    if jitter_ms > JITTER_WARN_MS:
        _missed_deadlines += 1
        if cfg.DEV_MODE:
            print("⚠ jitter", jitter_ms)

# ---- Heartbeat ----
def heartbeat():
    global _last_heartbeat
    _last_heartbeat = time.ticks_ms()

# ---- Heap Monitoring ----
def check_heap():
    global _low_heap_events
    free = gc.mem_free()
    if free < LOW_HEAP:
        _low_heap_events += 1
        if cfg.DEV_MODE:
            print("⚠ low heap", free)
    return free

# ---- Snapshot (für Web / Debug) ----
def snapshot():
    return {
        "jitter_max": _loop_jitter_max,
        "missed_deadlines": _missed_deadlines,
        "low_heap_events": _low_heap_events,
        "last_heartbeat": _last_heartbeat,
        "heap_free": gc.mem_free(),
    }

