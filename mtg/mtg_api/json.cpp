#include <cstdio>
#include <cstring>
#include <iostream>
#include <map>
#include <memory>
#include <ranges>
#include <set>
#include <vector>

#include <boost/scope_exit.hpp>

#include "database.hpp"
#include "rapidjson/document.h"
#include "rapidjson/error/en.h"
#include "rapidjson/filereadstream.h"
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

}

namespace mtg_api {

void all_sets(rapidjson::Document const &document, database &db) {
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

	std::vector<card_sets_container::value_type> all_sets;

	auto const &member_data = document.FindMember("data")->value;
	for (auto it = member_data.MemberBegin(); it != member_data.MemberEnd(); ++it) {
		std::vector<cards_by_collector_number_container::value_type> cards_by_collector_number_temp;
		auto const &set = it->value;
		set_code_type const set_code = as_string(member(set, "code"));

		auto const extract_set = [&](auto const &json_card) {
			try {
				auto const &identifiers = member(json_card, "identifiers");
				std::string const id_s = std::string(as_string(member(identifiers, "multiverseId")));
				auto const multiverse_id = std::stoi(id_s);

				auto const collector_number = std::stoi(std::string(as_string(member(json_card, "number"))));
				auto const name = as_string(member(json_card, "name"));

				{
					auto it = card_name_to_multiverse_id_temp.find(name);
					if (it == card_name_to_multiverse_id_temp.end()) {
						it = card_name_to_multiverse_id_temp.insert(it, {name, {}});
					}
					it->second.insert(multiverse_id);
				}

				{
					std::cout << " >>> " << multiverse_id << " " << set_code << " " << collector_number << std::endl;
					auto it = multiverse_id_to_set_printing_temp.find(multiverse_id);
					if (it == multiverse_id_to_set_printing_temp.end()) {
						it = multiverse_id_to_set_printing_temp.insert(it, {multiverse_id, set_printing{collector_number, set_code}});
					} else {
						// This is unexpected!
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
		std::vector<multiverse_id_to_card_name_index_container::value_type> inverted_index_temp;
		for (std::size_t i = 0; i < db.card_name_to_multiverse_id.size(); ++i) {
			auto const it = db.card_name_to_multiverse_id.nth(i);
			for (auto const &multiverse_id : it->second) {
				inverted_index_temp.push_back(multiverse_id_to_card_name_index_container::value_type{multiverse_id, i});
			}
		}
		db.multiverse_id_to_card_name_index = multiverse_id_to_card_name_index_container{inverted_index_temp.begin(), inverted_index_temp.end()};
	}
}

database read(mtg_api_args const &args) {
	database ret;

	{
		auto document = read_JSON_file(args.path_cards);
		expect_2(document, "All cards file missing.");
		//ret.unique_cards = all_cards(*document);
	}

	{
		auto document = read_JSON_file(args.path_sets);
		expect_2(document, "All set document missing.");
		all_sets(*document, ret);
	}

	// {
	// 	auto document = read_JSON_file(args.path_tags);
	// 	expect(document);
	// 	ret.tags = tags(*document);
	// }

	// {
		// auto document = read_JSON_file(args.path_name_to_tags);
	// 	expect(document);
	// 	name_to_tags(*document, ret.unique_cards, ret.tags);
	// }

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

}
