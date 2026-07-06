import os
import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Int32
from sensor_msgs.msg import CompressedImage
import numpy as np
import cv2
from hobot_dnn import pyeasy_dnn as dnn
import time

# ===================== 工具函数 完全不变 =====================
def bgr2nv12_opencv(image):
    height, width = image.shape[0], image.shape[1]
    area = height * width
    yuv420p = cv2.cvtColor(image, cv2.COLOR_BGR2YUV_I420).reshape((area * 3 // 2,))
    y = yuv420p[:area]
    uv_planar = yuv420p[area:].reshape((2, area // 4))
    uv_packed = uv_planar.transpose((1, 0)).reshape((area // 2,))
    nv12 = np.zeros_like(yuv420p)
    nv12[:height * width] = y
    nv12[height * width:] = uv_packed
    return nv12

def nms(dets, scores, thresh):
    x1 = dets[:, 0]
    y1 = dets[:, 1]
    x2 = dets[:, 2]
    y2 = dets[:, 3]
    areas = (x2 - x1) * (y2 - y1)
    order = scores.argsort()[::-1]
    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y2[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        w = np.maximum(0.0, xx2 - xx1)
        h = np.maximum(0.0, yy2 - yy1)
        inter = w * h
        ovr = inter / (areas[i] + areas[order[1:]] - inter)
        inds = np.where(ovr <= thresh)[0]
        order = order[inds + 1]
    return keep

# ===================== 室外交通标志物类别配置 =====================
CLASS_NAMES = [
    'tree',                # 0 树木
    'red_light',           # 1 红灯
    'green_light',         # 2 绿灯
    'crosswalk',           # 3 斑马线
    'tactile_paving',      # 4 盲道砖
    'sign',                # 5 交通标识牌
    'pedestrian',          # 6 行人
    'bicycle',             # 7 自行车
    'bus',                 # 8 公交车
    'truck',               # 9 货车
    'car',                 # 10 小轿车
    'motorcycle',          # 11 摩托车
    'reflective_cone',     # 12 反光路锥
    'ashcan',              # 13 垃圾桶
    'warning_column',      # 14 警示柱
    'roadblock',           # 15 路障
    'pole',                # 16 电线杆
    'dog',                 # 17 犬只
    'tricycle',            # 18 三轮车
    'fire_hydrant'         # 19 消防栓
]

# 仅保留需要播报5类室外目标
TARGET_CLASSES = {'crosswalk', 'red_light', 'green_light', 'motorcycle', 'roadblock'}
# 英文转中文播报名称
CN_NAME_MAP = {
    'crosswalk': '斑马线',
    'red_light': '红灯',
    'green_light': '绿灯',
    'motorcycle': '电动车',
    'roadblock': '路障'
}

# ===================== 新增室内标识模型配置 =====================
INDOOR_CLASS_NAMES = [
    "无障碍设施",
    "安全出口",
    "男厕所",
    "禁止吸烟",
    "WIFI",
    "女厕所"
]
# 需要播报的室内标识，过滤禁止吸烟、WIFI
INDOOR_TARGET = {"无障碍设施", "安全出口", "男厕所", "女厕所"}

# ===================== 主节点 =====================
class BlindRoadDetector(Node):
    def __init__(self):
        super().__init__('blind_road_detector')
        self.get_logger().info("✅ 三模型融合检测节点启动")

        # 三个模型句柄
        self.blind_model = None
        self.traffic_model = None
        self.sign_model = None

        # 1.盲道模型
        try:
            self.blind_model = dnn.load("/userdata/blind_road_test/blind_road_test/models/yolov5s_2.bin")[0]
            self.get_logger().info("✅ 盲道模型加载成功")
        except Exception as e:
            self.get_logger().error(f"盲道模型加载失败: {e}")

        # 2.交通标志物模型
        try:
            self.traffic_model = dnn.load("/userdata/blind_road_test/blind_road_test/models/traffic_yolov5s_new.bin")[0]
            self.get_logger().info("✅ 交通标志物模型加载成功")
        except Exception as e:
            self.get_logger().error(f"交通标志物模型加载失败: {e}")

        # 3.室内标识模型
        try:
            self.sign_model = dnn.load("/userdata/blind_road_test/blind_road_test/models/signs_yolov5s_new.bin")[0]
            self.get_logger().info("✅ 室内标识模型加载成功")
        except Exception as e:
            self.get_logger().error(f"室内标识模型加载失败: {e}")

        # 盲道专用输出话题
        self.result_publisher = self.create_publisher(String, '/image_ai_blind', 10)

        self.image_sub = self.create_subscription(
            CompressedImage,
            '/image',
            self.image_callback,
            10
        )

        self.sign_sub = self.create_subscription(
            Int32,
            '/sign4return',
            self.sign_callback,
            10
        )

        self.trigger_analysis = False
        self.latest_image_data = None

        # 重复播报过滤缓存
        self.last_speak_text = ""
        self.last_speak_time = time.time()

    # 触发信号回调
    def sign_callback(self, msg):
        if msg.data == 30:
            self.get_logger().info("🚦 收到触发信号(30)，准备检测")
            self.trigger_analysis = True

    # 图像回调
    def image_callback(self, msg):
        self.latest_image_data = msg.data
        if self.trigger_analysis and self.latest_image_data is not None:
            self.trigger_analysis = False
            self.get_logger().info("开始处理图像...")
            self.process_image(self.latest_image_data)
            self.latest_image_data = None

    # 图像解码 & 三模型并行推理
    def process_image(self, compressed_data):
        try:
            np_arr = np.frombuffer(compressed_data, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if img is None:
                self.get_logger().error("图像解码失败")
                return

            blind_res = self.detect_blind_road(img.copy()) if self.blind_model else ""
            traffic_res = self.detect_traffic_signs(img.copy()) if self.traffic_model else ""
            indoor_res = self.detect_indoor_signs(img.copy()) if self.sign_model else ""

            # 合并播报内容：只有非空结果才加入
            combine_list = []
            if blind_res:
                combine_list.append(blind_res)
            if traffic_res:
                combine_list.append(traffic_res)
            if indoor_res:
                combine_list.append(indoor_res)

            if not combine_list:
                # 三个模型都没检测到，不播报
                self.get_logger().info("未检测到任何目标，不播报")
                return

            final_text = "，".join(combine_list)
            self.publish_result(final_text)

        except Exception as e:
            self.get_logger().error(f"处理错误: {str(e)}")

    # ===================== 盲道检测（修改输出格式） =====================
    def detect_blind_road(self, img):
        try:
            h0, w0 = img.shape[:2]
            resized = cv2.resize(img, (640, 640))
            nv12 = bgr2nv12_opencv(resized)
            outputs = self.blind_model.forward(nv12)
            pred = outputs[0].buffer.reshape(25200, 6)

            cx = pred[:, 0]
            cy = pred[:, 1]
            bw = pred[:, 2]
            bh = pred[:, 3]
            conf = pred[:, 4]

            x1 = cx - bw / 2
            y1 = cy - bh / 2
            x2 = cx + bw / 2

            mask = (conf > 0.5) & (bw > 20) & (bh > 20)
            boxes = np.stack([x1, y1, x2], axis=1)[mask]
            confs = conf[mask]

            count = 0
            pos = "中间"

            if len(boxes) > 0:
                keep = nms(boxes, confs, 0.3)
                count = len(keep)
                for i in keep:
                    x1_ = np.clip(int(boxes[i,0] * w0 / 640), 0, w0)
                    if x1_ < w0//3:
                        pos = "左侧"
                    elif x1_ > w0*2//3:
                        pos = "右侧"

            if count == 0:
                return ""
            # 修改格式：检测到左侧有盲道
            return f"检测到{pos}有盲道"

        except Exception as e:
            self.get_logger().error(f"盲道检测失败: {e}")
            return ""

    # ===================== 室外交通标志物检测（修改条目格式） =====================
    def detect_traffic_signs(self, img):
        try:
            h0, w0 = img.shape[:2]
            resized = cv2.resize(img, (640, 640))
            nv12 = bgr2nv12_opencv(resized)
            outputs = self.traffic_model.forward(nv12)

            pred = outputs[0].buffer.reshape(25200, 25)

            cx = pred[:, 0]
            cy = pred[:, 1]
            bw = pred[:, 2]
            bh = pred[:, 3]
            conf = pred[:, 4]
            cls_scores = pred[:, 5:]

            cls = np.argmax(cls_scores, axis=1)
            max_cls_score = np.max(cls_scores, axis=1)
            final_conf = conf * max_cls_score

            x1 = cx - bw / 2
            y1 = cy - bh / 2
            x2 = cx + bw / 2
            y2 = cy + bh / 2

            conf_thresh = 0.5
            mask = final_conf > conf_thresh

            boxes = np.stack([x1, y1, x2, y2], axis=1)[mask]
            scores = final_conf[mask]
            class_ids = cls[mask]

            detect_list = []

            if len(boxes) > 0:
                keep = nms(boxes, scores, 0.5)
                seen = set()

                for i in keep:
                    class_id = int(class_ids[i])
                    en_name = CLASS_NAMES[class_id]
                    if en_name not in TARGET_CLASSES:
                        continue

                    cn_name = CN_NAME_MAP[en_name]
                    x1_ = int(boxes[i, 0] * w0 / 640)
                    x2_ = int(boxes[i, 2] * w0 / 640)
                    if x1_ < w0 // 3:
                        pos = "左侧"
                    elif x2_ > w0 * 2 // 3:
                        pos = "右侧"
                    else:
                        pos = "中间"

                    key = (cn_name, pos)
                    if key not in seen:
                        seen.add(key)
                        # 格式：检测到左侧有红灯
                        detect_list.append(f"检测到{pos}有{cn_name}")

            if detect_list:
                return "，".join(detect_list)
            else:
                return ""

        except Exception as e:
            self.get_logger().error(f"标志物检测失败: {e}")
            return ""

    # ===================== 室内标识检测（统一格式） =====================
    def detect_indoor_signs(self, img):
        try:
            h0, w0 = img.shape[:2]
            resized = cv2.resize(img, (640, 640))
            nv12 = bgr2nv12_opencv(resized)
            outputs = self.sign_model.forward(nv12)

            pred = outputs[0].buffer.reshape(25200, 11)

            cx = pred[:, 0]
            cy = pred[:, 1]
            bw = pred[:, 2]
            bh = pred[:, 3]
            conf = pred[:, 4]
            cls_scores = pred[:, 5:]

            cls = np.argmax(cls_scores, axis=1)
            max_cls_score = np.max(cls_scores, axis=1)
            final_conf = conf * max_cls_score

            x1 = cx - bw / 2
            y1 = cy - bh / 2
            x2 = cx + bw / 2
            y2 = cy + bh / 2

            conf_thresh = 0.5
            mask = final_conf > conf_thresh

            boxes = np.stack([x1, y1, x2, y2], axis=1)[mask]
            scores = final_conf[mask]
            class_ids = cls[mask]

            detect_list = []
            if len(boxes) > 0:
                keep = nms(boxes, scores, 0.5)
                seen = set()

                for i in keep:
                    cid = int(class_ids[i])
                    name = INDOOR_CLASS_NAMES[cid]
                    if name not in INDOOR_TARGET:
                        continue

                    x1_ = int(boxes[i, 0] * w0 / 640)
                    x2_ = int(boxes[i, 2] * w0 / 640)
                    if x1_ < w0 // 3:
                        pos = "左侧"
                    elif x2_ > w0 * 2 // 3:
                        pos = "右侧"
                    else:
                        pos = "中间"

                    key = (name, pos)
                    if key not in seen:
                        seen.add(key)
                        # 格式：检测到左侧有安全出口
                        detect_list.append(f"检测到{pos}有{name}")

            if detect_list:
                return "，".join(detect_list)
            else:
                return ""

        except Exception as e:
            self.get_logger().error(f"室内标识检测失败: {e}")
            return ""

    # 发布结果：移除"图像分析结果："前缀，直接发送文本
    def publish_result(self, text):
        now = time.time()
        if text == self.last_speak_text and now - self.last_speak_time < 3.0:
            self.get_logger().info("重复播报内容，跳过发布")
            return
        self.last_speak_text = text
        self.last_speak_time = now

        msg = String()
        # 关键修改：删除前缀，直接赋值原始拼接文本
        msg.data = text
        self.get_logger().info(text)
        self.result_publisher.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = BlindRoadDetector()
    node.get_logger().info("✅ 三模型检测节点已启动，等待触发信号...")
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()