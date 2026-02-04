

# scheduler_watchdog.py
import uasyncio as asyncio
import time
import pitnode.dev.monitor as monitor

async def scheduler_watchdog(period_ms=10):
    last = time.ticks_ms()
    while True:
        await asyncio.sleep_ms(period_ms)
        now = time.ticks_ms()
        delta = time.ticks_diff(now, last)
        monitor.record_jitter(delta - period_ms)
        last = now

async def heartbeat_task():
    while True:
        monitor.heartbeat()
        await asyncio.sleep(1)

async def heap_task():
    while True:
        monitor.check_heap()
        await asyncio.sleep(1)
