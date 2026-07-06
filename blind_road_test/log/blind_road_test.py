#!/usr/bin/env python3
import numpy as np
import cv2
from hobot_dnn import pyeasy_dnn as dnn

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
        ovr = inter / (areas[i] + areas[order[1:]] - inter)
        inds = np.where(ovr <= thresh)[0]
        order = order[inds + 1]
    return keep

if __name__ == '__main__':
    models = dnn.load('/userdata/blind_road_test/blind_road_test/models/yolov5s_2.bin')
    img = cv2.imread('./0011.jpg')
    h0, w0 = img.shape[:2]

    resized = cv2.resize(img, (640, 640))
    nv12 = bgr2nv12_opencv(resized)
    outputs = models[0].forward(nv12)

    pred = outputs[0].buffer.reshape(25200, 6)

    # ======================== 【完全适配你的模型】 ========================
    cx = pred[:, 0]
    cy = pred[:, 1]
    bw = pred[:, 2]
    bh = pred[:, 3]
    conf = pred[:, 4]
    cls = pred[:, 5]

    # 坐标转换
    x1 = cx - bw / 2
    y1 = cy - bh / 2
    x2 = cx + bw / 2
    y2 = cy + bh / 2

    # ======================== 【阈值放极低 + 类别改为 1】 ========================
    mask = conf > 0.5  # 阈值
    boxes = np.stack([x1, y1, x2, y2], axis=1)[mask]
    conf = conf[mask]
    cls = cls[mask]

    print(f"候选框数量：{len(boxes)}")

    if len(boxes) > 0:
        keep = nms(boxes, conf, 0.5)
        for i in keep:
            x1_ = int(boxes[i, 0] * w0 / 640)
            y1_ = int(boxes[i, 1] * h0 / 640)
            x2_ = int(boxes[i, 2] * w0 / 640)
            y2_ = int(boxes[i, 3] * h0 / 640)
            print(f"✅ 盲道：({x1_},{y1_}) ~ ({x2_},{y2_}) 置信度:{conf[i]:.2f}")
            cv2.rectangle(img, (x1_, y1_), (x2_, y2_), (0,255,0), 2)

    cv2.imwrite('result.jpg', img)
    print("🎉 完成")
