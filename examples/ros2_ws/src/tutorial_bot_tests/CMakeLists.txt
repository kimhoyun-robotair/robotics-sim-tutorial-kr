cmake_minimum_required(VERSION 3.8)
project(tutorial_bot_tests)

find_package(ament_cmake REQUIRED)

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(launch_argument_validation test_launch_argument_validation.py TIMEOUT 60)
  ament_add_pytest_test(advanced_contract test_advanced_contract.py TIMEOUT 30)
  ament_add_pytest_test(advanced_framework_cli test_advanced_framework_cli.py TIMEOUT 30)
  ament_add_pytest_test(advanced_headless_integration test_advanced_headless.py TIMEOUT 180)
  ament_add_pytest_test(run_tdd_phase test_run_tdd_phase.py TIMEOUT 30)
  ament_add_pytest_test(
    rover_examples
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../scripts/test_rover_examples.py
    TIMEOUT 30
  )
endif()

ament_package()
