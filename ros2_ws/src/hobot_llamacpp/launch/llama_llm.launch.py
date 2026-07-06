# Copyright (c) 2024，D-Robotics.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
# 导入ROS2 launch依赖
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch_ros.actions import Node
from launch.substitutions import TextSubstitution
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python import get_package_share_directory
from ament_index_python.packages import get_package_prefix
# 定义可配置参数
def generate_launch_description():

    # args that can be set from the command line or a default will be used
    gguf_file_name_launch_arg = DeclareLaunchArgument(
        "llamacpp_gguf_model_file_name", default_value=TextSubstitution(text="Qwen2.5-0.5B-Instruct-Q4_0.gguf")
    )
    user_prompt_launch_arg = DeclareLaunchArgument(
        "llamacpp_user_prompt", default_value=TextSubstitution(text="")
    )
    system_prompt_launch_arg = DeclareLaunchArgument(
        "llamacpp_system_prompt", default_value=TextSubstitution(text="config/system_prompt.txt")
    )
    text_msg_pub_name_launch_arg = DeclareLaunchArgument( #大模型输出回答，发给TTS的topic
        "llamacpp_text_msg_pub_name", default_value=TextSubstitution(text="/tts_text")
    )
    prompt_msg_sub_name_launch_arg = DeclareLaunchArgument(# ASR识别结果，发给大模型的topic
        "llamacpp_prompt_msg_sub_name", default_value=TextSubstitution(text="/prompt_text")
    )
    audio_asr_model_launch_arg = DeclareLaunchArgument( #ASR模型文件名
        "audio_asr_model", default_value=TextSubstitution(text="sense-voice-small-fp16.gguf")
    )
    audio_device_launch_arg = DeclareLaunchArgument( #音频设备
        "audio_device", default_value=TextSubstitution(text="plughw:0,0")
    )
# 判断使用云端ASR/TTS还是本地ASR/TTS，默认使用本地ASR/TTS
    asr_type = os.getenv('ASR_TYPE')
    print("asr_type is ", asr_type)
    tts_type = os.getenv('TTS_TYPE')
    print("tts_type is ", tts_type)

    asr_node = None
    tts_node = None
#启动ASR节点：打开麦克风，听人说话，将识别文字结果发布到指定/prompt_text 话题
    if asr_type == "cloud": #云端
        asr_node = Node(
            package='aliyun_asr_node',
            executable='asr_node',
            output='screen',
            parameters=[
                {"audio_device": LaunchConfiguration('audio_device')},
                {"pub_topic_name": LaunchConfiguration('llamacpp_prompt_msg_sub_name')},
                {"pub_awake_keyword": False}
            ],
            arguments=['--ros-args', '--log-level', 'warn']
        )
    else:
        asr_node = Node( #本地
            package='sensevoice_ros2',
            executable='sensevoice_ros2',
            output='screen',
            parameters=[
                {"push_wakeup": 1},
                {"asr_model": LaunchConfiguration('audio_asr_model')},
                {"asr_pub_topic_name": LaunchConfiguration(
                    'llamacpp_prompt_msg_sub_name')},
                {"micphone_name": LaunchConfiguration('audio_device')}
            ],
            arguments=['--ros-args', '--log-level', 'warn']
        )
# 启动TTS节点，订阅话题/tts_text，拿到大模型的回答文本后进行语音合成并播放
    if tts_type == "cloud":
        tts_node = Node(
            package='aliyun_tts_node',
            executable='aliyun_tts_node',
            output='screen',
            parameters=[
                {"tts_method": "sambert"},
                {"text_topic": "/tts_text"},
                {"cosy_voice": "longjielidou"},
                {"audio_device": LaunchConfiguration('audio_device')}
            ],
            arguments=['--ros-args', '--log-level', 'info']
        )
    else:
        tts_node = Node(
            package='hobot_tts',
            executable='hobot_tts',
            output='screen',
            parameters=[
                {"playback_device": LaunchConfiguration('audio_device')}
            ],
            arguments=['--ros-args', '--log-level', 'warn']
        )

    # 算法pkg，启动大模型节点
    llama_node = Node(
        package='hobot_llamacpp',
        executable='hobot_llamacpp',
        output='screen',
        parameters=[
            {"feed_type": 2}, #纯文本对话
            {"llm_threads": 6},
            {"user_prompt": LaunchConfiguration('llamacpp_user_prompt')},
            {"system_prompt": LaunchConfiguration('llamacpp_system_prompt')},
            {"cute_words": "我来啦"}, #启动后说的第一句话
            {"text_msg_pub_topic_name": LaunchConfiguration('llamacpp_text_msg_pub_name')}, #大模型回答文本发布话题/tts_text
            {"ros_string_sub_topic_name": LaunchConfiguration('llamacpp_prompt_msg_sub_name')}, #ASR识别结果订阅话题/prompt_text
            {"llm_model_name": LaunchConfiguration('llamacpp_gguf_model_file_name')} #gguf模型文件名
        ],
        arguments=['--ros-args', '--log-level', 'warn']
    )
# 将所有节点和参数组合成一个LaunchDescription对象并返回
    return LaunchDescription([
        gguf_file_name_launch_arg,
        user_prompt_launch_arg,
        system_prompt_launch_arg,
        text_msg_pub_name_launch_arg,
        prompt_msg_sub_name_launch_arg,
        audio_asr_model_launch_arg,
        audio_device_launch_arg,
        # asr 节点
        asr_node,
        # 启动llamacpp pkg
        llama_node,
        # 启动 tts pkg
        tts_node
    ])
