#pragma once

#include "basic_interface.h"
#include "database.hpp"

namespace mtg_api {

database read(mtg_api_args const &args);

struct to_json {
	allocator_t allocator;

	bytes_view write(std::string const &s) const;
	bytes_view write(database const &database) const;
	bytes_view write(multiverse_ids_container const &x) const;
	bytes_view write(int const *first, int const *last) const;
};

}
