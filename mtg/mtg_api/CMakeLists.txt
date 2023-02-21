cmake_minimum_required(VERSION 3.10)

set(project mtg_api)
project(${project})

set(CMAKE_CXX_STANDARD 17)

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

function(set_compile_options target)
	target_compile_features(${target} PRIVATE cxx_std_17)
	target_compile_options(${target} PRIVATE -pthread -O2 -Werror -Wall -Wextra
		-Wno-unused-parameter
		-Wpedantic
		-fdiagnostics-generate-patch)
	set_property(TARGET ${target} PROPERTY POSITION_INDEPENDENT_CODE ON)
endfunction()

option(BUILD_TESTS "build tests" ON)
if (BUILD_TESTS)
	include(FetchContent)
	FetchContent_Declare(
		googletest
		GIT_REPOSITORY https://github.com/google/googletest.git
		GIT_TAG        v1.13.0
	)
	set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
	FetchContent_MakeAvailable(googletest)
	include(GoogleTest)

	add_executable(mtg_api_test mtg_api_test.cpp)
	set_compile_options(${project}_test)

	target_link_libraries(${project}_test ${project})
	target_link_libraries(${project}_test GTest::gtest_main)
	gtest_add_tests(
		TARGET ${project}_test
		TEST_LIST mtg_api_test
	)
endif()


set_compile_options(${project})

add_executable(mtg_api_util mtg_api_util.cpp)
set_compile_options(mtg_api_util)
target_link_libraries(mtg_api_util mtg_api)

option(BUILD_NGINX_MODULE "build nginx module" ON)
if (BUILD_NGINX_MODULE)
	add_subdirectory(nginx)
else()
	message(STATUS "Not building nginx module.")
endif()


