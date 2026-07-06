import requests
from voice_navigation.config import *


# 地址 -> 经纬度
GEOCODE_API = (
    "https://api.map.baidu.com/geocoding/v3/"
)

# 坐标转换
CONVERT_API = (
    "https://api.map.baidu.com/geoconv/v2/"
)

# 步行导航
WALK_API = (
    "https://api.map.baidu.com/"
    "directionlite/v1/walking"
)


class BaiduAPI:

    # 地址 -> 百度坐标(BD09)
    @staticmethod
    def geocode(address):

        params = {
            "address": address,
            "output": "json",
            "ak": BAIDU_AK
        }

        r = requests.get(
            GEOCODE_API,
            params=params,
            timeout=5
        )

        data = r.json()

        print("\n地理编码返回:")
        print(data)

        if data["status"] != 0:
            return None

        loc = data["result"]["location"]

        return (
            loc["lat"],
            loc["lng"]
        )

    # GPS(WGS84) -> 百度BD09
    @staticmethod
    def wgs84_to_bd09(lat, lon):

        params = {
            "coords": f"{lon},{lat}",
            "model": 2,   # GPS -> 百度BD09
            "ak": BAIDU_AK
        }

        r = requests.get(
            CONVERT_API,
            params=params,
            timeout=5
        )

        data = r.json()

        print("\n坐标转换返回:")
        print(data)

        if data["status"] != 0:
            return None

        result = data["result"][0]

        return (
            result["y"],   # lat
            result["x"]    # lon
        )

    # 步行路线规划
    @staticmethod
    def walking_route(
            origin,
            destination
    ):

        params = {
            "origin":
                f"{origin[0]},{origin[1]}",

            "destination":
                f"{destination[0]},"
                f"{destination[1]}",

            "coord_type":
                "bd09ll",

            "steps_info":
                1,

            "ak":
                BAIDU_AK
        }

        r = requests.get(
            WALK_API,
            params=params,
            timeout=5
        )

        data = r.json()

        print("\n路线规划返回:")
        print(data)

        if data["status"] != 0:
            return None

        return data["result"]["routes"][0]