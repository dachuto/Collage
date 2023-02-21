#pragma once

#include <string>

#include <boost/container/flat_map.hpp>
#include <boost/container/flat_set.hpp>

namespace mtg_api {

using tag_id = int;
using tag_ids_container = boost::container::flat_set<tag_id>;

using multiverse_id = int;
using multiverse_ids_container = boost::container::flat_set<multiverse_id>;

struct card_set {
	std::string name;
	multiverse_ids_container printings{};
};

struct unique_card {
	multiverse_ids_container printings{};
	tag_ids_container tags{};
};

using card_sets_container = boost::container::flat_map<std::string, card_set>;
using unique_cards_container = boost::container::flat_map<std::string, unique_card>;

struct printing {
	unique_cards_container::const_iterator card_iterator;
};

using printings_container = boost::container::flat_map<multiverse_id, printing>;

struct tag {
	std::string name;
	using card_iterators_container = boost::container::flat_set<unique_cards_container::const_iterator>;
	card_iterators_container card_iterators{};
};

using tags_container = boost::container::flat_map<tag_id, tag>;

struct database {
	card_sets_container card_sets;
	printings_container printings;
	tags_container tags;
	unique_cards_container unique_cards;
};

}