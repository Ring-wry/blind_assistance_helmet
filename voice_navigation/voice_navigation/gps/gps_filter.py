class GPSFilter:           # GPS数据防抖/平滑类→让定位不飘、不乱跳
    def __init__(self):
        self.last_lat = None       #存上一次的维度
        self.last_lon = None       #存上一次的经度
    def filter(self, lat, lon):
        if self.last_lat is None:
            self.last_lat = lat
            self.last_lon = lon
            return lat, lon
        lat = self.last_lat * 0.7 + lat * 0.3
        lon = self.last_lon * 0.7 + lon * 0.3
        self.last_lat = lat
        self.last_lon = lon
        return lat, lon
