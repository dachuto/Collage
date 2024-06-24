#include <iostream>

#include "json.hpp"

int main() {
	auto database = mtg_api::read({"./AllCards.json", "./name_to_tags.json", "./AllPrintings.json", "./tags.json"});

	for (auto const &kv: database.card_name_to_multiverse_id) {
		std::cout << kv.first << "\n";
	}

	return 0;
}
