import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Int32

class VisionController(Node):
    def __init__(self):
        super().__init__('vision_controller')

        # 订阅语音提问
        self.prompt_sub = self.create_subscription(
            String,
            '/prompt_text',
            self.prompt_callback,
            10
        )

        # 订阅AI图像分析结果
        self.ai_sub = self.create_subscription(
            String,
            '/image_ai',
            self.ai_callback,
            10
        )

        # 发布触发信号
        self.trigger_pub = self.create_publisher(Int32, '/sign4return', 10)

        # 发布语音回答
        self.tts_pub = self.create_publisher(String, '/tts_text', 10)

        self.get_logger().info("✅ 视觉对话控制器已启动")

    def prompt_callback(self, msg):
        self.get_logger().info(f'🗣️ 收到语音：{msg.data}')

        # 触发图像分析
        trigger_msg = Int32()
        trigger_msg.data = 30
        self.trigger_pub.publish(trigger_msg)

    def ai_callback(self, msg):
        self.get_logger().info(f'🤖 AI分析结果：{msg.data}')

        # 转发给TTS朗读
        tts_msg = String()
        tts_msg.data = msg.data
        self.tts_pub.publish(tts_msg)

def main(args=None):
    rclpy.init(args=args)
    node = VisionController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()