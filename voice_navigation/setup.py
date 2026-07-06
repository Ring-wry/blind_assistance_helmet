from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'voice_navigation'

setup(
    name=package_name,
    version='0.0.0',
    # 自动发现所有子包（gps/map/utils 都会被包含）
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # 安装所有 launch 文件
        (os.path.join('share', package_name, 'launch'),
         glob(os.path.join('launch', '*'))),
    ],
    install_requires=['setuptools'],
    zip_safe=False,  # ROS2 推荐设为 False，避免导入问题
    maintainer='root',
    maintainer_email='root@todo.todo',
    description='Voice navigation with ASR+TTS+GPS for RDK X5',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'navigator_node = voice_navigation.navigator_node:main',
        'voice_controller_node = voice_navigation.voice_controller_node:main',
        ],
    },
)