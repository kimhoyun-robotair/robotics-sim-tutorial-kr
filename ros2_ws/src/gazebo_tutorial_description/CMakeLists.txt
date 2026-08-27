cmake_minimum_required(VERSION 3.8)
project(gazebo_tutorial_description)

find_package(ament_cmake REQUIRED)

# Xacro/URDF files are consumed at runtime by launch files and
# robot_state_publisher, so install the complete description directory.
install(
  DIRECTORY urdf
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
