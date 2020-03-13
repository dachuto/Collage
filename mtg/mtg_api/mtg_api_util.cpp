#include <iostream>

#include "json.hpp"

int main() {
	auto database = mtg_api::read({"./AllCards.json", "./name_to_tags.json", "./AllPrintings.json", "./tags.json"});

	for (auto const &kv: database.unique_cards) {
		std::cout << kv.first << "\n";
	}

	return 0;
}
