#pragma once

#include <optional>
#include <string>

#include <boost/container/flat_map.hpp>
#include <boost/container/flat_set.hpp>

namespace mtg_api {

using collector_number_type = std::string;
using multiverse_id_type = int;
using set_code_type = std::string;

using cards_by_collector_number_container = boost::container::flat_map<collector_number_type, multiverse_id_type>;

struct card_set {
	std::string name;
	std::string release_date;
	cards_by_collector_number_container cards_by_collector_number;
};

using card_sets_container = boost::container::flat_map<set_code_type, card_set>;

using multiverse_ids_container = boost::container::flat_set<multiverse_id_type>;
using card_name_to_multiverse_id_container = boost::container::flat_map<std::string, multiverse_ids_container>;

struct printing_prices {
	std::optional<float> tcgnormal;
	std::optional<float> tcgfoil;
	std::optional<float> mkmnormal;
	std::optional<float> mkmfoil;
};

struct set_printing {
	collector_number_type collector_number;
	set_code_type set_code;

	auto operator<=>(set_printing const &) const = default;
};

using set_printing_container = boost::container::flat_set<set_printing>;
using card_name_to_set_printing_container = boost::container::flat_map<std::string, set_printing_container>;
using multiverse_id_to_set_printing_container = boost::container::flat_map<multiverse_id_type, set_printing>;
using multiverse_id_to_card_name_index_container = boost::container::flat_map<multiverse_id_type, std::size_t>;

using set_printing_to_prices_container = boost::container::flat_map<set_printing, printing_prices>;

struct database {
	card_sets_container card_sets;
	multiverse_id_to_set_printing_container multiverse_id_to_set_printing;
	multiverse_id_to_card_name_index_container multiverse_id_to_card_name_index;
	card_name_to_multiverse_id_container card_name_to_multiverse_id;
	card_name_to_set_printing_container card_name_to_set_printing;
	set_printing_to_prices_container set_printing_to_prices;
};

}