#pragma once

#include "basic_interface.h"

#ifdef __cplusplus
extern "C" {
#endif

void *construct(mtg_api_args const *args);
void destroy(void *p);

bytes_view mtg_api_f1(void *p, allocator_t allocator, char const *args, size_t args_len);
bytes_view mtg_api_f2(void *p, allocator_t allocator, char const *args, size_t args_len);

#ifdef __cplusplus
}
#endif
