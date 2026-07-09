from glob import glob
import os

from setuptools import find_packages, setup

package_name = 'r2_monitor'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'web'), glob('web/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='R2 Team',
    maintainer_email='dev@r2.local',
    description='R2 pure monitor node and web UI.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'monitor_node = r2_monitor.monitor_node:main',
        ],
    },
)
