cmake_minimum_required(VERSION 3.10)

set(project mtg_api_module)
project(${project})

file(MAKE_DIRECTORY ${DOWNLOAD_DIR})
set(NGINX_SOURCE_DIR ${DOWNLOAD_DIR}/nginx)

set(NGINX_MODULE_NAME mtg_api_module)
set(NGINX_GENERATED_SOURCE ${NGINX_SOURCE_DIR}/objs/${NGINX_MODULE_NAME}_modules.c)
set(NGINX_BINARY ${NGINX_SOURCE_DIR}/objs/nginx)


set(NGINX_VERSION nginx-1.22.1)
set(ZLIB_VERSION zlib-1.2.13)

function(wget_and_unpack url filename working_dir unpacked_dir_name new_dir_name)
	add_custom_command(
		OUTPUT ${working_dir}/${filename}
		COMMAND wget ${url}/${filename}
		WORKING_DIRECTORY ${working_dir}
		VERBATIM
	)

	add_custom_command(
		DEPENDS ${working_dir}/${filename}
		OUTPUT ${working_dir}/${new_dir_name}
		COMMAND tar xzvf ${filename}
		COMMAND mv ${unpacked_dir_name} ${new_dir_name}
		WORKING_DIRECTORY ${working_dir}
		VERBATIM
	)
endfunction()

wget_and_unpack(http://nginx.org/download ${NGINX_VERSION}.tar.gz  ${DOWNLOAD_DIR} ${NGINX_VERSION} nginx)
wget_and_unpack(http://www.zlib.net ${ZLIB_VERSION}.tar.gz ${DOWNLOAD_DIR} ${ZLIB_VERSION} zlib)

add_custom_command(
	OUTPUT ${DOWNLOAD_DIR}/openssl
	COMMAND git clone --depth=1 https://github.com/openssl/openssl.git
	WORKING_DIRECTORY ${DOWNLOAD_DIR}
	VERBATIM
)

add_custom_command(
	DEPENDS ${DOWNLOAD_DIR}/nginx ${DOWNLOAD_DIR}/openssl ${DOWNLOAD_DIR}/zlib
	OUTPUT ${DOWNLOAD_DIR}/nginx/objs/Makefile ${NGINX_GENERATED_SOURCE}
	COMMAND ./configure --prefix=${CMAKE_INSTALL_PREFIX} --with-openssl=../openssl --with-http_ssl_module --with-zlib=../zlib/ --with-compat --add-dynamic-module=${CMAKE_CURRENT_SOURCE_DIR} --without-http_rewrite_module
	COMMENT "nginx configure"
	WORKING_DIRECTORY ${DOWNLOAD_DIR}/nginx
	VERBATIM
)

# we want custom cpp build for our module; only binary here
add_custom_target(nginx_slow_build)

add_custom_command(
	TARGET nginx_slow_build PRE_BUILD
	COMMENT "nginx build (slow)"
	DEPENDS ${DOWNLOAD_DIR}/nginx/objs/Makefile
	COMMAND make -f objs/Makefile binary
	WORKING_DIRECTORY ${DOWNLOAD_DIR}/nginx
	VERBATIM
)

function(download_and_unzip url filename working_dir)
	add_custom_command(
		OUTPUT ${working_dir}/${filename}
		COMMAND wget ${url}/${filename}.zip
		COMMAND unzip -ao ${filename}.zip
		BYPRODUCTS ${working_dir}/${filename}.zip
		WORKING_DIRECTORY ${working_dir}
		VERBATIM
	)
endfunction()

set(MTG_JSON_FILES
	AtomicCards.json
	AllPrintings.json
)

foreach(X IN LISTS MTG_JSON_FILES)
	download_and_unzip(https://mtgjson.com/api/v5 ${X} ${DOWNLOAD_DIR})
endforeach()

message(STATUS "nginx ./configure also generates a C file in objs/ directory with module declaration.")
message(STATUS "Generated file is: ${NGINX_GENERATED_SOURCE}")

add_library(${project} MODULE ${NGINX_GENERATED_SOURCE} mtg_api_module.c)

set_target_properties(${project} PROPERTIES PREFIX "") # do not add lib prefix (nginx modules do not want it)
target_link_libraries(${project} mtg_api)

set(MTG_JSON_FILES_DOWNLOADED "")
foreach(X IN LISTS MTG_JSON_FILES)
	list(APPEND MTG_JSON_FILES_DOWNLOADED "${DOWNLOAD_DIR}/${X}")
endforeach()

add_custom_target(json_data DEPENDS ${MTG_JSON_FILES_DOWNLOADED})

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

foreach(X IN LISTS MTG_JSON_FILES)
	install(FILES "${DOWNLOAD_DIR}/${X}" DESTINATION .)
endforeach()
#install(FILES ${DOWNLOAD_DIR}/AllCards.json DESTINATION .)
#install(FILES ${DOWNLOAD_DIR}/AllPrintings.json DESTINATION .)
install(FILES ${CMAKE_CURRENT_SOURCE_DIR}/../name_to_tags.json DESTINATION .)
install(FILES ${CMAKE_CURRENT_SOURCE_DIR}/../tags.json DESTINATION .)

add_custom_target(run_nginx
	COMMAND ${CMAKE_CURRENT_SOURCE_DIR}/nginx_runtime.sh
	WORKING_DIRECTORY ${CMAKE_INSTALL_PREFIX}
	VERBATIM
)

