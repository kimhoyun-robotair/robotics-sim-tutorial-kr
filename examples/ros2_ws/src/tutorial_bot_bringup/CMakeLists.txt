cmake_minimum_required(VERSION 3.8)
project(tutorial_bot_bringup)

find_package(ament_cmake REQUIRED)

install(DIRECTORY config launch rviz
  DESTINATION share/${PROJECT_NAME}
  PATTERN "__pycache__" EXCLUDE
)

install(PROGRAMS
  scripts/wait_localization
  scripts/odom_to_path
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
