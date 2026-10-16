# Host build of the engine-free simulation core, its tests, and the balance tool.
cmake_minimum_required(VERSION 3.25)
project(EnhancedPower LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

add_compile_options(-Wall -Wextra -Wpedantic -Wshadow -Werror)

file(GLOB CORE_SOURCES CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/Source/EnhancedPowerCore/Private/*.cpp")
list(FILTER CORE_SOURCES EXCLUDE REGEX "Module\\.cpp$")

add_library(enhanced_power_core STATIC ${CORE_SOURCES})
target_include_directories(enhanced_power_core PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}/Source/EnhancedPowerCore/Public")

find_package(doctest REQUIRED)

file(GLOB CORE_TEST_SOURCES CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/Tests/Core/*.cpp")

add_executable(enhanced_power_core_tests ${CORE_TEST_SOURCES})
target_link_libraries(enhanced_power_core_tests PRIVATE enhanced_power_core doctest::doctest)

enable_testing()
add_test(NAME enhanced_power_core_tests COMMAND enhanced_power_core_tests)

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/tools/balance/CMakeLists.txt")
  add_subdirectory(tools/balance)
endif()
