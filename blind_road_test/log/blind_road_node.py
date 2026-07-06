#!/usr/bin/env python3
import numpy as np
import cv2
from hobot_dnn import pyeasy_dnn as dnn
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import threading
import time

# ===================== 你的函数完全不变 =====================
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
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        w = np.maximum(0.0, xx2 - xx1)
        h = np.maximum(0.0, yy2 - yy1)
        inter = w * h
        ovr = inter / (areas[i] + areas[order[1:]])
        inds = np.where(ovr <= thresh)[0]
        order = order[inds + 1]
    return keep

# ===================== ROS2 节点 =====================
class BlindRoadNode(Node):
    def __init__(self):
        super().__init__('blind_road_detection_node')
        self.bridge = CvBridge()
        self.model = dnn.load('/userdata/blind_road_test/blind_road_test/models/yolov5s_2.bin')[0]
        self.get_logger().info("✅ 盲道检测模型已加载")

        # 订阅摄像头图像
        self.sub = self.create_subscription(
            Image, '/image', self.image_callback, 10
        )

        # 发布画框后的图像（给网页显示） → 【修复1】换话题名，避免循环！
        self.pub = self.create_publisher(Image, '/blind_road_result', 10)

        self.frame = None
        self.lock = threading.Lock()

        # 异步推理线程
        threading.Thread(target=self.infer_loop, daemon=True).start()

    def image_callback(self, msg):
        try:
            cv_img = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
            with self.lock:
                self.frame = cv_img
        except Exception as e:
            self.get_logger().error(f"图像转换错误: {e}")

    def infer_loop(self):
        while rclpy.ok():
            time.sleep(0.05)  # 控制推理频率，不卡CPU
            with self.lock:
                if self.frame is None:
                    continue
                img = self.frame.copy()

            h0, w0 = img.shape[:2]
            try:
                # ===================== 你的推理逻辑 100% 不变 =====================
                resized = cv2.resize(img, (640, 640))
                nv12 = bgr2nv12_opencv(resized)
                outputs = self.model.forward(nv12)
                pred = outputs[0].buffer.reshape(25200, 6)

                cx = pred[:, 0]
                cy = pred[:, 1]
                bw = pred[:, 2]
                bh = pred[:, 3]
                conf = pred[:, 4]

                x1 = cx - bw / 2
                y1 = cy - bh / 2
                x2 = cx + bw / 2
                y2 = cy + bh / 2

                mask = (conf > 0.5) & (bw > 20) & (bh > 20)
                boxes = np.stack([x1, y1, x2, y2], axis=1)[mask]
                confs = conf[mask]

                if len(boxes) > 0:
                    keep = nms(boxes, confs, 0.3)
                    for i in keep:
                        x1_ = np.clip(int(boxes[i,0] * w0 / 640), 0, w0)
                        y1_ = np.clip(int(boxes[i,1] * h0 / 640), 0, h0)
                        x2_ = np.clip(int(boxes[i,2] * w0 / 640), 0, w0)
                        y2_ = np.clip(int(boxes[i,3] * h0 / 640), 0, h0)
                        cv2.rectangle(img, (x1_, y1_), (x2_, y2_), (0,255,0), 2)
                        cv2.putText(img, f"Blind Road {confs[i]:.2f}",
                                    (x1_, y1_-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)

            except Exception as e:
                self.get_logger().error(f"推理错误: {e}")

            # 发布处理后图像
            try:
                msg_out = self.bridge.cv2_to_imgmsg(img, 'bgr8')
                self.pub.publish(msg_out)
            except Exception as e:
                self.get_logger().error(f"发布图像错误: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = BlindRoadNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()