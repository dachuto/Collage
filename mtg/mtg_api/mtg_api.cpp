#include <memory>
#include <string>
#include <string_view>

#include "mtg_api.h"

#include "database.hpp"
#include "json.hpp"
#include "web.hpp"

void *construct(mtg_api_args const *args) {
	try {
		auto temp = std::make_unique<mtg_api::database>();
		*temp = mtg_api::read(*args);
		return temp.release();
	} catch (...) {
		return nullptr;
	}
}

void destroy(void *p) {
	delete static_cast<mtg_api::database*>(p);
}

mtg_api::database const &as_database(void *p) {
	return *static_cast<mtg_api::database const *>(p);
}

bytes_view f1(mtg_api::database const &database, allocator_t allocator, std::string_view const &args) {
	return mtg_api::to_json{allocator}.write(database);
}

bytes_view f2(mtg_api::database const &database, allocator_t allocator, std::string_view const &args) {
	std::vector<int> what_to_output;
	what_to_output.reserve(512);

	auto const card_to_multiverse_id = [](mtg_api::unique_card const &card) {
		return *std::crbegin(card.printings); //we assume there is always at least one printing
	};

	auto const handle_query = [&](std::string_view const &key, std::string_view const &value) {
		//TODO(boost 1.68) : here we construct std::string just to find
		if (key == "set") {
			auto const it = database.card_sets.find(std::string(value));
			if (it != std::cend(database.card_sets)) {
				std::copy(std::cbegin(it->second.printings), std::cend(it->second.printings), std::back_inserter(what_to_output));
			}
		} else if (key == "tag") {
			try {
				mtg_api::tag_id const tag_id = std::stoi(std::string(value)); //TODO(std::from_chars): help us
				auto const it = database.tags.find(tag_id);
				if (it != std::cend(database.tags)) {
					for (auto const &ci : it->second.card_iterators) {
						what_to_output.push_back(card_to_multiverse_id(ci->second));
					}
				}
			} catch (...) {
				//
			}
		}
	};

	mtg_api::args_into_decoded_pairs(args, handle_query);

	if (not what_to_output.empty()) {
		return mtg_api::to_json{allocator}.write(what_to_output.data(), what_to_output.data() + what_to_output.size());
	}
	return {nullptr, 0};
}

bytes_view mtg_api_f1(void *p, allocator_t allocator, char const *args, size_t args_len) {
	return f1(as_database(p), allocator, {args, args_len});
}

bytes_view mtg_api_f2(void *p, allocator_t allocator, char const *args, size_t args_len) {
	return f2(as_database(p), allocator, {args, args_len});
}
