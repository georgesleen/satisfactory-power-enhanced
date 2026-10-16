find_package(nlohmann_json 3.11 REQUIRED)
find_package(Python3 COMPONENTS Interpreter REQUIRED)

add_executable(ep-balance
  Source/Main.cpp
  Source/Model.cpp
  Source/Layout.cpp
  Source/Pulse.cpp
)
target_link_libraries(ep-balance PRIVATE enhanced_power_core nlohmann_json::nlohmann_json)

add_test(NAME enhanced_power_balance_scenarios
  COMMAND ep-balance --tuning "${CMAKE_CURRENT_SOURCE_DIR}/tuning.json" "${CMAKE_CURRENT_SOURCE_DIR}/scenarios"
)

add_test(NAME enhanced_power_balance_gates
  COMMAND "${Python3_EXECUTABLE}" -B "${CMAKE_CURRENT_SOURCE_DIR}/test_report.py" $<TARGET_FILE:ep-balance>
)
add_test(NAME enhanced_power_building_extraction
  COMMAND "${Python3_EXECUTABLE}" -B "${CMAKE_CURRENT_SOURCE_DIR}/test_extract_buildings.py"
)
