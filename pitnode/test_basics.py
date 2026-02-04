import asyncio

from pitnode.controller import PitNodeCtrl as Ctrl
from pitnode.driver.rpi_pico import RPiPico as Pico
import pitnode.hw_config as hw_cfg

async def test_buzzer():
    for _ in range(5):
        await Ctrl.trigger_buzzer()
        await asyncio.sleep(0.5)

async def main():
    await Ctrl.start_pitnode_ctrl()
    await asyncio.sleep(1)
    print("Alarm on")
    Ctrl.alarms = [False, False, True]
    await asyncio.sleep(3)
    print("Alarm off")
    Ctrl.alarms = [False] * hw_cfg.PROBE_CHANNELS
    await asyncio.sleep(3)
    print("Alarm on")
    Ctrl.alarms = [True] * hw_cfg.PROBE_CHANNELS
    await asyncio.sleep(5)
    print(Ctrl._alarm_acked_flag)
    Ctrl.confirm_alarm(0)
    Ctrl.confirm_alarm(1)
    Ctrl.confirm_alarm(2)
    await asyncio.sleep(0)
    print(Ctrl._alarm_acked_flag)
    print(Ctrl.alarms)
    print("Confirmed all alarms")
    print(Ctrl.any_alarm_active())
    await asyncio.sleep(3)
    Ctrl._alarm_acked_flag = 0
    print("Alarm on")
    await asyncio.sleep(3)

Ctrl.hw = Pico()
asyncio.run(main())
