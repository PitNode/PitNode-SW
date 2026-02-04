from machine import SoftSPI, Pin
import os
from pitnode.driver import sdcard
import time
import pitnode.hw_config as hw_cfg

# --- SPI setup (SPI0) ---
spi2 = SoftSPI(
    baudrate=10_000,          # slower than you think
    polarity=0,
    phase=0,
    sck=Pin(hw_cfg.PIN_SPI2_CLK),
    mosi=Pin(hw_cfg.PIN_SPI2_MOSI),
    miso=Pin(hw_cfg.PIN_SPI2_MISO),
)
sd_cs = Pin(hw_cfg.PIN_SD_CS, Pin.OUT, value=1)
time.sleep_ms(200)

# --- Mount SD ---
sd = sdcard.SDCard(spi2, sd_cs)
time.sleep_ms(200)
os.mount(sd, "/sd")

print("SD mounted")
print("Files:", os.listdir("/sd"))

# --- Test write ---
with open("/sd/test.txt", "w") as f:
    f.write("Hello from Pico 2W!\n")

print("Write OK")

# --- Test read ---
with open("/sd/test.txt") as f:
    print("Read:", f.read())

