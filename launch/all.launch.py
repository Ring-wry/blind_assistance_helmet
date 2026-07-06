from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    audio_device_arg = DeclareLaunchArgument("audio_device", default_value="plughw:1,0")

    # ========== 硬件&语音底层：全局仅启动一份 ==========
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

    # ASR语音识别（唯一）
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

    # TTS语音播报（唯一，根治重复播报根源）
    tts_node = Node(
        package='hobot_tts',
        executable='hobot_tts',
        name='tts',
        parameters=[
            {"playback_device": "plughw:1,0"}
        ],
        output='screen'
    )

    # ========== 业务1：导盲障碍物检测 ==========
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

    # ========== 业务2：豆包图像大模型问答 ==========
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
        name='vision_controller_llm',
        output='screen'
    )

    # ========== 业务3：语音导航全套（新增） ==========
    # 导航语音交互控制器（唤醒词“导航”）
    nav_voice_controller = Node(
        package='voice_navigation',
        executable='voice_controller_node',
        name='voice_controller_node',
        output='screen'
    )
    # 导航核心GPS/百度地图/MQTT上报节点
    nav_core_node = Node(
        package='voice_navigation',
        executable='navigator_node',
        name='navigator_node',
        output='screen'
    )

    return LaunchDescription([
        audio_device_arg,
        # 硬件底层
        usb_cam_node,
        asr_node,
        tts_node,
        # 导盲视觉
        blind_detector_node,
        blind_controller_node,
        # LLM图像问答
        llm_analyzer_node,
        llm_controller_node,
        # 导航模块
        nav_voice_controller,
        nav_core_node
    ])