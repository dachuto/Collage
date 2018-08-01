cmake_minimum_required(VERSION 3.10)

set(project mtg_api_module)
project(${project})

file(MAKE_DIRECTORY ${DOWNLOAD_DIR})
set(NGINX_SOURCE_DIR ${DOWNLOAD_DIR}/nginx)

set(NGINX_MODULE_NAME mtg_api_module)
set(NGINX_GENERATED_SOURCE ${NGINX_SOURCE_DIR}/objs/${NGINX_MODULE_NAME}_modules.c)
set(NGINX_BINARY ${NGINX_SOURCE_DIR}/objs/nginx)

add_custom_command(
	OUTPUT ${NGINX_BINARY} ${NGINX_GENERATED_SOURCE}
	COMMAND ${CMAKE_CURRENT_SOURCE_DIR}/setup_nginx.sh ${CMAKE_INSTALL_PREFIX} ${CMAKE_CURRENT_SOURCE_DIR}
	WORKING_DIRECTORY ${DOWNLOAD_DIR}
	VERBATIM
)

add_custom_command(
	OUTPUT ${DOWNLOAD_DIR}/AllSets.json
	COMMAND ${CMAKE_CURRENT_SOURCE_DIR}/mtg_api_download.sh
	WORKING_DIRECTORY ${DOWNLOAD_DIR}
	VERBATIM
)

message(STATUS "nginx ./configure also generates a C file in objs/ directory with module declaration.")
message(STATUS "Generated file is: ${NGINX_GENERATED_SOURCE}")

add_library(${project} MODULE ${NGINX_GENERATED_SOURCE} mtg_api_module.c)
set_target_properties(${project} PROPERTIES PREFIX "") # do not add lib prefix (nginx modules do not want it)
target_link_libraries(${project} mtg_api)

message(STATUS "Internal include directories are manually taken from nginx's Makefile; beware changes")
target_include_directories(${project} PRIVATE
	${NGINX_SOURCE_DIR}/src/core/
	${NGINX_SOURCE_DIR}/src/event/
	${NGINX_SOURCE_DIR}/src/event/modules/
	${NGINX_SOURCE_DIR}/src/os/unix/
	${NGINX_SOURCE_DIR}/objs/
	${NGINX_SOURCE_DIR}/src/http/
	${NGINX_SOURCE_DIR}/src/http/modules/
)

target_include_directories(${project} SYSTEM PRIVATE
	${NGINX_SOURCE_DIR}/../openssl/include/
)

install(PROGRAMS ${NGINX_BINARY} DESTINATION sbin)
install(FILES nginx.conf DESTINATION conf)
install(TARGETS ${project} DESTINATION modules)

install(FILES ${DOWNLOAD_DIR}/AllCards-x.json DESTINATION .)
install(FILES ${DOWNLOAD_DIR}/AllSets.json DESTINATION .)
install(FILES ${CMAKE_CURRENT_SOURCE_DIR}/../name_to_tags.json DESTINATION .)
install(FILES ${CMAKE_CURRENT_SOURCE_DIR}/../tags.json DESTINATION .)

add_custom_target(run_nginx
	COMMAND ${CMAKE_CURRENT_SOURCE_DIR}/nginx_runtime.sh
	WORKING_DIRECTORY ${CMAKE_INSTALL_PREFIX}
	VERBATIM
)

