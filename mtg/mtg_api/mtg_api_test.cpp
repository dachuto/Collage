#include "gtest/gtest.h"

#include "database.hpp"
#include "json.hpp"

#include "web.hpp"

namespace mtg_api {

void *allocate_with_new(void *data, size_t size) {
	return new char[size];
}

TEST(mtg_api_test, works) {


	auto const database = read({"./AtomicCards.json", "./AllPrintings.json", "./AllPricesToday.json"});
	if (false) {
		allocator_t a{allocate_with_new, nullptr};
		auto ret = to_json{a}.write(database);
		std::string s(ret.data, ret.size);
		std::cout << s << "\n";
	}

	if (false) {
		for (auto const &kv: database.multiverse_id_to_set_printing) {
			std::cout << kv.first;
			std::cout << " [ " << kv.second.collector_number << ", " << kv.second.set_code;
			std::cout << " ]\n";
		}
	}

	if (false) {
		for (auto const &kv: database.card_sets) {
			std::cout << kv.first << "\n";
			for (auto const &id : kv.second.cards_by_collector_number) {
				std::cout << id.second << " ";
			}
			std::cout << "\n";
		}
	}

	auto const it = database.card_name_to_multiverse_id.find(std::string("Fog"));
	if (it != database.card_name_to_multiverse_id.end()) {
		for (auto const &id : it->second) {
			std::cout << "multiverseId for Fog: " << id << "\n";
		}
	}

	// mtg_api_f2(&d, a, "x=1&y=2", 7);
	// auto const print_it = [](std::string_view const &key, std::string_view const &value) {
	// 	std::cout << key << " = " << value << "\n";
	// };
	// split_into_key_value("x=1&y=2", print_it);

	// args_into_decoded_pairs("a=%201", print_it);
	//TODO: test web decode
	ASSERT_TRUE(false);
}

}
