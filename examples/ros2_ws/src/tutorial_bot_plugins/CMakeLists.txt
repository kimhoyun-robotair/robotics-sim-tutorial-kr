cmake_minimum_required(VERSION 3.8)
project(tutorial_bot_plugins)

find_package(ament_cmake REQUIRED)
find_package(gz-msgs10 REQUIRED)
find_package(gz-plugin2 REQUIRED COMPONENTS register)
find_package(gz-sim8 REQUIRED)
find_package(gz-transport13 REQUIRED)

add_library(TutorialBotDiagnosticsSystem SHARED
  src/tutorial_bot_diagnostics.cpp
)
target_compile_features(TutorialBotDiagnosticsSystem PUBLIC cxx_std_17)
target_include_directories(TutorialBotDiagnosticsSystem PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)
target_link_libraries(TutorialBotDiagnosticsSystem
  gz-msgs10::gz-msgs10
  gz-plugin2::gz-plugin2-register
  gz-sim8::gz-sim8
  gz-transport13::gz-transport13
)

install(TARGETS TutorialBotDiagnosticsSystem
  LIBRARY DESTINATION lib
)

install(FILES config/diagnostics-contract.yaml
  DESTINATION share/${PROJECT_NAME}/config
)
install(FILES schema/diagnostics-contract.schema.json
  DESTINATION share/${PROJECT_NAME}/schema
)
install(FILES include/tutorial_bot_plugins/diagnostics_contract.hpp
  include/tutorial_bot_plugins/tutorial_bot_diagnostics.hpp
  DESTINATION include/tutorial_bot_plugins
)

if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)
  find_package(gz-msgs10 REQUIRED)
  find_package(gz-sim8 REQUIRED)
  find_package(gz-transport13 REQUIRED)

  foreach(test_name IN ITEMS diagnostics_distance diagnostics_model_lifecycle)
    ament_add_gtest(${test_name} test/test_${test_name}.cpp TIMEOUT 30)
    target_link_libraries(${test_name}
      gz-msgs10::gz-msgs10
      gz-sim8::gz-sim8
      gz-transport13::gz-transport13
    )
    set_tests_properties(${test_name} PROPERTIES
      ENVIRONMENT "GZ_SIM_SYSTEM_PLUGIN_PATH=${CMAKE_CURRENT_BINARY_DIR}"
    )
  endforeach()

  foreach(test_name IN ITEMS
      diagnostics_enable_reset
      diagnostics_enable_reset_concurrency)
    if(CMAKE_CXX_FLAGS MATCHES "fsanitize=thread")
      ament_add_gtest_executable(${test_name} test/test_diagnostics_enable_reset.cpp)
      set(result_file "${AMENT_TEST_RESULTS_DIR}/${PROJECT_NAME}/${test_name}.gtest.xml")
      ament_add_test(${test_name}
        COMMAND /usr/bin/setarch x86_64 -R $<TARGET_FILE:${test_name}>
          --gtest_output=xml:${result_file}
        OUTPUT_FILE "${CMAKE_BINARY_DIR}/ament_cmake_gtest/${test_name}.txt"
        RESULT_FILE "${result_file}"
        TIMEOUT 30
      )
    else()
      ament_add_gtest(${test_name} test/test_diagnostics_enable_reset.cpp TIMEOUT 30)
    endif()
    target_link_libraries(${test_name}
      gz-msgs10::gz-msgs10
      gz-sim8::gz-sim8
      gz-transport13::gz-transport13
    )
    string(TOUPPER ${test_name} test_definition)
    target_compile_definitions(${test_name} PRIVATE ${test_definition})
    if(CMAKE_CXX_FLAGS MATCHES "fsanitize=thread")
      target_compile_options(${test_name} PRIVATE -fno-pie)
      target_link_options(${test_name} PRIVATE -no-pie)
    endif()
    set_tests_properties(${test_name} PROPERTIES
      ENVIRONMENT "GZ_SIM_SYSTEM_PLUGIN_PATH=${CMAKE_CURRENT_BINARY_DIR}"
    )
  endforeach()
endif()

ament_export_include_directories(include)
ament_export_dependencies(gz-msgs10 gz-plugin2 gz-sim8 gz-transport13)
ament_export_libraries(TutorialBotDiagnosticsSystem)
ament_package()
