import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class VoiceControllerNode(Node):
    def __init__(self):
        super().__init__('voice_controller_node')

        # 订阅ASR
        self.prompt_sub = self.create_subscription(
            String, '/prompt_text', self.prompt_callback, 10
        )
        # 发布目的地给导航节点
        self.dest_pub = self.create_publisher(String, '/dest_text', 10)

        self.get_logger().info("✅ 语音交互节点已启动")

    def prompt_callback(self, msg):
        text = msg.data.strip()
        self.get_logger().info(f'🗣️ 收到语音：{text}')

        # 简单提取目的地（适配你口语）
        if "导航到" in text:
            dest = text.split("导航到")[-1].strip()
        elif "去" in text:
            dest = text.split("去")[-1].strip()
        elif "到" in text:
            dest = text.split("到")[-1].strip()
        else:
            dest = text

        if dest:
            self.get_logger().info(f'📍 发送目的地：{dest}')
            self.dest_pub.publish(String(data=dest))

def main(args=None):
    rclpy.init(args=args)
    node = VoiceControllerNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()