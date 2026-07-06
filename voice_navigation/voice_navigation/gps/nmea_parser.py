import pynmea2
class NMEAParser:         #GPS解析工具
    @staticmethod         #省去创建对象的步骤
    def parse(line):      # line 就是 GPS 发来的原始字符串
        try:
            msg = pynmea2.parse(line)
            if isinstance(msg, pynmea2.RMC):   #只保留开头是GNRMC的串口数据
                if msg.status != 'A':
                    return None
                return {
                    "lat": float(msg.latitude),
                    "lon": float(msg.longitude),
                    "speed": float(msg.spd_over_grnd or 0)
                }
        except:
            return None
        return None
