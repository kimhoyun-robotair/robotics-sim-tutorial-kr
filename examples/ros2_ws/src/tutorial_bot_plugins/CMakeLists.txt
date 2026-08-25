cmake_minimum_required(VERSION 3.8)
project(tutorial_bot_plugins)

find_package(ament_cmake REQUIRED)

install(FILES config/diagnostics-contract.yaml
  DESTINATION share/${PROJECT_NAME}/config
)
install(FILES schema/diagnostics-contract.schema.json
  DESTINATION share/${PROJECT_NAME}/schema
)
install(FILES include/tutorial_bot_plugins/diagnostics_contract.hpp
  DESTINATION include/tutorial_bot_plugins
)

ament_export_include_directories(include)
ament_package()
