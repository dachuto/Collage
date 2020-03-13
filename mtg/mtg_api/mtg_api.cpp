#include <charconv>
#include <memory>
#include <string>
#include <string_view>

#include "mtg_api.h"

#include "database.hpp"
#include "json.hpp"
#include "web.hpp"

void *construct(interface_from_c_to_cpp_t const *interface, mtg_api_args const *args) {
	try {
		auto temp = std::make_unique<mtg_api::database>();
		*temp = mtg_api::read(*args);
		{
			std::stringstream ss;
			ss << "Unique cards loaded: " << temp->unique_cards.size();
			std::string s = ss.str();
			log_error(&interface->logger, s.c_str());
		}

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

bytes_view f1(mtg_api::database const &database, interface_from_c_to_cpp_t const *interface, std::string_view const &args) {
	return mtg_api::to_json{interface->allocator}.write(database);
}

bytes_view f2(mtg_api::database const &database, interface_from_c_to_cpp_t const *interface, std::string_view const &args) {
	auto const card_to_multiverse_id = [](mtg_api::unique_card const &card) {
		return *std::crbegin(card.printings); //we assume there is always at least one printing
	};

	auto const as_int = [](std::string_view const &value) {
		int ret = 0;
		auto const [p, error] = std::from_chars(value.cbegin(), value.cend(), ret);
		if (error != std::errc()) {
			return -1; //TODO: we do not have error handling yet
		}
		return ret;
	};

	bytes_view output{nullptr, 0};

	auto const handle_query = [&](std::string_view const &key, std::string_view const &value) {
		std::vector<mtg_api::multiverse_id> ids;
		ids.reserve(16);

		auto const serializer = mtg_api::to_json{interface->allocator};

		if (key == "set") {
			auto const it = database.card_sets.find(std::string(value)); //TODO(boost 1.68) : here we construct std::string just to find
			if (it != std::cend(database.card_sets)) {
				std::copy(std::cbegin(it->second.printings), std::cend(it->second.printings), std::back_inserter(ids));
				output = serializer.write(ids.data(), ids.data() + ids.size()); //TODO: copy paste
			}
		} else if (key == "tag") {
			mtg_api::tag_id const tag_id = as_int(value);
			auto const it = database.tags.find(tag_id);
			if (it != std::cend(database.tags)) {
				for (auto const &ci : it->second.card_iterators) {
					ids.push_back(card_to_multiverse_id(ci->second));
				}
				output = serializer.write(ids.data(), ids.data() + ids.size()); //TODO: copy paste
			}
		} else if (key == "name") {
			auto const it = database.unique_cards.find(std::string(value));
			if (it != std::cend(database.unique_cards)) {
				for (auto const &id : it->second.printings) {
					ids.push_back(id);
				}
				output = serializer.write(ids.data(), ids.data() + ids.size()); //TODO: copy paste
			} else {
				log_error(&interface->logger, "No cards with that name.");
			}
		} else if (key == "multiverse_id") {
			int const id = as_int(value);
			auto const it = database.printings.find(id);
			if (it != database.printings.cend()) {
				output = serializer.write(it->second.card_iterator->first);
			}
		}
	};

	mtg_api::args_into_decoded_pairs(args, handle_query);
	return output;
}

bytes_view mtg_api_f1(void *p, interface_from_c_to_cpp_t const *interface, char const *args, size_t args_len) {
	return f1(as_database(p), interface, {args, args_len});
}

bytes_view mtg_api_f2(void *p, interface_from_c_to_cpp_t const *interface, char const *args, size_t args_len) {
	return f2(as_database(p), interface, {args, args_len});
}
