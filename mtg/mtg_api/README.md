# HTTP server for MtG queries

We read text data and preprocess it at startup. Data can be collected from paring existing sources like gatherer or currently even easier downloaded from mtgjson.com.

Core code is written in C++ and then exposed as C nginx module. Only allocator API is passed from nginx. Module is compiled by separate CMake script i.e. nginx build script is not used for better control over C++ compilation.

To utilize memory one process and multiple worker threads should be fine. Requests don't modify internal state so can be processed in parallel.

Basic nginx info:

run (with this setup one doesn't need root):
```
./sbin/nginx
./sbin/nginx -s stop
```

## TODO: move to script and test on clean install
git clone https://github.com/nginx/nginx.git
wget http://www.zlib.net/zlib-1.2.11.tar.gz && tar xzvf zlib-1.2.11.tar.gz
git clone https://github.com/openssl/openssl.git
cd nginx
./configure --prefix=${1} --with-openssl=../openssl --with-http_ssl_module --with-zlib=../zlib-1.2.11/ --with-compat #--add-dynamic-module=...

./conf/nginx.conf