cmake_minimum_required(VERSION 3.10)

set(project mtg_api)
project(${project})

set(sources
	database.cpp
	json.cpp
	mtg_api.cpp
)

add_library(${project} STATIC ${sources})

set(DOWNLOAD_DIR ${CMAKE_CURRENT_BINARY_DIR}/downloads)

target_include_directories(${project} PUBLIC
	$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
)

message(STATUS "Dependencies:")
message(STATUS "sudo apt install libboost-dev rapidjson-dev")
message(STATUS "")

option(BUILD_TESTS "build tests" OFF)
if (BUILD_TESTS)
	add_subdirectory(/usr/src/gtest ${CMAKE_BINARY_DIR}/build_gtest)
	include(GoogleTest)
	add_executable(mtg_api_test mtg_api_test.cpp)

	target_link_libraries(${project}_test ${project})
	target_link_libraries(${project}_test gtest gtest_main)
	gtest_add_tests(
		TARGET ${project}_test
		TEST_LIST mtg_api_test
	)
endif()

target_compile_features(${project} PRIVATE cxx_std_17)
target_compile_options(${project} PRIVATE -pthread -O2 -Werror -Wall -Wextra
	-Wno-unused-parameter
	-Wpedantic
	-fdiagnostics-generate-patch)
set_property(TARGET ${project} PROPERTY POSITION_INDEPENDENT_CODE ON)

option(BUILD_NGINX_MODULE "build nginx module" OFF)
if (BUILD_NGINX_MODULE)
	add_subdirectory(nginx)
else()
	message(STATUS "Not building nginx module.")
endif()


