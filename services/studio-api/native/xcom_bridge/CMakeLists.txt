cmake_minimum_required(VERSION 3.22)
project(studio_native_xcom_bridge LANGUAGES CXX)

# Contributor/host inputs only. No project or runtime request selects these paths.
foreach(input PLATFORM_SOURCE PLATFORM_BUILD THIRD_PARTY_INCLUDE)
  if(NOT DEFINED ${input})
    message(FATAL_ERROR "Missing explicit admitted native build input: ${input}")
  endif()
endforeach()
find_package(Threads REQUIRED)
add_executable(studio_native_xcom_bridge bridge.cpp)
target_compile_features(studio_native_xcom_bridge PRIVATE cxx_std_20)
set_target_properties(studio_native_xcom_bridge PROPERTIES
  CXX_STANDARD 20 CXX_STANDARD_REQUIRED ON CXX_EXTENSIONS OFF)
target_include_directories(studio_native_xcom_bridge PRIVATE
  "${PLATFORM_SOURCE}/src/xverse/xcom/include")
target_include_directories(studio_native_xcom_bridge SYSTEM PRIVATE "${THIRD_PARTY_INCLUDE}")
target_compile_options(studio_native_xcom_bridge PRIVATE
  -Wall -Wextra -Wpedantic -Wconversion -Wsign-conversion -Wshadow -Werror)
target_link_libraries(studio_native_xcom_bridge PRIVATE
  "${PLATFORM_BUILD}/src/xverse/xcom/libxverse_xcom_provider_loopback.a"
  "${PLATFORM_BUILD}/src/xverse/xcom/libxverse_xcom_endpoint_route_lifecycle.a"
  "${PLATFORM_BUILD}/src/xverse/xcom/libxverse_xcom_observation.a"
  "${PLATFORM_BUILD}/src/xverse/xcom/libxverse_xcom_core_types.a"
  Threads::Threads)
