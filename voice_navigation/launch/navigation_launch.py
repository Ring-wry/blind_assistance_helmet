from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    audio_device_arg = DeclareLaunchArgument("audio_device", default_value="plughw:1,0")

    # ASR
    asr_node = Node(
        package='sensevoice_ros2',
        executable='sensevoice_ros2',
        name='asr',
        parameters=[{"asr_pub_topic_name": "/prompt_text", "micphone_name": LaunchConfiguration('audio_device')}],
        output='screen'
    )

    # TTS
    tts_node = Node(
        package='hobot_tts',
        executable='hobot_tts',
        name='tts',
        parameters=[{"playback_device": "plughw:1,0"}],
        output='screen'
    )

    # 语音交互节点
    voice_node = Node(
        package='voice_navigation',
        executable='voice_controller_node',
        name='voice_controller_node',
        output='screen'
    )

    # 导航核心节点
    nav_node = Node(
        package='voice_navigation',
        executable='navigator_node',
        name='navigator_node',
        output='screen'
    )

    return LaunchDescription([
        audio_device_arg,
        asr_node,
        tts_node,
        voice_node,
        nav_node
    ])