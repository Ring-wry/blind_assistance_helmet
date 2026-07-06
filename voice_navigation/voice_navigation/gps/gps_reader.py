import serial
import threading     #导入线程库，让GPS读取在后台一直跑
import time          #时间工具，用来延时、等待
from voice_navigation.gps.nmea_parser import NMEAParser
from voice_navigation.gps.gps_filter import GPSFilter
from voice_navigation.config import *
class GPSReader:
    def __init__(self):
        self.ser = None
        self.running = False      #控制是否持续读取GPS
        self.location = None
        self.lock = threading.Lock()
        self.filter = GPSFilter()
    def connect(self):
        self.ser = serial.Serial(
            GPS_SERIAL,
            GPS_BAUDRATE,
            timeout=GPS_TIMEOUT
        )
    def start(self):
        self.running = True
        threading.Thread(
            target=self.read_loop,
            daemon=True
        ).start()
    def read_loop(self):
        while self.running:
            try:
                line = self.ser.readline()\
                    .decode(errors='ignore')\
                    .strip()
                if not line.startswith("$"):
                    continue
                data = NMEAParser.parse(line)
                if not data:
                    continue
                lat, lon = self.filter.filter(
                    data["lat"],
                    data["lon"]
                )
                with self.lock:
                    self.location = {
                        "lat": lat,
                        "lon": lon,
                        "speed": data["speed"]
                    }
            except Exception as e:
                print("GPS ERROR:", e)
                time.sleep(1)
    def get_location(self):
        with self.lock:
            return self.location
    def stop(self):
        self.running = False
        if self.ser:
            self.ser.close()
