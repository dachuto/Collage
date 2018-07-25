cmake_minimum_required(VERSION 3.10)

set(project mtg_api)
project(${project})

set(sources
	database.cpp
	json.cpp
	mtg_api.cpp
)

add_library(${project} STATIC ${sources})
set_target_properties(${project} PROPERTIES PUBLIC_HEADER mtg_api.h)

#set(BUILD_TESTS OFF)
set(NGINX_SOURCE_DIR "/mnt/storage/DUPA_nginx/nginx-1.15.0") #TODO : ASK USER!
set(NGINX_MODULE_NAME mtg_api_module)
set(NGINX_GENERATED_SOURCE ${NGINX_SOURCE_DIR}/objs/${NGINX_MODULE_NAME}_modules.c)

message(STATUS "./configure --add-dynamic-module=...")
message(STATUS "This command also generates a C file in objs/ directory with module declaration.")
message(STATUS "Generated file is: ${NGINX_GENERATED_SOURCE}")

add_library(${project}_module MODULE ${NGINX_GENERATED_SOURCE} mtg_api_module.c)
set_target_properties(${project}_module PROPERTIES PREFIX "")
target_link_libraries(${project}_module ${project})
message(STATUS "Internal include directories are manually taken from nginx's Makefile; beware changes")
target_include_directories(${project}_module PRIVATE
	${NGINX_SOURCE_DIR}/src/core/
	${NGINX_SOURCE_DIR}/src/event/
	${NGINX_SOURCE_DIR}/src/event/modules/
	${NGINX_SOURCE_DIR}/src/os/unix/
	${NGINX_SOURCE_DIR}/objs/
	${NGINX_SOURCE_DIR}/src/http/
	${NGINX_SOURCE_DIR}/src/http/modules/
)

target_include_directories(${project}_module SYSTEM PRIVATE
	${NGINX_SOURCE_DIR}/../openssl/include/
)

add_subdirectory(/usr/src/gtest ${CMAKE_BINARY_DIR}/build_gtest)
include(GoogleTest)
add_executable(mtg_api_test mtg_api_test.cpp)

target_link_libraries(${project}_test ${project})
target_link_libraries(${project}_test gtest gtest_main)
gtest_add_tests(
	TARGET ${project}_test
	TEST_LIST mtg_api_test
)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fPIC -std=c++17 -pthread -O2 -Werror -Wall -Wextra\
	-Wno-unused-parameter\
	-Wpedantic\
	-fdiagnostics-generate-patch")
