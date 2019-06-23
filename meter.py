from telnetlib import Telnet
import time
import re
import statistics


# A bare-bones implementation of a circular buffer that will be used to store the last n readings
# Better than either a list or a Collections.deque
class CircularList:
    def __init__(self, size):
        self._list = []
        self._size = size
        self._start = 0
        self._len = 0

    def __getitem__(self, item):
        # raise IndexError so instances of this class can be used on methods that expect a sequence
        if item >= self._len:
            raise IndexError
        return self._list[(self._start + item) % self._len]

    def append(self, item):
        if self._len < self._size:
            self._list.append(item)
            self._len += 1
        else:
            self._list[self._start] = item
            self._start = (self._start + 1) % self._size

    def __len__(self):
        return self._len

    def __str__(self):
        return str(self._list[self._start:] + self._list[:self._start])


IP = '192.168.1.1'
# ISP default credentials
USERNAME = b'meo'
PASSWORD = b'meo'

SMA_SIZE = 3
READING_PERIOD = 5

with Telnet(IP) as tn:
    tn.read_until(b"Login: ")
    tn.write(USERNAME + b'\n')
    tn.read_until(b'Password: ')
    tn.write(PASSWORD + b'\n')
    tn.read_until(b'ADB# ')
    pattern = re.compile('Bytes.+?(\d+).+?(\d+)')
    download = CircularList(SMA_SIZE)
    upload = CircularList(SMA_SIZE)
    down_prev = 0
    up_prev = 0
    time_prev = 0
    while True:
        tn.write(b'show ip counters ppp0\n')
        r = tn.read_until(b'ADB# ').decode('ascii')
        time_cur = time.time_ns()
        m = re.search(pattern, r)
        down_cur = int(m.group(1))
        up_cur = int(m.group(2))
        if time_prev:
            time_d = time_cur - time_prev
            download.append((down_cur - down_prev) / time_d)
            upload.append((up_cur - up_prev) / time_d)
            print(round(statistics.mean(download) / 1024E-9, 1), "KiB/s ↓ |",
                  round(statistics.mean(upload) / 1024E-9, 1), "KiB/s ↑")
        down_prev = down_cur
        up_prev = up_cur
        time_prev = time_cur
        time.sleep(READING_PERIOD)
