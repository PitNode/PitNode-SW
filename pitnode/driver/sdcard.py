from micropython import const
import time

_CMD_TIMEOUT = const(2000)
_R1_IDLE_STATE = const(1 << 0)
_TOKEN_DATA = const(0xFE)

class SDCard:
    def __init__(self, spi, cs):
        self.spi = spi
        self.cs = cs
        self.cs.init(self.cs.OUT, value=1)
        self.init_card()

    def init_card(self):
        # 80+ clocks with CS HIGH
        self.cs(1)
        for _ in range(20):
            self.spi.write(b"\xff")

        # CMD0
        self.cs(0)
        if self.cmd(0, 0, 0x95) != _R1_IDLE_STATE:
            self.cs(1)
            raise OSError("CMD0 failed")

        # CMD8
        r = self.cmd(8, 0x1AA, 0x87)

        # ACMD41 loop
        while True:
            self.cmd(55, 0, 0)
            if self.cmd(41, 0x40000000 if r == _R1_IDLE_STATE else 0, 0) == 0:
                break
            time.sleep_ms(10)

        # Set block size
        self.cmd(16, 512, 0)

        self.cs(1)
        self.spi.write(b"\xff")

    def cmd(self, cmd, arg, crc):
        self.spi.write(b"\xff")
        self.spi.write(bytearray([0x40 | cmd]))
        self.spi.write(arg.to_bytes(4, "big"))
        self.spi.write(bytearray([crc]))

        for _ in range(_CMD_TIMEOUT):
            r = self.spi.read(1, 0xFF)[0]
            if not (r & 0x80):
                return r
            time.sleep_us(20)
        return -1

    def readblocks(self, block, buf):
        self.cs(0)
        self.cmd(17, block * 512, 0)
        while self.spi.read(1, 0xFF)[0] != _TOKEN_DATA:
            pass
        self.spi.readinto(buf)
        self.spi.read(2, 0xFF)
        self.cs(1)

    def writeblocks(self, block, buf):
        self.cs(0)
        self.cmd(24, block * 512, 0)
        self.spi.write(bytearray([_TOKEN_DATA]))
        self.spi.write(buf)
        self.spi.write(b"\xff\xff")
        while self.spi.read(1, 0xFF)[0] == 0:
            pass
        self.cs(1)

    def ioctl(self, op, arg):
        if op == 4:
            return 0
        if op == 5:
            return 512
