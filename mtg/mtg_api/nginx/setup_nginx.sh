#!/usr/bin/env bash
if [[ $# -ne 2 ]] ; then
	echo "wrong number of arguments"
	exit 1
fi

NGINX_WORKSPACE_DIR=${1}
NGINX_MODULE_SRC_DIR=${2}

NGINX_VERSION="nginx-1.15.2"

wget http://nginx.org/download/${NGINX_VERSION}.tar.gz && tar xzvf ${NGINX_VERSION}.tar.gz && mv ${NGINX_VERSION} nginx
wget http://www.zlib.net/zlib-1.2.11.tar.gz && tar xzvf zlib-1.2.11.tar.gz
git clone https://github.com/openssl/openssl.git
cd nginx
./configure --prefix=${NGINX_WORKSPACE_DIR} --with-openssl=../openssl --with-http_ssl_module --with-zlib=../zlib-1.2.11/ --with-compat --add-dynamic-module=${NGINX_MODULE_SRC_DIR} --without-http_rewrite_module
make -f objs/Makefile binary # we want custom cpp build for our module; only binary here

