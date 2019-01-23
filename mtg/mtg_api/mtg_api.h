#pragma once

#include "basic_interface.h"

#ifdef __cplusplus
extern "C" {
#endif

void *construct(interface_from_c_to_cpp_t const *interface, mtg_api_args const *args);
void destroy(void *p);

typedef bytes_view (*cpp_api_function)(void *p, interface_from_c_to_cpp_t const *interface, char const *args, size_t args_len);

bytes_view mtg_api_f1(void *p, interface_from_c_to_cpp_t const *interface, char const *args, size_t args_len);
bytes_view mtg_api_f2(void *p, interface_from_c_to_cpp_t const *interface, char const *args, size_t args_len);

#ifdef __cplusplus
}
#endif
