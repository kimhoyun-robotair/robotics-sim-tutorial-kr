cmake_minimum_required(VERSION 3.8)
project(gazebo_tutorial_plugins)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(ament_cmake REQUIRED)
find_package(gazebo_dev REQUIRED)
find_package(gazebo_ros REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(rclcpp REQUIRED)

# gazebo_dev가 Gazebo Classic 11의 비표준 라이브러리 검색 경로를 제공한다.
link_directories(${gazebo_dev_LIBRARY_DIRS})

add_library(ground_truth_path_plugin SHARED
  src/ground_truth_path_plugin.cpp
)
target_include_directories(ground_truth_path_plugin
  PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)
target_compile_options(ground_truth_path_plugin PRIVATE
  -Wall -Wextra -Wpedantic
)
ament_target_dependencies(ground_truth_path_plugin
  gazebo_dev
  gazebo_ros
  geometry_msgs
  nav_msgs
  rclcpp
)

install(
  TARGETS ground_truth_path_plugin
  EXPORT export_ground_truth_path_plugin
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)
install(
  DIRECTORY include/
  DESTINATION include
)
install(
  DIRECTORY urdf/
  DESTINATION share/${PROJECT_NAME}/urdf
)
install(
  FILES README.md
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)

  ament_add_gtest(test_path_recorder_config
    test/test_path_recorder_config.cpp
  )
  target_include_directories(test_path_recorder_config PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
  )
endif()

ament_export_include_directories(include)
ament_export_targets(export_ground_truth_path_plugin HAS_LIBRARY_TARGET)
ament_export_dependencies(gazebo_dev gazebo_ros geometry_msgs nav_msgs rclcpp)
ament_package()
