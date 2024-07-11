#include <cstdio>
#include <cstring>
#include <iostream>
#include <map>
#include <memory>
#include <ranges>
#include <set>
#include <string>
#include <string_view>
#include <vector>

#include <boost/scope_exit.hpp>

#include "database.hpp"
#include "rapidjson/document.h"
#include "rapidjson/error/en.h"
#include "rapidjson/filereadstream.h"
#include "rapidjson/pointer.h"
#include "rapidjson/stringbuffer.h"
#include "rapidjson/writer.h"

#include "json.hpp"

#define STRINGIFY(s) #s
#define STRINGIFY_MACRO(s) STRINGIFY(s)

#define expect_2(v, const_char) \
do { \
	if (not (v)) { \
		throw std::runtime_error(std::string(STRINGIFY(v) " " __FILE__ ":" STRINGIFY_MACRO(__LINE__) " ") + const_char); \
	} \
} while (0)

#define expect(v) expect_2(v, "")

namespace {

std::unique_ptr<rapidjson::Document> read_JSON_file(char const *path) {
	std::FILE * const fp = fopen(path, "rb");
	if (fp == nullptr) {
		expect_2(fp, path);
		return {};
	}

	BOOST_SCOPE_EXIT(&fp) {
		std::fclose(fp);
	} BOOST_SCOPE_EXIT_END

	std::vector<char> read_buffer;
	read_buffer.resize(256 * 1024);

	rapidjson::FileReadStream input_stream(fp, read_buffer.data(), read_buffer.size());

	auto document = std::make_unique<rapidjson::Document>();

	document->ParseStream(input_stream);

	if (document->HasParseError()) {
		auto const error = document->GetParseError();
		std::cout << rapidjson::GetParseError_En(error) << "\n";
		return {};
	}
	return document;
}

rapidjson::Value const *member_optional(rapidjson::Value const &d, char const *c) {
	auto const it = d.FindMember(c);
	if (it == d.MemberEnd()) {
		return nullptr;
	}
	return &it->value;
}

template <typename GenericValue>
auto const &member(GenericValue const &d, char const *c) {
	auto const it = d.FindMember(c);
	expect_2(it != d.MemberEnd(), c);
	return it->value;
}

// template <typename GenericValue>
// auto as_bool(GenericValue const &d) {
// 	expect(d.IsBool());
// 	return d.GetBool();
// }

template <typename GenericValue>
auto as_int(GenericValue const &d) {
	expect(d.IsInt());
	return d.GetInt();
}

template <typename GenericValue>
auto as_string(GenericValue const &d) {
	expect(d.IsString());
	return d.GetString();
}

template <typename GenericValue>
void show_members(GenericValue const &d) {
	for (auto it = d.MemberBegin(); it != d.MemberEnd(); ++it) {
		std::cout << as_string(it->name) << "\n";
	}
}

struct rapid_json_allocator {
	allocator_t const *allocator;

	void *Malloc(size_t size) {
		return allocate(allocator, size);
	}

	void *Realloc(void *original_ptr, size_t original_size, size_t new_size) {
		void *temp = Malloc(new_size);
		std::memcpy(temp, original_ptr, original_size);
		return temp;
	}

	static void Free(void *ptr) {
		// we assume that it is short living pool allocator
	}
};

bytes_view serialize(allocator_t allocator, rapidjson::Document const &document) {
	rapid_json_allocator rja{&allocator};
	using buffer_type = rapidjson::GenericStringBuffer<rapidjson::UTF8<char>, rapid_json_allocator>;
	buffer_type buffer(&rja);
	rapidjson::Writer<decltype(buffer)> writer(buffer);
	document.Accept(writer);
	return {const_cast<buffer_type::Ch*>(buffer.GetString()), buffer.GetSize()}; // cast const away - it's memory from allocator
}

template <typename DocOrValue, typename It, typename Allocator>
auto as_json_array(DocOrValue &d, It first, It last, Allocator &allocator) {
	d.SetArray();
	for (auto it = first; it != last; ++it) {
		rapidjson::Value v;
		v.SetInt(*it);
		d.PushBack(v, allocator);
	}
}

template <typename Allocator>
rapidjson::Value to_value(mtg_api::set_printing const &x, Allocator &allocator) {
	rapidjson::Value ret;
	ret.SetObject();

	rapidjson::Value sc;
	sc.SetString(x.set_code.c_str(), x.set_code.length(), allocator);
	ret.AddMember("set", sc, allocator);

	rapidjson::Value sn;
	sc.SetString(x.collector_number.c_str(), x.collector_number.length(), allocator);
	ret.AddMember("collector_number", sc, allocator);

	return ret;
}

template <typename GenericValue>
bool card_available_in_paper(GenericValue const &json_card) {
	auto const &availability = member(json_card, "availability");
	expect(availability.IsArray());
	std::string_view const paper("paper");
	for (auto it = availability.Begin(); it != availability.End(); ++it) {
		auto const &p = *it;
		expect(p.IsString());
		if (paper == std::string_view(p.GetString())) {
			return true;
		}
	}
	return false;
}

// Returns map from card uuid to paper prices
std::map<std::string, mtg_api::printing_prices> extract_paper_prices(rapidjson::Document const &document) {
	expect(document.IsObject());
	auto const &cards = member(document, "data");
	expect(cards.IsObject());

	std::map<std::string, mtg_api::printing_prices> ret;
	for (rapidjson::Value::ConstMemberIterator it = cards.MemberBegin(); it != cards.MemberEnd(); ++it) {
		auto const *paper = member_optional(it->value, "paper");
		if (paper == nullptr) {
			continue;
		}

		mtg_api::printing_prices prices;
		{
			rapidjson::Value const *tcgnormal = rapidjson::Pointer("/tcgplayer/retail/normal").Get(*paper);
			if (tcgnormal != nullptr) {
				prices.tcgnormal = tcgnormal->MemberBegin()->value.GetFloat();
			}
			rapidjson::Value const *tcgfoil = rapidjson::Pointer("/tcgplayer/retail/foil").Get(*paper);
			if (tcgfoil != nullptr) {
				prices.tcgfoil = tcgfoil->MemberBegin()->value.GetFloat();
			}
		}

		{
			rapidjson::Value const *mkmnormal = rapidjson::Pointer("/cardmarket/retail/normal").Get(*paper);
			if (mkmnormal != nullptr) {
				prices.mkmnormal = mkmnormal->MemberBegin()->value.GetFloat();
			}
			rapidjson::Value const *mkmfoil = rapidjson::Pointer("/cardmarket/retail/foil").Get(*paper);
			if (mkmfoil != nullptr) {
				prices.mkmfoil = mkmfoil->MemberBegin()->value.GetFloat();
			}
		}

		ret.insert({std::string(it->name.GetString()), prices});
	}
	return ret;
}

}

namespace mtg_api {

void all_sets(rapidjson::Document const &document, rapidjson::Document const &prices, database &db) {
	auto const one_set = [](auto const &json_set, auto &&card_functor) {
		expect(json_set.IsObject());
		auto const &cards = member(json_set, "cards");
		for (auto it = cards.Begin(); it != cards.End(); ++it) {
			auto const &p = *it;
			expect(p.IsObject());
			card_functor(p);
		}
	};

	expect(document.IsObject());

	std::map<std::string, std::set<multiverse_id_type>> card_name_to_multiverse_id_temp;
	std::map<multiverse_id_type, set_printing> multiverse_id_to_set_printing_temp;
	std::map<std::string, std::set<set_printing>> card_name_to_set_printing_temp;

	std::map<set_printing, printing_prices> set_printing_to_price_temp;


	std::vector<card_sets_container::value_type> all_sets;

	auto const prices_map = extract_paper_prices(prices);

	auto const &member_data = document.FindMember("data")->value;
	for (auto it = member_data.MemberBegin(); it != member_data.MemberEnd(); ++it) {
		std::vector<cards_by_collector_number_container::value_type> cards_by_collector_number_temp;
		auto const &set = it->value;
		set_code_type const set_code = as_string(member(set, "code"));

		auto const extract_set = [&](auto const &json_card) {
			try {
				if (not card_available_in_paper(json_card)) {
					return;
				}

				auto const &identifiers = member(json_card, "identifiers");

				auto const name = as_string(member(json_card, "name"));
				auto const collector_number = std::string(as_string(member(json_card, "number")));
				set_printing const printing_identifier{collector_number, set_code};

				{
					auto it = card_name_to_set_printing_temp.find(name);
					if (it == card_name_to_set_printing_temp.end()) {
						it = card_name_to_set_printing_temp.insert(it, {name, {}});
					}

					it->second.insert(printing_identifier);
				}

				std::string const id_s = std::string(as_string(member(identifiers, "multiverseId")));
				auto const multiverse_id = std::stoi(id_s);

				{
					auto it = card_name_to_multiverse_id_temp.find(name);
					if (it == card_name_to_multiverse_id_temp.end()) {
						it = card_name_to_multiverse_id_temp.insert(it, {name, {}});
					}
					it->second.insert(multiverse_id);
				}

				{
					//std::cout << " >>> " << multiverse_id << " " << set_code << " " << collector_number << std::endl;
					auto it = multiverse_id_to_set_printing_temp.find(multiverse_id);
					if (it == multiverse_id_to_set_printing_temp.end()) {
						it = multiverse_id_to_set_printing_temp.insert(it, {multiverse_id, printing_identifier});
					} else {
						// This is unexpected!
					}
				}

				{
					auto const *uuid = member_optional(json_card, "uuid");
					if (uuid != nullptr) {
						auto const it = prices_map.find(uuid->GetString());
						if (it != prices_map.end()) {
							set_printing_to_price_temp.insert({printing_identifier, it->second});
						}
					}
				}

				cards_by_collector_number_temp.push_back({collector_number, multiverse_id});
			} catch (std::exception const &e) {
				// this is because data source lists cards, from weird supplementary sets, without important fields (like multiverse id)
				// std::cerr << e.what();
			}
		};

		one_set(it->value, extract_set);
		all_sets.push_back(card_sets_container::value_type{set_code, {as_string(member(set, "name")), as_string(member(set, "releaseDate")), cards_by_collector_number_container{std::cbegin(cards_by_collector_number_temp), std::cend(cards_by_collector_number_temp)}}});
	}

	db.card_sets = card_sets_container{std::cbegin(all_sets), std::cend(all_sets)};

	{
		auto const temp_range = std::ranges::views::transform(multiverse_id_to_set_printing_temp, [](auto const &e) {
			return multiverse_id_to_set_printing_container::value_type{e.first, e.second};
		});
		db.multiverse_id_to_set_printing = multiverse_id_to_set_printing_container{boost::container::ordered_unique_range_t{}, temp_range.begin(), temp_range.end()};
	}

	{
		auto const temp_range = std::ranges::views::transform(card_name_to_multiverse_id_temp, [](auto const &e) {
			return card_name_to_multiverse_id_container::value_type{e.first, multiverse_ids_container{e.second.begin(), e.second.end()}};
		});
		db.card_name_to_multiverse_id = card_name_to_multiverse_id_container{temp_range.begin(), temp_range.end()};
	}

	{
		auto const temp_range = std::ranges::views::transform(card_name_to_set_printing_temp, [](auto const &e) {
			return card_name_to_set_printing_container::value_type{e.first, set_printing_container{e.second.begin(), e.second.end()}};
		});
		db.card_name_to_set_printing = card_name_to_set_printing_container{temp_range.begin(), temp_range.end()};
	}

	{
		std::vector<multiverse_id_to_card_name_index_container::value_type> inverted_index_temp;
		for (std::size_t i = 0; i < db.card_name_to_multiverse_id.size(); ++i) {
			auto const it = db.card_name_to_multiverse_id.nth(i);
			for (auto const &multiverse_id : it->second) {
				inverted_index_temp.push_back(multiverse_id_to_card_name_index_container::value_type{multiverse_id, i});
			}
		}
		db.multiverse_id_to_card_name_index = multiverse_id_to_card_name_index_container{inverted_index_temp.begin(), inverted_index_temp.end()};
	}

	db.set_printing_to_prices = set_printing_to_prices_container{set_printing_to_price_temp.begin(), set_printing_to_price_temp.end()};
}

database read(mtg_api_args const &args) {
	database ret;

	{
		auto document = read_JSON_file(args.path_cards);
		expect_2(document, "All cards file missing."); //unused
	}

	{
		auto const document = read_JSON_file(args.path_sets);
		expect_2(document, "All set document missing.");
		auto const prices = read_JSON_file(args.path_prices);
		expect_2(prices, "Prices document is missing.");
		all_sets(*document, *prices, ret);
	}

	return ret;
}

bytes_view to_json::write(std::string const &s) const {
	rapidjson::Document d;
	d.SetString(s.data(), s.length(), d.GetAllocator());
	return serialize(allocator, d);
}

bytes_view to_json::write(database const &database) const {
	rapidjson::Document d;
	d.SetArray();

	// for (auto const &[name, set] : database.card_sets) {
	// 	rapidjson::Value v;
	// 	d.AddMember(rapidjson::StringRef(s.first.data(), s.first.length()), v, d.GetAllocator());
	// }
	// 		v.SetString(key.c_str(), key.length());
	// 	d.PushBack(v, d.GetAllocator());

	return serialize(allocator, d);
}

bytes_view to_json::write(multiverse_ids_container const &x) const {
	rapidjson::Document d;
	as_json_array(d, std::cbegin(x), std::cend(x), d.GetAllocator());
	return serialize(allocator, d);
}

bytes_view to_json::write(int const *first, int const *last) const {
	rapidjson::Document d;
	as_json_array(d, first, last, d.GetAllocator());
	return serialize(allocator, d);
}

bytes_view to_json::write(card_name_to_multiverse_id_container const &c) const {
	rapidjson::Document d;
	d.SetObject();

	for (auto const &[key, value] : c) {
			rapidjson::Value ids;
			as_json_array(ids, std::cbegin(value), std::cend(value), d.GetAllocator());

			rapidjson::Value kv;
			kv.SetString(key.c_str(), key.length());
			d.AddMember(kv, ids, d.GetAllocator());
	}

	return serialize(allocator, d);
}

bytes_view to_json::write(card_name_to_set_printing_container const &c) const {
	rapidjson::Document d;
	d.SetObject();

	for (auto const &[key, value] : c) {
			rapidjson::Value printings;
			printings.SetArray();

			for (auto const &p : value) {
				printings.PushBack(to_value(p, d.GetAllocator()), d.GetAllocator());
			}

			rapidjson::Value kv;
			kv.SetString(key.c_str(), key.length(), d.GetAllocator());
			d.AddMember(kv, printings, d.GetAllocator());
	}

	return serialize(allocator, d);
}

bytes_view to_json::write(set_printing_to_prices_container const &c) const {
	rapidjson::Document d;
	d.SetObject();

	auto const add_if_value_exists = [&allocator = d.GetAllocator()](auto &obj, char const *name, std::optional<float> const &ov) {
		if (ov.has_value()) {
			rapidjson::Value v;
			v.SetFloat(ov.value());

			rapidjson::Value kv;
			kv.SetString(name, allocator);
			obj.AddMember(kv, v, allocator);
		}
	};

	for (auto const &[key, value] : c) {
			rapidjson::Value prices;
			prices.SetObject();

			add_if_value_exists(prices, "mkmfoil", value.mkmfoil);
			add_if_value_exists(prices, "mkmnormal", value.mkmnormal);
			add_if_value_exists(prices, "tcgfoil", value.tcgfoil);
			add_if_value_exists(prices, "tcgnormal", value.tcgnormal);

			std::string encoded = key.set_code + "/" + key.collector_number;
			rapidjson::Value kv;
			kv.SetString(encoded.c_str(), encoded.length(), d.GetAllocator());
			d.AddMember(kv, prices, d.GetAllocator());
	}

	return serialize(allocator, d);
}

bytes_view to_json::write(multiverse_id_to_set_printing_container const &c) const {
	rapidjson::Document d;
	d.SetObject();

	for (auto const &[key, value] : c) {
			std::string multiverse_id_as_key{std::to_string(key)};

			rapidjson::Value kv;
			kv.SetString(multiverse_id_as_key.c_str(), multiverse_id_as_key.length(), d.GetAllocator());
			d.AddMember(kv, to_value(value, d.GetAllocator()), d.GetAllocator());
	}

	return serialize(allocator, d);

}

}
