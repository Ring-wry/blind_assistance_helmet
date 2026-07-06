import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import time

# 你已有的模块（路径保持和你的包结构一致）
from voice_navigation.gps.gps_reader import GPSReader
from voice_navigation.map.baidu_api import BaiduAPI
from voice_navigation.map.navigator import BlindNavigator
from voice_navigation.config import *

class NavigatorNode(Node):
    def __init__(self):
        super().__init__('navigator_node')

        # 发布给TTS
        self.tts_pub = self.create_publisher(String, '/tts_text', 10)
        # 订阅语音节点发来的目的地
        self.dest_sub = self.create_subscription(String, '/dest_text', self.dest_callback, 10)

        # 导航相关
        self.gps = GPSReader()
        self.navigator = BlindNavigator()
        self.origin_bd = None
        self.is_ready = False
        self.is_navigating = False

        self.get_logger().info("✅ 导航节点启动，正在连接GPS...")
        self.gps.connect()
        self.gps.start()

        # 定时器：每秒检查一次GPS和导航状态
        self.timer = self.create_timer(1.0, self.gps_check)

    def speak(self, text):
        msg = String()
        msg.data = text
        self.tts_pub.publish(msg)
        self.get_logger().info(f'🔊 TTS播报：{text}')

    def gps_check(self):
        if self.is_ready:
            if self.is_navigating:
                self.navigation_loop()
            return

        # 等待GPS定位
        loc = self.gps.get_location()
        if loc and loc["lat"] is not None:
            self.get_logger().info("✅ GPS定位成功")
            # 坐标转换
            self.origin_bd = BaiduAPI.wgs84_to_bd09(loc["lat"], loc["lon"])
            if not self.origin_bd:
                self.speak("坐标转换失败")
                return
            self.is_ready = True
            self.speak("请说您要前往的目的地")

    def dest_callback(self, msg):
        if self.is_navigating:
            self.speak("正在导航中，先结束当前导航")
            return
        dest_text = msg.data.strip()
        self.get_logger().info(f'📍 收到目的地：{dest_text}')

        # 解析目的地
        dest_bd = BaiduAPI.geocode(dest_text)
        if not dest_bd:
            self.speak("目的地解析失败，请重新说一次")
            return

        # 规划路线
        route = BaiduAPI.walking_route(self.origin_bd, dest_bd)
        if not route:
            self.speak("路线规划失败，请检查网络")
            return

        self.navigator.load_route(route)
        self.speak(f"路线规划完成，全程大约{route['duration']//60}分钟，现在开始导航")
        self.is_navigating = True

    def navigation_loop(self):
        loc = self.gps.get_location()
        if not loc:
            return
        bd = BaiduAPI.wgs84_to_bd09(loc["lat"], loc["lon"])
        if not bd:
            return

        cmd = self.navigator.update(*bd)
        if cmd == "ARRIVED":
            self.speak("已到达目的地，导航结束")
            self.is_navigating = False
        elif cmd:
            self.speak(cmd)

    def destroy_node(self):
        self.gps.stop()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = NavigatorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()