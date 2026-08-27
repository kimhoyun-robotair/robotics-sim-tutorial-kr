from glob import glob
import os

from setuptools import find_packages, setup


package_name = 'gazebo_tutorial_bringup'


setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'rviz'), glob('rviz/*.rviz')),
        (os.path.join('share', package_name, 'worlds'), glob('worlds/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='kimhoyun-robotair',
    maintainer_email='kimhoyun.robotair@gmail.com',
    description=(
        'Reusable Gazebo Classic launch files and RViz presets for the tutorial robots.'
    ),
    license='Apache-2.0',
    tests_require=['pytest'],
)
