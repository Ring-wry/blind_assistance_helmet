from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    audio_device_arg = DeclareLaunchArgument("audio_device", default_value="plughw:1,0")

    # ========== 硬件&语音模块：只启动一次，全局单例 ==========
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

    # ASR语音识别 仅1个
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

    # TTS播报 仅1个，解决重复播报根源
    tts_node = Node(
        package='hobot_tts',
        executable='hobot_tts',
        name='tts',
        parameters=[
            {"playback_device": "plughw:1,0"}
        ],
        output='screen'
    )

    # ========== 业务1：导盲道路检测整套 ==========
    blind_detector_node = Node(
        package='blind_road_test',
        executable='blind_road_detector',
        name='blind_road_detector',
        output='screen'
    )
    blind_controller_node = Node(
        package='blind_road_test',
        executable='vision_controller',
        name='vision_controller_blind',
        output='screen'
    )

    # ========== 业务2：豆包图像对话API整套 ==========
    llm_analyzer_node = Node(
        package='image_upload_analyzer',
        executable='image_upload_analyzer',
        name='image_upload_analyzer',
        parameters=[{
            "ark_api_key": "da3e46cb-2625-44dc-933b-c3006e294499"
        }],
        output='screen'
    )
    llm_controller_node = Node(
        package='image_upload_analyzer',
        executable='vision_controller',
        name='vision_controller_llm',  # 改名，避免和导盲控制器重名冲突
        output='screen'
    )

    return LaunchDescription([
        audio_device_arg,
        # 硬件语音层
        usb_cam_node,
        asr_node,
        tts_node,
        # 导盲业务
        blind_detector_node,
        blind_controller_node,
        # LLM对话业务
        llm_analyzer_node,
        llm_controller_node
    ])