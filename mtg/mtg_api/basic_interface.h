#pragma once

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef void *(*allocate_cb)(void *allocate_cb_data, size_t size);

typedef struct {
	allocate_cb allocate;
	void *data;
} allocator_t;

inline void *allocate(allocator_t const *allocator, size_t size) {
	return allocator->allocate(allocator->data, size);
}

typedef struct {
	char *data;
	size_t size;
} bytes_view;

typedef struct {
	char const *path_cards;
	char const *path_name_to_tags;
	char const *path_sets;
	char const *path_tags;
} mtg_api_args;

#ifdef __cplusplus
}
#endif
