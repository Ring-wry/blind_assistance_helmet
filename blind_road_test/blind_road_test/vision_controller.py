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
            '/image_ai_blind',
            self.ai_callback,
            10
        )

        # 发布触发信号
        self.trigger_pub = self.create_publisher(Int32, '/sign4return', 10)

        # 发布语音回答
        self.tts_pub = self.create_publisher(String, '/tts_text', 10)

        # 循环开关与定时器
        self.is_running = False
        self.timer = None

        self.get_logger().info("✅ 视觉对话控制器已启动")

    def prompt_callback(self, msg):
        self.get_logger().info(f'🗣️ 收到语音：{msg.data}')

        if "开始" in msg.data or "盲道" in msg.data or "启动" in msg.data:
            if not self.is_running:
                self.get_logger().info("🚦 语音指令：开启 10 秒循环检测")
                self.is_running = True
                # 修改此处：间隔改为10秒
                self.timer = self.create_timer(10.0, self.send_trigger)

        elif "停止" in msg.data or "结束" in msg.data:
            if self.is_running and self.timer is not None:
                self.get_logger().info("🛑 语音指令：停止循环检测")
                self.is_running = False
                self.timer.cancel()
                self.timer = None

    # 定时发布触发信号
    def send_trigger(self):
        if self.is_running:
            trigger_msg = Int32()
            trigger_msg.data = 30
            self.trigger_pub.publish(trigger_msg)
            self.get_logger().info("📤 已发布触发信号 30（每10秒一次）")

    def ai_callback(self, msg):
        data = msg.data
        # 只转发包含“检测到”的盲道结果，LLM描述内容直接丢弃
        if "检测到" in data:
            self.get_logger().info(f'🤖 盲道AI分析结果：{data}')
            tts_msg = String()
            tts_msg.data = data
            self.tts_pub.publish(tts_msg)
        else:
            self.get_logger().info(f"忽略非盲道消息：{data}")

def main(args=None):
    rclpy.init(args=args)
    node = VisionController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()