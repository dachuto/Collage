#include "gtest/gtest.h"

#include "database.hpp"
#include "json.hpp"

#include "web.hpp"

namespace mtg_api {

void *allocate_with_new(void *data, size_t size) {
	return new char[size];
}

TEST(mtg_api_test, works) {
	allocator_t a{allocate_with_new, nullptr};

	auto database = read({"./AtomicCards.json", "./name_to_tags.json", "./AllPrintings.json", "./tags.json"});
	auto ret = to_json{a}.write(database);
	std::string s(ret.data, ret.size);
	std::cout << s << "\n";

	for (auto const &kv: database.unique_cards) {
		std::cout << kv.first;
		std::cout << " [ ";
		for (auto const &x : kv.second.printings) {
			std::cout << " " << x;
		}
		std::cout << "]\n";
	}

	for (auto const &kv: database.card_sets) {
		std::cout << kv.first << "\n";
		for (auto const &id : kv.second.printings) {
			std::cout << id << " ";
		}
		std::cout << "\n";
	}

	auto const it = database.unique_cards.find(std::string("Fog"));
	if (it != database.unique_cards.end()) {
		for (auto const &id : it->second.printings) {
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
