from setuptools import find_packages, setup


package_name = 'gazebo_tutorial_tools'


setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='kimhoyun-robotair',
    maintainer_email='kimhoyun.robotair@gmail.com',
    description='Small ROS 2 utilities used by the Gazebo Classic Korean tutorial.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'ackermann_odom = gazebo_tutorial_tools.ackermann_odom:main',
            'odom_to_path = gazebo_tutorial_tools.odom_to_path:main',
        ],
    },
)
