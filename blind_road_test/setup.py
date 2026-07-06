from setuptools import setup
import os
from glob import glob

package_name = 'blind_road_test'

setup(
    name=package_name,
    version='0.0.0',
    # 强制指定包名，跳过 find_packages() 的坑
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='root',
    maintainer_email='root@todo.todo',
    description='Blind Road Detection Package',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            # 这里必须和你的节点文件名完全对应
            'blind_road_detector = blind_road_test.blind_road_detector:main',
            'vision_controller = blind_road_test.vision_controller:main',
            'blind_road_ocr = blind_road_test.blind_road_ocr:main',
            'vision_controller2 = blind_road_test.vision_controller2:main',
        ],
    },
)