import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration

def generate_launch_description():

    audio_device_arg = DeclareLaunchArgument("audio_device", default_value="plughw:1,0")

    # USB摄像头
    usb_cam_node = Node(
        package='hobot_usb_cam',
        executable='hobot_usb_cam',
        name='usb_cam',
        parameters=[
            {"usb_image_width": 640},
            {"usb_image_height": 480},
            {"usb_video_device": "/dev/video0"},
            {"enable_shared_mem": True},
            {"image_pub_topic": "/image"}
        ],
        output='screen'
    )

    # ASR语音识别
    asr_node = Node(
        package='sensevoice_ros2',
        executable='sensevoice_ros2',
        name='asr',
        parameters=[
            {"asr_pub_topic_name": "/prompt_text"},
            {"micphone_name": LaunchConfiguration('audio_device')}
        ],
        output='screen'
    )

    # --------------------- 替换成：盲道检测节点 ---------------------
    image_ai_node = Node(
        package='blind_road_test',
        executable='blind_road_detector',
        name='blind_road_detector',
        output='screen'
    )

    # 视觉控制器（你原来的，完全不用改！）
    vision_controller_node = Node(
        package='blind_road_test',
        executable='vision_controller',
        name='vision_controller',
        output='screen'
    )

    # TTS播报
    tts_node = Node(
        package='hobot_tts',
        executable='hobot_tts',
        name='tts',
        parameters=[
            {"playback_device": "plughw:1,0"}
        ],
        output='screen'
    )

    return LaunchDescription([
        audio_device_arg,
        usb_cam_node,
        asr_node,
        image_ai_node,
        vision_controller_node,
        tts_node
    ])