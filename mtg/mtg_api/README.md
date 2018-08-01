# HTTP server for MtG queries

We read text data and preprocess it at startup. Data can be collected from paring existing sources like gatherer or currently even easier downloaded from mtgjson.com.

Core code is written in C++ and then exposed as C nginx module. Only allocator API is passed from nginx. Module is compiled by separate CMake script i.e. nginx build script is not used for better control over C++ compilation.

To utilize memory one process and multiple worker threads should be fine. Requests don't modify internal state so can be processed in parallel.


Build and run (with this setup one doesn't need root):
```
cmake -DBUILD_NGINX_MODULE=ON -DCMAKE_INSTALL_PREFIX=<WHERE TO PUT NGINX> <Collage/mtg/mtg_api/>
make download_json
make && make install && make run_nginx
```

