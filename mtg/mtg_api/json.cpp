#include <cstdio>
#include <cstring>
#include <map>
#include <memory>
#include <unordered_map>
#include <vector>
#include <iostream>

#include <boost/scope_exit.hpp>

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

template <typename It>
auto as_json_array(It first, It last) {
	rapidjson::Document d;
	d.SetArray();
	for (auto it = first; it != last; ++it) {
		rapidjson::Value v;
		v.SetInt(*it);
		d.PushBack(v, d.GetAllocator());
	}
	return d;
}

}

namespace mtg_api {

auto all_cards(rapidjson::Document const &document) {
	auto const one_card = [](auto const &d) {
		expect(d.IsString());
		return unique_cards_container::value_type{as_string(d), {}};
	};

	std::vector<unique_cards_container::value_type> temp;
	expect(document.IsObject());
	auto const &data = member(document, "data");
	expect(data.IsObject());

	for (auto it = data.MemberBegin(); it != data.MemberEnd(); ++it) {
		temp.push_back(one_card(it->name));
		//it->value
	}

	return unique_cards_container{std::cbegin(temp), std::cend(temp)};
}

void all_sets(rapidjson::Document const &document, database &db) {
	auto const one_set = [&unique_cards = db.unique_cards](auto const &json_set, auto &&card_functor) {
		expect(json_set.IsObject());
		auto const &cards = member(json_set, "cards");
		for (auto it = cards.Begin(); it != cards.End(); ++it) {
			auto const &p = *it;
			expect(p.IsObject());
// <<<<<<< HEAD
// 			try {
// 				auto const &identifiers = member(p, "identifiers");
// 				expect(identifiers.IsObject());
// 				auto const &id_object = member(identifiers, "multiverseId");
// 				auto const id = std::stoi(as_string(id_object));
// 				auto const unique_cards_it = unique_cards.find(as_string(member(p, "name")));
// =======
			card_functor(p);
		}

	};

	expect(document.IsObject());
	auto const &member_data = document.FindMember("data")->value;

	std::unordered_map<std::string, unique_card> card_names;
	auto const extract_name = [&card_names](auto const &json_card) {
		card_names.insert({as_string(member(json_card, "name")), {}});
	};

	for (auto it = member_data.MemberBegin(); it != member_data.MemberEnd(); ++it) {
		one_set(it->value, extract_name);
	}
	db.unique_cards = unique_cards_container{std::cbegin(card_names), std::cend(card_names)};

	std::vector<card_sets_container::value_type> all_sets;
	std::vector<printings_container::value_type> printings_not_sorted;

	for (auto it = member_data.MemberBegin(); it != member_data.MemberEnd(); ++it) {
		multiverse_ids_container multiverse_ids;
		auto const extract_set = [&unique_cards = db.unique_cards, &multiverse_ids, &printings_not_sorted](auto const &json_card) {
			try {
				auto const &identifiers = member(json_card, "identifiers");
				std::string const id_s = std::string(as_string(member(identifiers, "multiverseId")));
				auto const id = std::stoi(id_s);
				auto const name = as_string(member(json_card, "name"));
				auto unique_cards_it = unique_cards.find(name);
				assert(unique_cards_it != unique_cards.end());
// >>>>>>> 07a136e (json changes cpp)
				unique_cards_it->second.printings.insert(id);

				printings_not_sorted.push_back({id, {unique_cards_it}});
				multiverse_ids.insert(id);
			} catch (...) {
				// this is because data source lists cards, from wierd supplementary sets, without important fields (like multiverse id)
				//std::cerr << e.what();
			}
		};

// <<<<<<< HEAD
// 		return card_sets_container::value_type{as_string(member(d, "code")), {as_string(member(d, "name")), temp}};
// 	};

// 	std::vector<card_sets_container::value_type> temp;
// 	expect(document.IsObject());
// 	auto const &data = member(document, "data");
// 	expect(data.IsObject());

// 	for (auto it = data.MemberBegin(); it != data.MemberEnd(); ++it) {
// 		temp.push_back(one_set(it->value));
// =======
		auto const &set = it->value;
		one_set(it->value, extract_set);
		all_sets.push_back(card_sets_container::value_type{as_string(member(set, "code")), {as_string(member(set, "name")), multiverse_ids}});
	}
	db.card_sets = card_sets_container{std::cbegin(all_sets), std::cend(all_sets)};
	db.printings = printings_container{std::cbegin(printings_not_sorted), std::cend(printings_not_sorted)};
}

auto tags(rapidjson::Document const &document) {
	expect(document.IsObject());
	std::vector<tags_container::value_type> temp;
	for (auto it = document.MemberBegin(); it != document.MemberEnd(); ++it) {
		temp.push_back({std::stoi(as_string(it->name)), {as_string(it->value)}});
	}
	return tags_container{std::cbegin(temp), std::cend(temp)};
}

void name_to_tags(rapidjson::Document const &document, unique_cards_container &unique_cards, tags_container &tags) {
	expect(document.IsObject());

	std::map<tag_id, std::vector<unique_cards_container::const_iterator>> temp;
	for (auto it = document.MemberBegin(); it != document.MemberEnd(); ++it) {
		auto const unique_cards_it = unique_cards.find(as_string(it->name));
		expect(unique_cards_it != unique_cards.end());
		auto const &array = it->value;
		expect(array.IsArray());
		for (auto it2 = array.Begin(); it2 != array.End(); ++it2) {
			tag_id const tag_id = as_int(*it2);
			unique_cards_it->second.tags.insert(tag_id);
			temp[tag_id].push_back(unique_cards_it);
		}
	}

	for (auto const &kv : temp) {
			auto const tags_it = tags.find(kv.first);
			expect(tags_it != tags.end());
			tags_it->second.card_iterators = tag::card_iterators_container{std::cbegin(kv.second), std::cend(kv.second)};
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
	// 	auto document = read_JSON_file(args.path_name_to_tags);
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
	d.SetObject();
	//TODO: this is just a test
	// for (auto const &s : database.unique_cards) {
	// 	rapidjson::Value v{1}; //TODO
	// 	d.AddMember(rapidjson::StringRef(s.first.data(), s.first.length()), v, d.GetAllocator());
	// }

	// d.SetArray();
	for (auto const &t : database.tags) {
		// rapidjson::Value dd;
		// dd.SetObject();

		{
			std::string const i = std::to_string(t.first);
			rapidjson::Value n;
			n.SetString(i.data(), i.length(), d.GetAllocator());
			rapidjson::Value v;
			v.SetString(t.second.name.data(), t.second.name.length());
			d.AddMember(n, v, d.GetAllocator());
		}
		// {
		// 	rapidjson::Value v;
		// 	v.SetInt(t.first);
		// 	dd.AddMember("id", v, d.GetAllocator());
		// }
		// d.PushBack(dd, d.GetAllocator());
	}

	return serialize(allocator, d);
}

bytes_view to_json::write(multiverse_ids_container const &x) const {
	return serialize(allocator, as_json_array(std::cbegin(x), std::cend(x)));
}

bytes_view to_json::write(int const *first, int const *last) const {
	return serialize(allocator, as_json_array(first, last));
}

}
