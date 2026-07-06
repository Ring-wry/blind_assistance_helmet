from voice_navigation.utils.geo import haversine
from voice_navigation.config import *

import time
import re


class BlindNavigator:

    def __init__(self):
        # 整条路线
        self.route = None
        # 每一步导航
        self.steps = []
        # 当前执行到哪一步
        self.step_index = 0
        # 上次提醒时间
        self.last_continue_time = 0
        # 上次播报的指令（防止重复播报）
        self.last_instruction = None
        # 是否已经播报过第一步指令
        self.first_step_spoken = False

    def load_route(self, route):
        self.route = route
        self.steps = route["steps"]
        self.step_index = 0
        self.last_continue_time = 0
        self.last_instruction = None
        self.first_step_spoken = False

        print("\n===== 开始导航 =====")
        print(f"总距离: {route['distance']} 米")
        print(f"预计时间: {route['duration'] // 60} 分钟")

    def clean_instruction(self, text):
        # 去掉HTML标签
        text = re.sub(r"<.*?>", "", text)
        return text

    def update(self, lat, lon):
        # 全部完成
        if self.step_index >= len(self.steps):
            return "ARRIVED"

        step = self.steps[self.step_index]
        end = step["end_location"]

        distance = haversine(
            lat, lon,
            float(end["lat"]), float(end["lng"])
        )
        
           # ========== 终端实时打印（仅日志，不播报） ==========
        print(f"\r当前步骤: {self.step_index+1}/{len(self.steps)} | 距离下一路口: {distance:.1f} 米", end="")
        
        # 立刻播报第一步指令
        if not self.first_step_spoken:
            first_instruction = self.clean_instruction(step["instruction"])
            self.first_step_spoken = True
            self.last_instruction = first_instruction
            return first_instruction

        # 原地停留：播报 继续前进 + 剩余距离
        now = time.time()
        if now - self.last_continue_time > CONTINUE_REMIND_INTERVAL:
            self.last_continue_time = now
            # 拼接距离文案
            return f"继续前进，距离下一个路口还有{distance:.0f}米"

        # 到达路口，播报下一步指令
        if distance < NAV_TRIGGER_DISTANCE:
            self.step_index += 1
            if self.step_index >= len(self.steps):
                return "ARRIVED"
            
            next_step = self.steps[self.step_index]
            instruction = self.clean_instruction(next_step["instruction"])
            self.last_instruction = instruction
            return instruction

        # 其他情况，不播报任何内容
        return None